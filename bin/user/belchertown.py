# Extension for the Belchertown skin. 
# This extension builds search list extensions as well
# as a crude "cron" to download necessary files. 
#
# Pat O'Brien, August 19, 2018

from __future__ import with_statement
import datetime
import time
import calendar
import json
import os
import os.path
import syslog
import sys
import locale

import weewx
import weecfg
import configobj
import weedb
import weeutil.weeutil
import weewx.reportengine
import weewx.station
import weewx.units
import weewx.tags
import weeplot.genplot
import weeplot.utilities

from collections import OrderedDict

from weewx.cheetahgenerator import SearchList
from weewx.tags import TimespanBinder
from weeutil.weeutil import to_bool, TimeSpan, to_int, archiveDaySpan, archiveWeekSpan, archiveMonthSpan, archiveYearSpan, startOfDay, timestamp_to_string
from weeutil.config import search_up

# This helps with locale. https://stackoverflow.com/a/40346898/1177153
reload(sys)
sys.setdefaultencoding("utf-8")
locale.setlocale(locale.LC_ALL, "")

def logmsg(level, msg):
    syslog.syslog(level, 'Belchertown Extension: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)
    
# Print version in syslog for easier troubleshooting
VERSION = "1.0rc3"
loginf("version %s" % VERSION)

class getData(SearchList):
    def __init__(self, generator):
        SearchList.__init__(self, generator)

    def get_extension_list(self, timespan, db_lookup):
        """
        Build the data needed for the Belchertown skin
        """
        
        # Look for the debug flag which can be used to show more logging
        weewx.debug = int(self.generator.config_dict.get('debug', 0))
        
        # Check if the pre-requisites have been completed. Either station_url or belchertown_root_url need to be set. 
        if self.generator.skin_dict['Extras']['belchertown_root_url'] != "":
            belchertown_root_url = self.generator.skin_dict['Extras']['belchertown_root_url']
        elif self.generator.config_dict["Station"].has_key("station_url"):
            belchertown_root_url = self.generator.config_dict["Station"]["station_url"]
        else:
            belchertown_root_url = ""
            
        belchertown_debug = self.generator.skin_dict['Extras'].get('belchertown_debug', 0)

        # Find the right HTML ROOT
        if 'HTML_ROOT' in self.generator.skin_dict:
            local_root = os.path.join(self.generator.config_dict['WEEWX_ROOT'],
                                      self.generator.skin_dict['HTML_ROOT'])
        else:
            local_root = os.path.join(self.generator.config_dict['WEEWX_ROOT'],
                                      self.generator.config_dict['StdReport']['HTML_ROOT'])
        
        # Find the SKIN ROOT
        local_skin_root = os.path.join( self.generator.config_dict['WEEWX_ROOT'], self.generator.skin_dict['SKIN_ROOT'], self.generator.skin_dict['skin'] )
        
        # Setup UTC offset hours for moment.js in index.html
        moment_js_stop_struct = time.localtime( time.time() )
        moment_js_utc_offset = (calendar.timegm(moment_js_stop_struct) - calendar.timegm(time.gmtime(time.mktime(moment_js_stop_struct))))/60
        
        # Highcharts UTC offset is the opposite of normal. Positive values are west, negative values are east of UTC. https://api.highcharts.com/highcharts/time.timezoneOffset
        # Multiplying by -1 will reverse the number sign and keep 0 (not -0). https://stackoverflow.com/a/14053631/1177153
        highcharts_timezoneoffset = moment_js_utc_offset * -1
        
        # Get the system locale for use with moment.js, and the system decimal for use with highcharts
        system_locale, locale_encoding = locale.getdefaultlocale()
        system_locale_js = system_locale.replace("_", "-") # Python's locale is underscore. JS uses dashes.
        highcharts_decimal = locale.localeconv()["decimal_point"]
        
        # Get the archive interval for the highcharts gapsize
        archive_interval_ms = int(self.generator.config_dict["StdArchive"]["archive_interval"]) * 1000
        
        # Build the chart array for the HTML
        # Outputs a dict of nested lists which allow you to have different charts for different timespans on the site.
        # OrderedDict([('day', ['chart1', 'chart2', 'chart3', 'chart4']), 
        # ('week', ['chart1', 'chart2', 'chart3', 'chart4', 'chart5', 'chart6']),
        # ('month', ['chart1', 'chart2', 'chart3', 'chart4', 'chart5', 'chart6', 'chart7']), 
        # ('year', ['chart1', 'chart2', 'chart3', 'chart4', 'chart5'])])
        chart_dict = self.generator.skin_dict['Charts']
        charts = OrderedDict()
        for chart_timespan in chart_dict.sections:
            timespan_chart_list = []
            for plotname in chart_dict[chart_timespan].sections:
                if plotname not in timespan_chart_list:
                    timespan_chart_list.append( plotname )
            charts[chart_timespan] = timespan_chart_list
        
        # Set a default radar URL using station's lat/lon. Moved from skin.conf so we can get station lat/lon from weewx.conf. A lot of stations out there with Belchertown 0.1 through 0.7 are showing the visitor's location and not the proper station location because nobody edited the radar_html which did not have lat/lon set previously.
        if self.generator.skin_dict['Extras']['radar_html'] == "":
            lat = self.generator.config_dict['Station']['latitude']
            lon = self.generator.config_dict['Station']['longitude']
            radar_html = '<iframe width="650" height="360" src="https://embed.windy.com/embed2.html?lat={}&lon={}&zoom=8&level=surface&overlay=radar&menu=&message=true&marker=&calendar=&pressure=&type=map&location=coordinates&detail=&detailLat={}&detailLon={}&metricWind=&metricTemp=&radarRange=-1" frameborder="0"></iframe>'.format( lat, lon, lat, lon )
        else:
            radar_html = self.generator.skin_dict['Extras']['radar_html']
        
        """
        Build the all time stats.
        """
        wx_manager = db_lookup()
        
        # Find the beginning of the current year
        now = datetime.datetime.now()
        date_time = '01/01/%s 00:00:00' % now.year
        pattern = '%m/%d/%Y %H:%M:%S'
        year_start_epoch = int(time.mktime(time.strptime(date_time, pattern)))
        #_start_ts = startOfInterval(year_start_epoch ,86400) # This is the current calendar year
        
        # Setup the converter
        # Get the target unit nickname (something like 'US' or 'METRIC'):
        target_unit_nickname = self.generator.config_dict['StdConvert']['target_unit']
        # Get the target unit: weewx.US, weewx.METRIC, weewx.METRICWX
        target_unit = weewx.units.unit_constants[target_unit_nickname.upper()]
        # Bind to the appropriate standard converter units
        converter = weewx.units.StdUnitConverters[target_unit]
        
        # Temperature Range Lookups
        
        # 1. The database query finds the result based off the total column.
        # 2. We need to convert the min, max to the site's requested unit.
        # 3. We need to re-calculate the min/max range because the unit may have changed. 

        year_outTemp_max_range_query = wx_manager.getSql( 'SELECT dateTime, ROUND( (max - min), 1 ) as total, ROUND( min, 1 ) as min, ROUND( max, 1 ) as max FROM archive_day_outTemp WHERE dateTime >= %s AND min IS NOT NULL AND max IS NOT NULL ORDER BY total DESC LIMIT 1;' % year_start_epoch )
        year_outTemp_min_range_query = wx_manager.getSql( 'SELECT dateTime, ROUND( (max - min), 1 ) as total, ROUND( min, 1 ) as min, ROUND( max, 1 ) as max FROM archive_day_outTemp WHERE dateTime >= %s AND min IS NOT NULL AND max IS NOT NULL ORDER BY total ASC LIMIT 1;' % year_start_epoch )
        at_outTemp_max_range_query = wx_manager.getSql( 'SELECT dateTime, ROUND( (max - min), 1 ) as total, ROUND( min, 1 ) as min, ROUND( max, 1 ) as max FROM archive_day_outTemp WHERE min IS NOT NULL AND max IS NOT NULL ORDER BY total DESC LIMIT 1;' )
        at_outTemp_min_range_query = wx_manager.getSql( 'SELECT dateTime, ROUND( (max - min), 1 ) as total, ROUND( min, 1 ) as min, ROUND( max, 1 ) as max FROM archive_day_outTemp WHERE min IS NOT NULL AND max IS NOT NULL ORDER BY total ASC LIMIT 1;' )
        
        # Find the group_name for outTemp
        outTemp_unit = converter.group_unit_dict["group_temperature"]
        
        # Find the number of decimals to round to
        outTemp_round = self.generator.skin_dict['Units']['StringFormats'].get(outTemp_unit, "%.1f")

        # Largest Daily Temperature Range Conversions
        # Max temperature for this day
        if year_outTemp_max_range_query is not None:
            year_outTemp_max_range_max_tuple = (year_outTemp_max_range_query[3], outTemp_unit, 'group_temperature')
            year_outTemp_max_range_max = outTemp_round % self.generator.converter.convert(year_outTemp_max_range_max_tuple)[0]
            # Min temperature for this day
            year_outTemp_max_range_min_tuple = (year_outTemp_max_range_query[2], outTemp_unit, 'group_temperature')
            year_outTemp_max_range_min = outTemp_round % self.generator.converter.convert(year_outTemp_max_range_min_tuple)[0]
            # Largest Daily Temperature Range total
            year_outTemp_max_range_total = outTemp_round % ( float(year_outTemp_max_range_max) - float(year_outTemp_max_range_min) )
            # Replace the SQL Query output with the converted values
            year_outTemp_range_max = [ year_outTemp_max_range_query[0], locale.format("%g", float(year_outTemp_max_range_total)), locale.format("%g", float(year_outTemp_max_range_min)), locale.format("%g", float(year_outTemp_max_range_max)) ]
        else:
            year_outTemp_range_max = [ calendar.timegm( time.gmtime() ), 0.0, 0.0, 0.0 ]
        
        # Smallest Daily Temperature Range Conversions
        # Max temperature for this day
        if year_outTemp_min_range_query is not None:
            year_outTemp_min_range_max_tuple = (year_outTemp_min_range_query[3], outTemp_unit, 'group_temperature')
            year_outTemp_min_range_max = outTemp_round % self.generator.converter.convert(year_outTemp_min_range_max_tuple)[0]
            # Min temperature for this day
            year_outTemp_min_range_min_tuple = (year_outTemp_min_range_query[2], outTemp_unit, 'group_temperature')
            year_outTemp_min_range_min = outTemp_round % self.generator.converter.convert(year_outTemp_min_range_min_tuple)[0]
            # Smallest Daily Temperature Range total
            year_outTemp_min_range_total = outTemp_round % ( float(year_outTemp_min_range_max) - float(year_outTemp_min_range_min) )
            # Replace the SQL Query output with the converted values
            year_outTemp_range_min = [ year_outTemp_min_range_query[0], locale.format("%g", float(year_outTemp_min_range_total)), locale.format("%g", float(year_outTemp_min_range_min)), locale.format("%g", float(year_outTemp_min_range_max)) ]
        else:
            year_outTemp_range_min = [ calendar.timegm( time.gmtime() ), 0.0, 0.0, 0.0 ]
        
        # All Time - Largest Daily Temperature Range Conversions
        # Max temperature
        at_outTemp_max_range_max_tuple = (at_outTemp_max_range_query[3], outTemp_unit, 'group_temperature')
        at_outTemp_max_range_max = outTemp_round % self.generator.converter.convert(at_outTemp_max_range_max_tuple)[0]
        # Min temperature for this day
        at_outTemp_max_range_min_tuple = (at_outTemp_max_range_query[2], outTemp_unit, 'group_temperature')
        at_outTemp_max_range_min = outTemp_round % self.generator.converter.convert(at_outTemp_max_range_min_tuple)[0]
        # Largest Daily Temperature Range total
        at_outTemp_max_range_total = outTemp_round % ( float(at_outTemp_max_range_max) - float(at_outTemp_max_range_min) )
        # Replace the SQL Query output with the converted values
        at_outTemp_range_max = [ at_outTemp_max_range_query[0], locale.format("%g", float(at_outTemp_max_range_total)), locale.format("%g", float(at_outTemp_max_range_min)), locale.format("%g", float(at_outTemp_max_range_max)) ]

        # All Time - Smallest Daily Temperature Range Conversions
        # Max temperature for this day
        at_outTemp_min_range_max_tuple = (at_outTemp_min_range_query[3], outTemp_unit, 'group_temperature')
        at_outTemp_min_range_max = outTemp_round % self.generator.converter.convert(at_outTemp_min_range_max_tuple)[0]
        # Min temperature for this day
        at_outTemp_min_range_min_tuple = (at_outTemp_min_range_query[2], outTemp_unit, 'group_temperature')
        at_outTemp_min_range_min = outTemp_round % self.generator.converter.convert(at_outTemp_min_range_min_tuple)[0]
        # Smallest Daily Temperature Range total
        at_outTemp_min_range_total = outTemp_round % ( float(at_outTemp_min_range_max) - float(at_outTemp_min_range_min) )
        # Replace the SQL Query output with the converted values
        at_outTemp_range_min = [ at_outTemp_min_range_query[0], locale.format("%g", float(at_outTemp_min_range_total)), locale.format("%g", float(at_outTemp_min_range_min)), locale.format("%g", float(at_outTemp_min_range_max)) ]
        
        
        # Rain lookups
        # Find the group_name for rain
        rain_unit = converter.group_unit_dict["group_rain"]
        
        # Find the number of decimals to round to
        rain_round = self.generator.skin_dict['Units']['StringFormats'].get(rain_unit, "%.2f")
        
        # Rainiest Day
        rainiest_day_query = wx_manager.getSql( 'SELECT dateTime, sum FROM archive_day_rain WHERE dateTime >= %s ORDER BY sum DESC LIMIT 1;' % year_start_epoch )
        if rainiest_day_query is not None:
            rainiest_day_tuple = (rainiest_day_query[1], rain_unit, 'group_rain')
            rainiest_day_converted = rain_round % self.generator.converter.convert(rainiest_day_tuple)[0]
            rainiest_day = [ rainiest_day_query[0], rainiest_day_converted ]
        else:
            rainiest_day = [ calendar.timegm( time.gmtime() ), 0.00 ]
            

        # All Time Rainiest Day
        at_rainiest_day_query = wx_manager.getSql( 'SELECT dateTime, sum FROM archive_day_rain ORDER BY sum DESC LIMIT 1' )
        at_rainiest_day_tuple = (at_rainiest_day_query[1], rain_unit, 'group_rain')
        at_rainiest_day_converted = rain_round % self.generator.converter.convert(at_rainiest_day_tuple)[0]
        at_rainiest_day = [ at_rainiest_day_query[0], at_rainiest_day_converted ]
        

        # Find what kind of database we're working with and specify the correctly tailored SQL Query for each type of database
        dataBinding = self.generator.config_dict['StdArchive']['data_binding']
        database = self.generator.config_dict['DataBindings'][dataBinding]['database']
        databaseType = self.generator.config_dict['Databases'][database]['database_type']
        driver = self.generator.config_dict['DatabaseTypes'][databaseType]['driver']
        if driver == "weedb.sqlite":
            year_rainiest_month_sql = 'SELECT strftime("%%m", datetime(dateTime, "unixepoch")) as month, ROUND( SUM( sum ), 2 ) as total FROM archive_day_rain WHERE strftime("%%Y", datetime(dateTime, "unixepoch")) = "%s" GROUP BY month ORDER BY total DESC LIMIT 1;' % time.strftime( "%Y", time.localtime( time.time() ) )
            at_rainiest_month_sql = 'SELECT strftime("%m", datetime(dateTime, "unixepoch")) as month, strftime("%Y", datetime(dateTime, "unixepoch")) as year, ROUND( SUM( sum ), 2 ) as total FROM archive_day_rain GROUP BY month, year ORDER BY total DESC LIMIT 1;'
            year_rain_data_sql = 'SELECT dateTime, ROUND( sum, 2 ) FROM archive_day_rain WHERE strftime("%%Y", datetime(dateTime, "unixepoch")) = "%s";' % time.strftime( "%Y", time.localtime( time.time() ) )
            # The all stats from http://www.weewx.com/docs/customizing.htm doesn't seem to calculate "Total Rainfall for" all time stat correctly. 
            at_rain_highest_year_sql = 'SELECT strftime("%Y", datetime(dateTime, "unixepoch")) as year, ROUND( SUM( sum ), 2 ) as total FROM archive_day_rain GROUP BY year ORDER BY total DESC LIMIT 1;'
        elif driver == "weedb.mysql":
            year_rainiest_month_sql = 'SELECT FROM_UNIXTIME( dateTime, "%%m" ) AS month, ROUND( SUM( sum ), 2 ) AS total FROM archive_day_rain WHERE year( FROM_UNIXTIME( dateTime ) ) = "{0}" GROUP BY month ORDER BY total DESC LIMIT 1;'.format( time.strftime( "%Y", time.localtime( time.time() ) ) ) # Why does this one require .format() but the other's don't?
            at_rainiest_month_sql = 'SELECT FROM_UNIXTIME( dateTime, "%%m" ) AS month, FROM_UNIXTIME( dateTime, "%%Y" ) AS year, ROUND( SUM( sum ), 2 ) AS total FROM archive_day_rain GROUP BY month, year ORDER BY total DESC LIMIT 1;'
            year_rain_data_sql = 'SELECT dateTime, ROUND( sum, 2 ) FROM archive_day_rain WHERE year( FROM_UNIXTIME( dateTime ) ) = "%s";' % time.strftime( "%Y", time.localtime( time.time() ) )
            # The all stats from http://www.weewx.com/docs/customizing.htm doesn't seem to calculate "Total Rainfall for" all time stat correctly. 
            at_rain_highest_year_sql = 'SELECT FROM_UNIXTIME( dateTime, "%%Y" ) AS year, ROUND( SUM( sum ), 2 ) AS total FROM archive_day_rain GROUP BY year ORDER BY total DESC LIMIT 1;'
            
        # Rainiest month
        year_rainiest_month_query = wx_manager.getSql( year_rainiest_month_sql )
        if year_rainiest_month_query is not None:
            year_rainiest_month_tuple = (year_rainiest_month_query[1], rain_unit, 'group_rain')
            year_rainiest_month_converted = rain_round % self.generator.converter.convert(year_rainiest_month_tuple)[0]
            year_rainiest_month = [ calendar.month_name[ int( year_rainiest_month_query[0] ) ], locale.format("%g", float(year_rainiest_month_converted)) ]
        else:
            year_rainiest_month = [ "N/A", 0.0 ]

        # All time rainiest month
        at_rainiest_month_query = wx_manager.getSql( at_rainiest_month_sql )
        at_rainiest_month_tuple = (at_rainiest_month_query[2], rain_unit, 'group_rain')
        at_rainiest_month_converted = rain_round % self.generator.converter.convert(at_rainiest_month_tuple)[0]
        at_rainiest_month = [ calendar.month_name[ int( at_rainiest_month_query[0] ) ] + ", " + at_rainiest_month_query[1], locale.format("%g", float(at_rainiest_month_converted)) ]
        
        # All time rainiest year
        at_rain_highest_year_query = wx_manager.getSql( at_rain_highest_year_sql )
        at_rain_highest_year_tuple = (at_rain_highest_year_query[1], rain_unit, 'group_rain')
        #at_rain_highest_year_converted = round( self.generator.converter.convert(at_rain_highest_year_tuple)[0], rain_round )
        at_rain_highest_year_converted = rain_round % self.generator.converter.convert(at_rain_highest_year_tuple)[0]
        at_rain_highest_year = [ at_rain_highest_year_query[0], locale.format("%g", float(at_rain_highest_year_converted)) ]
        
        
        # Consecutive days with/without rainfall
        # dateTime needs to be epoch. Conversion done in the template using #echo
        year_days_with_rain_total = 0
        year_days_without_rain_total = 0
        year_days_with_rain_output = {}
        year_days_without_rain_output = {}
        year_rain_query = wx_manager.genSql( year_rain_data_sql )
        for row in year_rain_query:
            # Original MySQL way: CASE WHEN sum!=0 THEN @total+1 ELSE 0 END
            if row[1] != 0:
                year_days_with_rain_total += 1
            else:
                year_days_with_rain_total = 0
                
            # Original MySQL way: CASE WHEN sum=0 THEN @total+1 ELSE 0 END
            if row[1] == 0:
                year_days_without_rain_total += 1
            else:
                year_days_without_rain_total = 0
            
            year_days_with_rain_output[row[0]] = year_days_with_rain_total
            year_days_without_rain_output[row[0]] = year_days_without_rain_total

        if year_days_with_rain_output:
            year_days_with_rain = max( zip( year_days_with_rain_output.values(), year_days_with_rain_output.keys() ) )
        else:
            year_days_with_rain = [ 0.0, calendar.timegm( time.gmtime() ) ]
            
        if year_days_without_rain_output:
            year_days_without_rain = max( zip( year_days_without_rain_output.values(), year_days_without_rain_output.keys() ) )
        else:
            year_days_without_rain = [ 0.0, calendar.timegm( time.gmtime() ) ]
           
        at_days_with_rain_total = 0
        at_days_without_rain_total = 0
        at_days_with_rain_output = {}
        at_days_without_rain_output = {}
        at_rain_query = wx_manager.genSql( "SELECT dateTime, ROUND( sum, 2 ) FROM archive_day_rain;" )
        for row in at_rain_query:
            # Original MySQL way: CASE WHEN sum!=0 THEN @total+1 ELSE 0 END
            if row[1] != 0:
                at_days_with_rain_total += 1
            else:
                at_days_with_rain_total = 0
                
            # Original MySQL way: CASE WHEN sum=0 THEN @total+1 ELSE 0 END
            if row[1] == 0:
                at_days_without_rain_total += 1
            else:
                at_days_without_rain_total = 0
            
            at_days_with_rain_output[row[0]] = at_days_with_rain_total
            at_days_without_rain_output[row[0]] = at_days_without_rain_total

        at_days_with_rain = max( zip( at_days_with_rain_output.values(), at_days_with_rain_output.keys() ) )
        at_days_without_rain = max( zip( at_days_without_rain_output.values(), at_days_without_rain_output.keys() ) )

        """
        This portion is right from the weewx sample http://www.weewx.com/docs/customizing.htm
        """
        all_stats = TimespanBinder( timespan,
                                    db_lookup,
                                    formatter=self.generator.formatter,
                                    converter=self.generator.converter,
                                    skin_dict=self.generator.skin_dict )
                                    
        # Get the unit label from the skin dict for speed. 
        windSpeedUnit = self.generator.skin_dict["Units"]["Groups"]["group_speed"]
        windSpeedUnitLabel = self.generator.skin_dict["Units"]["Labels"][windSpeedUnit]
        
        
        """
        Get NOAA Data
        """
        years = []
        noaa_header_html = ""
        default_noaa_file = ""
        noaa_dir = local_root + "/NOAA/"
        
        try:
            noaa_file_list = os.listdir( noaa_dir )

            # Generate a list of years based on file name
            for f in noaa_file_list:
                filename = f.split(".")[0] # Drop the .txt
                year = filename.split("-")[1]
                years.append(year)

            years = sorted( set( years ) )[::-1] # Remove duplicates with set, and sort numerically, then reverse sort with [::-1] oldest year last
            #first_year = years[0]
            #final_year = years[-1]
            
            for y in years:
                # Link to the year file
                if os.path.exists( noaa_dir + "NOAA-%s.txt" % y ):
                    noaa_header_html += '<a href="?yr=%s" class="noaa_rep_nav"><b>%s</b></a>:' % ( y, y )
                else:
                    noaa_header_html += '<span class="noaa_rep_nav"><b>%s</b></span>:' % y
                    
                # Loop through all 12 months and find if the file exists. 
                # If the file doesn't exist, just show the month name in the header without a href link.
                # There is no month 13, but we need to loop to 12, so 13 is where it stops.
                for i in range(1, 13):
                    month_num = format( i, '02' ) # Pad the number with a 0 since the NOAA files use 2 digit month
                    month_abbr = calendar.month_abbr[ i ]
                    if os.path.exists( noaa_dir + "NOAA-%s-%s.txt" % ( y, month_num ) ):
                        noaa_header_html += ' <a href="?yr=%s&amp;mo=%s" class="noaa_rep_nav"><b>%s</b></a>' % ( y, month_num, month_abbr )
                    else:
                        noaa_header_html += ' <span class="noaa_rep_nav"><b>%s</b></span>' % month_abbr
                
                # Row build complete, push next row to new line
                noaa_header_html += "<br>"
                
            # Find the current month's NOAA file for the default file to show on JavaScript page load. 
            # The NOAA files are generated as part of this skin, but if for some reason that the month file doesn't exist, use the year file.
            now = datetime.datetime.now()
            current_year = str( now.year )
            current_month = str( format( now.month, '02' ) )
            if os.path.exists( noaa_dir + "NOAA-%s-%s.txt" % ( current_year, current_month ) ):
                default_noaa_file = "NOAA-%s-%s.txt" % ( current_year, current_month )
            else:
                default_noaa_file = "NOAA-%s.txt" % current_year
        except:
            # There's an error - I've seen this on first run and the NOAA folder is not created yet. Skip this section.
            pass

            
        """
        Forecast Data
        """
        if self.generator.skin_dict['Extras']['forecast_enabled'] == "1":
            forecast_file = local_root + "/json/darksky_forecast.json"
            forecast_json_url = belchertown_root_url + "/json/darksky_forecast.json"
            darksky_secret_key = self.generator.skin_dict['Extras']['darksky_secret_key']
            darksky_units = self.generator.skin_dict['Extras']['darksky_units'].lower()
            darksky_lang = self.generator.skin_dict['Extras']['darksky_lang'].lower()
            latitude = self.generator.config_dict['Station']['latitude']
            longitude = self.generator.config_dict['Station']['longitude']
            forecast_alert_enabled = int( self.generator.skin_dict['Extras']['forecast_alert_enabled'] )
            forecast_stale_timer = self.generator.skin_dict['Extras']['forecast_stale']
            forecast_is_stale = False
            
            forecast_url = "https://api.darksky.net/forecast/%s/%s,%s?units=%s&lang=%s" % ( darksky_secret_key, latitude, longitude, darksky_units, darksky_lang )
            
            # Determine if the file exists and get it's modified time
            if os.path.isfile( forecast_file ):
                if ( int( time.time() ) - int( os.path.getmtime( forecast_file ) ) ) > int( forecast_stale_timer ):
                    forecast_is_stale = True
            else:
                # File doesn't exist, download a new copy
                forecast_is_stale = True
            
            # File is stale, download a new copy
            if forecast_is_stale:
                # Download new forecast data
                try:
                    import urllib2
                    user_agent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3'
                    headers = { 'User-Agent' : user_agent }
                    req = urllib2.Request( forecast_url, None, headers )
                    response = urllib2.urlopen( req )
                    page = response.read()
                    response.close()
                except Exception as error:
                    raise Warning( "Error downloading forecast data. Check the URL in your configuration and try again. You are trying to use URL: %s, and the error is: %s" % ( forecast_url, error ) )
                    
                # Save forecast data to file. w+ creates the file if it doesn't exist, and truncates the file and re-writes it everytime
                try:
                    with open( forecast_file, 'w+' ) as file:
                        file.write( page )
                        loginf( "New forecast file downloaded to %s" % forecast_file )
                except IOError, e:
                    raise Warning( "Error writing forecast info to %s. Reason: %s" % ( forecast_file, e) )

            # Process the forecast file
            with open( forecast_file, "r" ) as read_file:
                data = json.load( read_file )
            
            current_obs_summary = data["currently"]["summary"]
            visibility = locale.format("%g", float( data["currently"]["visibility"] ) )
            
            if data["currently"]["icon"] == "partly-cloudy-night":
                current_obs_icon = '<img id="wxicon" src="'+belchertown_root_url+'/images/partly-cloudy-night.png">'
            else:
                current_obs_icon = '<img id="wxicon" src="'+belchertown_root_url+'/images/'+data["currently"]["icon"]+'.png">'

            # Even though we specify the DarkSky unit as darksky_units, if the user selects "auto" as their unit
            # then we don't know what DarkSky will return for visibility. So always use the DarkSky output to 
            # tell us what unit they are using. This fixes the guessing game for what label to use for the DarkSky "auto" unit
            if ( data["flags"]["units"].lower() == "us" ) or ( data["flags"]["units"].lower() == "uk2" ):
                visibility_unit = "miles"
            elif ( data["flags"]["units"].lower() == "si" ) or ( data["flags"]["units"].lower() == "ca" ):
                visibility_unit = "km"
            else:
                visibility_unit = ""
                
        else:
            forecast_json_url = ""
            current_obs_icon = ""
            current_obs_summary = ""
            visibility = ""
            visibility_unit = ""
        
        
        """
        Earthquake Data
        """
        # Only process if Earthquake data is enabled
        if self.generator.skin_dict['Extras']['earthquake_enabled'] == "1":
            earthquake_file = local_root + "/json/earthquake.json"
            earthquake_stale_timer = self.generator.skin_dict['Extras']['earthquake_stale']
            latitude = self.generator.config_dict['Station']['latitude']
            longitude = self.generator.config_dict['Station']['longitude']
            earthquake_maxradiuskm = self.generator.skin_dict['Extras']['earthquake_maxradiuskm']
            #Sample URL from Belchertown Weather: http://earthquake.usgs.gov/fdsnws/event/1/query?limit=1&lat=42.223&lon=-72.374&maxradiuskm=1000&format=geojson&nodata=204&minmag=2
            earthquake_url = "http://earthquake.usgs.gov/fdsnws/event/1/query?limit=1&lat=%s&lon=%s&maxradiuskm=%s&format=geojson&nodata=204&minmag=2" % ( latitude, longitude, earthquake_maxradiuskm )
            earthquake_is_stale = False
            
            # Determine if the file exists and get it's modified time
            if os.path.isfile( earthquake_file ):
                if ( int( time.time() ) - int( os.path.getmtime( earthquake_file ) ) ) > int( earthquake_stale_timer ):
                    earthquake_is_stale = True
            else:
                # File doesn't exist, download a new copy
                earthquake_is_stale = True
            
            # File is stale, download a new copy
            if earthquake_is_stale:
                # Download new earthquake data
                try:
                    import urllib2
                    user_agent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3'
                    headers = { 'User-Agent' : user_agent }
                    req = urllib2.Request( earthquake_url, None, headers )
                    response = urllib2.urlopen( req )
                    page = response.read()
                    response.close()
                    if weewx.debug:
                        logdbg( "Downloading earthquake data using urllib2 was successful" )
                except Exception as error:
                    if weewx.debug:
                        logdbg( "Error downloading earthquake data with urllib2, reverting to curl and subprocess" )
                    # Nested try - only execute if the urllib2 method fails
                    try:
                        import subprocess
                        command = 'curl -L --silent "%s"' % earthquake_url
                        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        page = p.communicate()[0]
                        if weewx.debug:
                            logdbg( "Downloading earthquake data with curl was successful." )
                    except Exception as error:
                        raise Warning( "Error downloading earthquake data using urllib2 and subprocess curl. Your software may need to be updated, or the URL is incorrect. You are trying to use URL: %s, and the error is: %s" % ( earthquake_url, error ) )

                # Save earthquake data to file. w+ creates the file if it doesn't exist, and truncates the file and re-writes it everytime
                try:
                    with open( earthquake_file, 'w+' ) as file:
                        file.write( page )
                        if weewx.debug:
                            logdbg( "Earthquake data saved to %s" % earthquake_file )
                except IOError, e:
                    raise Warning( "Error writing earthquake data to %s. Reason: %s" % ( earthquake_file, e) )

            # Process the earthquake file        
            with open( earthquake_file, "r" ) as read_file:
                eqdata = json.load( read_file )
            
            try:
                eqtime = eqdata["features"][0]["properties"]["time"] / 1000
                equrl = eqdata["features"][0]["properties"]["url"]
                eqplace = eqdata["features"][0]["properties"]["place"]
                eqmag = eqdata["features"][0]["properties"]["mag"]
                eqlat = str( round( eqdata["features"][0]["geometry"]["coordinates"][0], 4 ) )
                eqlon = str( round( eqdata["features"][0]["geometry"]["coordinates"][1], 4 ) )
            except:
                # No earthquake data
                eqtime = "No recent earthquake data available!"
                equrl = ""
                eqplace = ""
                eqmag = ""
                eqlat = ""
                eqlon = ""
                
        else:
            eqtime = ""
            equrl = ""
            eqplace = ""
            eqmag = ""
            eqlat = ""
            eqlon = ""
        
        
        """
        Social Share
        """
        station_location = self.generator.config_dict["Station"]["location"]
        facebook_enabled = self.generator.skin_dict['Extras']['facebook_enabled']
        twitter_enabled = self.generator.skin_dict['Extras']['twitter_enabled']
        twitter_owner = self.generator.skin_dict['Extras']['twitter_owner']
        twitter_hashtags = self.generator.skin_dict['Extras']['twitter_hashtags']
                
        if facebook_enabled == "1": 
            facebook_html = """
                <div id="fb-root"></div>
                <script>(function(d, s, id) {
                  var js, fjs = d.getElementsByTagName(s)[0];
                  if (d.getElementById(id)) return;
                  js = d.createElement(s); js.id = id;
                  js.src = "//connect.facebook.net/en_US/sdk.js#xfbml=1&version=v2.5";
                  fjs.parentNode.insertBefore(js, fjs);
                }(document, 'script', 'facebook-jssdk'));</script>
                <div class="fb-like" data-href="%s" data-width="500px" data-layout="button_count" data-action="like" data-show-faces="false" data-share="true"></div>
            """ % belchertown_root_url
        else:
            facebook_html = ""
        
        if twitter_enabled == "1":
            twitter_html = """
                <script>
                    !function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0],p=/^http:/.test(d.location)?'http':'https';if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src=p+'://platform.twitter.com/widgets.js';fjs.parentNode.insertBefore(js,fjs);}}(document, 'script', 'twitter-wjs');
                </script>
                <a href="https://twitter.com/share" class="twitter-share-button" data-url="%s" data-text="%s Weather Conditions" data-via="%s" data-hashtags="%s">Tweet</a>
            """ % ( belchertown_root_url, station_location, twitter_owner, twitter_hashtags )
        else:
            twitter_html = ""
        
        # Build the output
        social_html = ""
        if facebook_html != "" or twitter_html != "":
            social_html = '<div class="wx-stn-share">'
            # Facebook first
            if facebook_html != "":
                social_html += facebook_html
            # Add a separator margin if both are enabled
            if facebook_html != "" and twitter_html != "":
                social_html += '<div class="wx-share-sep"></div>'
            # Twitter second
            if twitter_html != "":
                social_html += twitter_html
            social_html += "</div>"

            
        # Build the search list with the new values
        search_list_extension = { 'belchertown_version': VERSION,
                                  'belchertown_root_url': belchertown_root_url,
                                  'belchertown_debug': belchertown_debug,
                                  'moment_js_utc_offset': moment_js_utc_offset,
                                  'highcharts_timezoneoffset': highcharts_timezoneoffset,
                                  'system_locale': system_locale,
                                  'system_locale_js': system_locale_js,
                                  'locale_encoding': locale_encoding,
                                  'highcharts_decimal': highcharts_decimal,
                                  'radar_html': radar_html,
                                  'archive_interval_ms': archive_interval_ms,
                                  'charts': charts,
                                  'alltime' : all_stats,
                                  'year_outTemp_range_max': year_outTemp_range_max,
                                  'year_outTemp_range_min': year_outTemp_range_min,
                                  'at_outTemp_range_max' : at_outTemp_range_max,
                                  'at_outTemp_range_min': at_outTemp_range_min,
                                  'rainiest_day': rainiest_day,
                                  'at_rainiest_day': at_rainiest_day,
                                  'year_rainiest_month': year_rainiest_month,
                                  'at_rainiest_month': at_rainiest_month,
                                  'at_rain_highest_year': at_rain_highest_year,
                                  'year_days_with_rain': year_days_with_rain,
                                  'year_days_without_rain': year_days_without_rain,
                                  'at_days_with_rain': at_days_with_rain,
                                  'at_days_without_rain': at_days_without_rain,
                                  'windSpeedUnitLabel': windSpeedUnitLabel,
                                  'noaa_header_html': noaa_header_html,
                                  'default_noaa_file': default_noaa_file,
                                  'forecast_json_url': forecast_json_url,
                                  'current_obs_icon': current_obs_icon,
                                  'current_obs_summary': current_obs_summary,
                                  'visibility': visibility,
                                  'visibility_unit': visibility_unit,
                                  'earthquake_time': eqtime,
                                  'earthquake_url': equrl,
                                  'earthquake_place': eqplace,
                                  'earthquake_magnitude': eqmag,
                                  'earthquake_lat': eqlat,
                                  'earthquake_lon': eqlon,
                                  'social_html': social_html }

        # Finally, return our extension as a list:
        return [search_list_extension]

# =============================================================================
# JsonGenerator
# =============================================================================

class JsonGenerator(weewx.reportengine.ReportGenerator):
    """Class for generating JSON files for the Highcharts. 
    Adapted from the ImageGenerator class.
    
    Useful attributes (some inherited from ReportGenerator):

        config_dict:      The weewx configuration dictionary 
        skin_dict:        The dictionary for this skin
        gen_ts:           The generation time
        first_run:        Is this the first time the generator has been run?
        stn_info:         An instance of weewx.station.StationInfo
        record:           A copy of the "current" record. May be None.
        formatter:        An instance of weewx.units.Formatter
        converter:        An instance of weewx.units.Converter
        search_list_objs: A list holding search list extensions
        db_binder:        An instance of weewx.manager.DBBinder from which the
                          data should be extracted
    """
    
    def run(self):
        """Main entry point for file generation."""
        
        self.chart_dict = self.skin_dict['Charts']
        self.converter = weewx.units.Converter.fromSkinDict(self.chart_dict)
        self.formatter = weewx.units.Formatter.fromSkinDict(self.skin_dict)
        self.db_lookup = self.db_binder.bind_default()
        binding = self.config_dict['StdReport'].get('data_binding', 'wx_binding')
        archive = self.db_binder.get_manager(binding)
        start_ts = archive.firstGoodStamp()
        stop_ts = archive.lastGoodStamp()
        timespan = weeutil.weeutil.TimeSpan(start_ts, stop_ts)

        # Setup title dict for plot titles
        try:
            d = self.skin_dict['Labels']['Generic']
        except KeyError:
            d = {}
        title_dict = weeutil.weeutil.KeyDict(d)
        
        # Final output dict
        output = {}
                
        # Loop through each timespan
        for chart_group in self.chart_dict.sections:
            output[chart_group] = OrderedDict() # This retains the order in which to load the charts on the page.
            
            # Loop through each chart within the chart_group
            for plotname in self.chart_dict[chart_group].sections:
                output[chart_group][plotname] = {}
                output[chart_group][plotname]["series"] = OrderedDict() # This retains the observation position in the dictionary to match the order in the conf so the chart is in the right user-defined order
                output[chart_group][plotname]["options"] = {}
                output[chart_group][plotname]["options"]["renderTo"] = chart_group + plotname # daychart1, weekchart1, etc. Used for the graphs page and the different chart_groups
                
                plot_options = weeutil.weeutil.accumulateLeaves(self.chart_dict[chart_group][plotname])
                
                plotgen_ts = self.gen_ts
                if not plotgen_ts:
                    plotgen_ts = stop_ts
                    if not plotgen_ts:
                        plotgen_ts = time.time()
                
                # Look for any keyword timespans first and default to those start/stop times for the chart
                time_length = plot_options.get('time_length', 86400)
                if time_length == "today":
                    minstamp, maxstamp = archiveDaySpan( timespan.stop )
                elif time_length == "week":
                    minstamp, maxstamp = archiveWeekSpan( timespan.stop )
                elif time_length == "month":
                    minstamp, maxstamp = archiveMonthSpan( timespan.stop )
                elif time_length == "year":
                    minstamp, maxstamp = archiveYearSpan( timespan.stop )
                else:
                    # Rolling timespans using seconds
                    (minstamp, maxstamp, timeinc) = weeplot.utilities.scaletime(plotgen_ts - int(plot_options.get('time_length', 86400)), plotgen_ts)
                                
                chart_title = plot_options.get("title", "")
                output[chart_group][plotname]["options"]["title"] = chart_title
                
                # Get the type of plot ("bar', 'line', 'spline', or 'scatter')
                plottype = plot_options.get('type', 'line')
                output[chart_group][plotname]["options"]["type"] = plottype
                
                polar = plot_options.get('polar', None)
                if polar:
                    output[chart_group][plotname]["polar"] = polar
                
                # Loop through each observation within the chart chart_group
                for line_name in self.chart_dict[chart_group][plotname].sections:
                    output[chart_group][plotname]["series"][line_name] = {}
                    output[chart_group][plotname]["series"][line_name]["obsType"] = line_name
                    
                    line_options = weeutil.weeutil.accumulateLeaves(self.chart_dict[chart_group][plotname][line_name])
                    
                    # Find the observation type. (e.g. outTemp, rainFall, windDir, etc.)
                    #obs_type = line_options.get('data_type', line_name) # TODO I don't think this is needed.
                    obs_type = line_name
                    
                    # Get any custom names for this observation 
                    name = line_options.get('name', None)
                    if not name:
                        # No explicit name. Look up a generic one. NB: title_dict is a KeyDict which
                        # will substitute the key if the value is not in the dictionary.
                        name = title_dict[obs_type]
                                        
                    if obs_type == "rainTotal":
                        obs_label = "rain"
                    else:
                        obs_label = obs_type
                    unit_label = line_options.get('y_label', weewx.units.get_label_string(self.formatter, self.converter, obs_label))
                    
                    # Look for aggregation type:
                    aggregate_type = line_options.get('aggregate_type')
                    if aggregate_type in (None, '', 'None', 'none'):
                        # No aggregation specified.
                        aggregate_type = aggregate_interval = None
                    else:
                        try:
                            # Aggregation specified. Get the interval.
                            aggregate_interval = line_options.as_int('aggregate_interval')
                        except KeyError:
                            syslog.syslog(syslog.LOG_ERR, "JsonGenerator: aggregate interval required for aggregate type %s" % aggregate_type)
                            syslog.syslog(syslog.LOG_ERR, "JsonGenerator: line type %s skipped" % obs_type)
                            continue
                    
                    # Build the final array items. 
                    
                    # This for loop is to get any user provided highcharts series config data. Built-in highcharts variable names accepted.  
                    for highcharts_config, highcharts_value in self.chart_dict[chart_group][plotname][line_name].items():
                        output[chart_group][plotname]["series"][line_name][highcharts_config] = highcharts_value
                    
                    # Override any highcharts series configs with standardized data, then generate the data output
                    output[chart_group][plotname]["series"][line_name]["name"] = name

                    # yAxis customizations. Place into series for custom JavaScript. Highcharts will ignore these by default
                    output[chart_group][plotname]["options"]["yAxisLabel"] = "(" + unit_label.strip() + ")"
                    output[chart_group][plotname]["series"][line_name]["yAxisLabel"] = "(" + unit_label.strip() + ")"
                                    
                    # Set the yAxis min and max if present. Useful for the rxCheckPercent plots
                    yaxis_min = plot_options.get('yaxis_min', None)
                    if yaxis_min:
                        output[chart_group][plotname]["series"][line_name]["yaxis_min"] = yaxis_min
                    yaxis_max = plot_options.get('yaxis_max', None)
                    if yaxis_max:
                        output[chart_group][plotname]["series"][line_name]["yaxis_max"] = yaxis_max
                    
                    # Build series data
                    output[chart_group][plotname]["series"][line_name]["data"] = self._getObservationData(obs_type, minstamp, maxstamp, aggregate_type, aggregate_interval)
            
            # This consolidates all chart_groups into the chart_group JSON (day.json, week.json, month.json, year.json) and saves them to HTML_ROOT/json
            html_dest_dir = os.path.join(self.config_dict['WEEWX_ROOT'],
                                     self.skin_dict['HTML_ROOT'],
                                     "json")
            json_filename = html_dest_dir + "/" + chart_group + ".json"
            with open(json_filename, mode='w') as fd:
                    fd.write( json.dumps( output[chart_group] ) )

    def _getObservationData(self, observation, start_ts, end_ts, aggregate_type, aggregate_interval):
        """Get the SQL vectors for the observation, the aggregate type and the interval of time"""
        
        # Special Belchertown Skin rain counter
        if observation == "rainTotal":
            obs_lookup = "rain"
        else:
            obs_lookup = observation
                
        (time_start_vt, time_stop_vt, obs_vt) = self.db_lookup().getSqlVectors(TimeSpan(start_ts, end_ts), obs_lookup, aggregate_type, aggregate_interval)
        obs_vt = self.converter.convert(obs_vt)
                
        # Special handling for the rain.
        if observation == "rainTotal":
            # The weewx "rain" observation is really "bucket tips". This special counter increments the bucket tips over timespan to return rain total.
            rain_count = 0
            rain_total = []
            for rain in obs_vt[0]:
                # If the rain value is None or "", add it as 0.0
                if rain is None or rain == "":
                    rain = 0.0
                rain_count = rain_count + rain
                rain_total.append( round( rain_count, 2 ) )
                time_ms = [float(x) * 1000 for x in time_stop_vt[0]]
                data = zip(time_ms, rain_total)
        elif observation == "rainRate":
            # Instead of using the _roundNone to round rainRate, we just return the rainRate untouched.
            rainrate_holder = []
            for rainRate in obs_vt[0]:
                rainrate_holder.append( rainRate )
                time_ms = [float(x) * 1000 for x in time_stop_vt[0]]
                data = zip(time_ms, rainrate_holder)
        else:        
            # Send all other observations through the usual process, except Barometer for finer detail
            if observation == "barometer":
                usageRound = int(self.skin_dict['Units']['StringFormats'].get(obs_vt[1], "1f")[-2])
                obsRound_vt = [round(x,usageRound) if x is not None else None for x in obs_vt[0]]
            else:
                usageRound = int(self.skin_dict['Units']['StringFormats'].get(obs_vt[2], "2f")[-2])
                obsRound_vt = [self._roundNone(x, usageRound) for x in obs_vt[0]]
            time_ms = [float(x) * 1000 for x in time_stop_vt[0]]
            data = zip(time_ms, obsRound_vt)
        
        return data
        
    def _roundNone(self, value, places):
        """Round value to 'places' places but also permit a value of None"""
        if value is not None:
            try:
                value = round(value, places)
            except Exception, e:
                value = None
        return value

