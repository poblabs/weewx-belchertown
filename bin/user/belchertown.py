# Extension for the Belchertown skin. 
# This extension builds search list extensions as well
# as a crude "cron" to download necessary files. 
#
# Pat O'Brien, August 19, 2018

import datetime
import time
import calendar
import json
import os
import syslog

import weewx
import weecfg

from weewx.cheetahgenerator import SearchList
from weewx.tags import TimespanBinder
from weeutil.weeutil import TimeSpan

def logmsg(level, msg):
    syslog.syslog(level, 'Belchertown Extension: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)
    
# Print version in syslog for easier troubleshooting
VERSION = "0.8.1"
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
        
        # Set a default radar URL using station's lat/lon. Moved from skin.conf so we can get station lat/lon from weewx.conf. A lot of stations out there with Belchertown 0.1 through 0.7 are showing the visitor's location and not the proper station location because nobody edited the radar_html which did not have lat/lon set previously.
        if self.generator.skin_dict['Extras']['radar_html'] == "":
            lat = self.generator.config_dict['Station']['latitude']
            lon = self.generator.config_dict['Station']['longitude']
            radar_html = '<iframe width="650" height="360" src="https://embed.windy.com/embed2.html?lat={}&lon={}&zoom=8&level=surface&overlay=radar&menu=&message=true&marker=&calendar=&pressure=&type=map&location=coordinates&detail=&detailLat={}&detailLon={}&metricWind=mph&metricTemp=%C2%B0F&radarRange=-1" frameborder="0"></iframe>'.format( lat, lon, lat, lon )
        else:
            radar_html = self.generator.skin_dict['Extras']['radar_html']
        
        # Handle the about.inc and records.inc files.
        # about.inc: if the file is present use it, otherwise use a default "please setup about.inc". 
        # records.inc: if the file is present use it, therwise do not show anything. 
        about_file = local_skin_root + "/about.inc"
        about_page_text = """
        <p>Welcome to your new about page!</p>
        <p>To change this text:
        <ul>
            <li> Rename the <code>skins/Belchertown/about.inc.example</code> file to <code>about.inc</code></li>
            <ul>
                <li> or create a new file at <code>skins/Belchertown/about.inc</code></li>
            </ul>
            <li> Use the example text within <code>skins/Belchertown/about.inc.example</code> to create your about page description!</li>
            <li>Full HTML is accepted.</li>
        </ul>
        </p>
        <p><a href="https://github.com/poblabs/weewx-belchertown#creating-about-page-and-records-page" target="_blank">Click this link if you need help!</a>
        <p>For an example of what this page could say, please see <a href="https://belchertownweather.com/about" target="_blank">https://belchertownweather.com/about</a></p>
        """
        
        try:
            with open( about_file, 'r' ) as af:
                about_page_text = af.read()
        except:
            # File doesn't exist - use the default text. 
            pass
        
        records_file = local_skin_root + "/records.inc"
        records_page_text = ""
        try:
            with open( records_file, 'r' ) as rf:
                records_page_text = rf.read()
        except:
            # File doesn't exist - show nothing. 
            pass        
        
        # Custom Row 1 on index. Between station info and forecast
        index_hook_after_station_info_enabled = 0
        index_hook_after_station_info_file = local_skin_root + "/index_hook_after_station_info.inc"
        index_hook_after_station_info_text = ""
        try:
            with open( index_hook_after_station_info_file, 'r' ) as ihasif:
                index_hook_after_station_info_text = ihasif.read()
        except:
            # File doesn't exist - show nothing. 
            pass
        # Check whether or not to display the custom hook area
        if index_hook_after_station_info_text != "":
            index_hook_after_station_info_enabled = 1
            
        # Custom Row 2 on index. Between forecast and snapshot records row
        index_hook_after_forecast_enabled = 0
        index_hook_after_forecast_file = local_skin_root + "/index_hook_after_forecast.inc"
        index_hook_after_forecast_text = ""
        try:
            with open( index_hook_after_forecast_file, 'r' ) as ihaff:
                index_hook_after_forecast_text = ihaff.read()
        except:
            # File doesn't exist - show nothing. 
            pass
        # Check whether or not to display the custom hook area
        if index_hook_after_forecast_text != "":
            index_hook_after_forecast_enabled = 1
            
        # Custom Row 3 on index. Between snapshot records row and the graphs
        index_hook_after_snapshot_enabled = 0
        index_hook_after_snapshot_file = local_skin_root + "/index_hook_after_snapshot.inc"
        index_hook_after_snapshot_text = ""
        try:
            with open( index_hook_after_snapshot_file, 'r' ) as ihasf:
                index_hook_after_snapshot_text = ihasf.read()
        except:
            # File doesn't exist - show nothing. 
            pass
        # Check whether or not to display the custom hook area
        if index_hook_after_snapshot_text != "":
            index_hook_after_snapshot_enabled = 1
            
        # Custom Row 4 on index. After the charts
        index_hook_after_charts_enabled = 0
        index_hook_after_charts_file = local_skin_root + "/index_hook_after_charts.inc"
        index_hook_after_charts_text = ""
        try:
            with open( index_hook_after_charts_file, 'r' ) as ihacf:
                index_hook_after_charts_text = ihacf.read()
        except:
            # File doesn't exist - show nothing. 
            pass
        # Check whether or not to display the custom hook area
        if index_hook_after_charts_text != "":
            index_hook_after_charts_enabled = 1
        
        
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
        outTemp_round = int(self.generator.skin_dict['Units']['StringFormats'].get("group_temperature", "1f")[-2])

        # Largest Daily Temperature Range Conversions
        # Max temperature for this day
        if year_outTemp_max_range_query is not None:
            year_outTemp_max_range_max_tuple = (year_outTemp_max_range_query[3], outTemp_unit, 'group_temperature')
            year_outTemp_max_range_max = round( self.generator.converter.convert(year_outTemp_max_range_max_tuple)[0], outTemp_round )
            # Min temperature for this day
            year_outTemp_max_range_min_tuple = (year_outTemp_max_range_query[2], outTemp_unit, 'group_temperature')
            year_outTemp_max_range_min = round ( self.generator.converter.convert(year_outTemp_max_range_min_tuple)[0], outTemp_round )
            # Largest Daily Temperature Range total
            year_outTemp_max_range_total = round( year_outTemp_max_range_max - year_outTemp_max_range_min, outTemp_round )
            # Replace the SQL Query output with the converted values
            year_outTemp_range_max = [ year_outTemp_max_range_query[0], year_outTemp_max_range_total, year_outTemp_max_range_min, year_outTemp_max_range_max ]
        else:
            year_outTemp_range_max = [ calendar.timegm( time.gmtime() ), 0.0, 0.0, 0.0 ]
        
        # Smallest Daily Temperature Range Conversions
        # Max temperature for this day
        if year_outTemp_min_range_query is not None:
            year_outTemp_min_range_max_tuple = (year_outTemp_min_range_query[3], outTemp_unit, 'group_temperature')
            year_outTemp_min_range_max = round( self.generator.converter.convert(year_outTemp_min_range_max_tuple)[0], outTemp_round )
            # Min temperature for this day
            year_outTemp_min_range_min_tuple = (year_outTemp_min_range_query[2], outTemp_unit, 'group_temperature')
            year_outTemp_min_range_min = round( self.generator.converter.convert(year_outTemp_min_range_min_tuple)[0], outTemp_round )
            # Smallest Daily Temperature Range total
            year_outTemp_min_range_total = round( year_outTemp_min_range_max - year_outTemp_min_range_min, outTemp_round )
            # Replace the SQL Query output with the converted values
            year_outTemp_range_min = [ year_outTemp_min_range_query[0], year_outTemp_min_range_total, year_outTemp_min_range_min, year_outTemp_min_range_max ]
        else:
            year_outTemp_range_min = [ calendar.timegm( time.gmtime() ), 0.0, 0.0, 0.0 ]
        
        # All Time - Largest Daily Temperature Range Conversions
        # Max temperature
        at_outTemp_max_range_max_tuple = (at_outTemp_max_range_query[3], outTemp_unit, 'group_temperature')
        at_outTemp_max_range_max = round( self.generator.converter.convert(at_outTemp_max_range_max_tuple)[0], outTemp_round )
        # Min temperature for this day
        at_outTemp_max_range_min_tuple = (at_outTemp_max_range_query[2], outTemp_unit, 'group_temperature')
        at_outTemp_max_range_min = round ( self.generator.converter.convert(at_outTemp_max_range_min_tuple)[0], outTemp_round )
        # Largest Daily Temperature Range total
        at_outTemp_max_range_total = round( at_outTemp_max_range_max - at_outTemp_max_range_min, outTemp_round )
        # Replace the SQL Query output with the converted values
        at_outTemp_range_max = [ at_outTemp_max_range_query[0], at_outTemp_max_range_total, at_outTemp_max_range_min, at_outTemp_max_range_max ]

        # All Time - Smallest Daily Temperature Range Conversions
        # Max temperature for this day
        at_outTemp_min_range_max_tuple = (at_outTemp_min_range_query[3], outTemp_unit, 'group_temperature')
        at_outTemp_min_range_max = round( self.generator.converter.convert(at_outTemp_min_range_max_tuple)[0], outTemp_round )
        # Min temperature for this day
        at_outTemp_min_range_min_tuple = (at_outTemp_min_range_query[2], outTemp_unit, 'group_temperature')
        at_outTemp_min_range_min = round( self.generator.converter.convert(at_outTemp_min_range_min_tuple)[0], outTemp_round )
        # Smallest Daily Temperature Range total
        at_outTemp_min_range_total = round( at_outTemp_min_range_max - at_outTemp_min_range_min, outTemp_round )
        # Replace the SQL Query output with the converted values
        at_outTemp_range_min = [ at_outTemp_min_range_query[0], at_outTemp_min_range_total, at_outTemp_min_range_min, at_outTemp_min_range_max ]
        
        
        # Rain lookups
        # Find the group_name for rain
        rain_unit = converter.group_unit_dict["group_rain"]
        
        # Find the number of decimals to round to
        rain_round = int(self.generator.skin_dict['Units']['StringFormats'].get("group_rain", "2f")[-2])
        
        # Rainiest Day
        rainiest_day_query = wx_manager.getSql( 'SELECT dateTime, ROUND( sum, 2 ) FROM archive_day_rain WHERE dateTime >= %s ORDER BY sum DESC LIMIT 1;' % year_start_epoch )
        if rainiest_day_query is not None:
            rainiest_day_tuple = (rainiest_day_query[1], rain_unit, 'group_rain')
            rainiest_day_converted = round( self.generator.converter.convert(rainiest_day_tuple)[0], rain_round )
            rainiest_day = [ rainiest_day_query[0], rainiest_day_converted ]
        else:
            rainiest_day = [ calendar.timegm( time.gmtime() ), 0.0 ]
            

        # All Time Rainiest Day
        at_rainiest_day_query = wx_manager.getSql( 'SELECT dateTime, sum FROM archive_day_rain ORDER BY sum DESC LIMIT 1' )
        at_rainiest_day_tuple = (at_rainiest_day_query[1], rain_unit, 'group_rain')
        at_rainiest_day_converted = round( self.generator.converter.convert(at_rainiest_day_tuple)[0], rain_round )
        at_rainiest_day = [ time.strftime( "%B %d, %Y at %-I:%M %p", time.localtime( at_rainiest_day_query[0] ) ), at_rainiest_day_converted ]
        

        # Find what kind of database we're working with and specify the correctly tailored SQL Query for each type of database
        dbtype = self.generator.config_dict['DataBindings']['wx_binding']['database']
        if dbtype == "archive_sqlite":
            year_rainiest_month_sql = 'SELECT strftime("%%m", datetime(dateTime, "unixepoch")) as month, ROUND( SUM( sum ), 2 ) as total FROM archive_day_rain WHERE strftime("%%Y", datetime(dateTime, "unixepoch")) = "%s" GROUP BY month ORDER BY total DESC LIMIT 1;' % time.strftime( "%Y", time.localtime( time.time() ) )
            at_rainiest_month_sql = 'SELECT strftime("%m", datetime(dateTime, "unixepoch")) as month, strftime("%Y", datetime(dateTime, "unixepoch")) as year, ROUND( SUM( sum ), 2 ) as total FROM archive_day_rain GROUP BY month, year ORDER BY total DESC LIMIT 1;'
            year_rain_data_sql = 'SELECT dateTime, ROUND( sum, 2 ) FROM archive_day_rain WHERE strftime("%%Y", datetime(dateTime, "unixepoch")) = "%s";' % time.strftime( "%Y", time.localtime( time.time() ) )
            at_rain_data_sql = 'SELECT dateTime, ROUND( sum, 2 ) FROM archive_day_rain;'
            # The all stats from http://www.weewx.com/docs/customizing.htm doesn't seem to calculate "Total Rainfall for" all time stat correctly. 
            at_rain_highest_year_sql = 'SELECT strftime("%Y", datetime(dateTime, "unixepoch")) as year, ROUND( SUM( sum ), 2 ) as total FROM archive_day_rain GROUP BY year ORDER BY total DESC LIMIT 1;'
        elif dbtype == "archive_mysql":
            year_rainiest_month_sql = 'SELECT FROM_UNIXTIME( dateTime, "%%m" ) AS month, ROUND( SUM( sum ), 2 ) AS total FROM archive_day_rain WHERE year( FROM_UNIXTIME( dateTime ) ) = "{0}" GROUP BY month ORDER BY total DESC LIMIT 1;'.format( time.strftime( "%Y", time.localtime( time.time() ) ) ) # Why does this one require .format() but the other's don't?
            at_rainiest_month_sql = 'SELECT FROM_UNIXTIME( dateTime, "%%m" ) AS month, FROM_UNIXTIME( dateTime, "%%Y" ) AS year, ROUND( SUM( sum ), 2 ) AS total FROM archive_day_rain GROUP BY month, year ORDER BY total DESC LIMIT 1;'
            year_rain_data_sql = 'SELECT dateTime, ROUND( sum, 2 ) FROM archive_day_rain WHERE year( FROM_UNIXTIME( dateTime ) ) = "%s";' % time.strftime( "%Y", time.localtime( time.time() ) )
            at_rain_data_sql = 'SELECT dateTime, ROUND( sum, 2 ) FROM archive_day_rain;'
            # The all stats from http://www.weewx.com/docs/customizing.htm doesn't seem to calculate "Total Rainfall for" all time stat correctly. 
            at_rain_highest_year_sql = 'SELECT FROM_UNIXTIME( dateTime, "%%Y" ) AS year, ROUND( SUM( sum ), 2 ) AS total FROM archive_day_rain GROUP BY year ORDER BY total DESC LIMIT 1;'
            
        # Rainiest month
        year_rainiest_month_query = wx_manager.getSql( year_rainiest_month_sql )
        if year_rainiest_month_query is not None:
            year_rainiest_month_tuple = (year_rainiest_month_query[1], rain_unit, 'group_rain')
            year_rainiest_month_converted = round( self.generator.converter.convert(year_rainiest_month_tuple)[0], rain_round )
            year_rainiest_month = [ calendar.month_name[ int( year_rainiest_month_query[0] ) ], year_rainiest_month_converted ]
        else:
            year_rainiest_month = [ "N/A", 0.0 ]

        # All time rainiest month
        at_rainiest_month_query = wx_manager.getSql( at_rainiest_month_sql )
        at_rainiest_month_tuple = (at_rainiest_month_query[2], rain_unit, 'group_rain')
        at_rainiest_month_converted = round( self.generator.converter.convert(at_rainiest_month_tuple)[0], rain_round )
        at_rainiest_month = [ calendar.month_name[ int( at_rainiest_month_query[0] ) ] + ", " + at_rainiest_month_query[1], at_rainiest_month_converted ]
        
        # All time rainiest year
        at_rain_highest_year_query = wx_manager.getSql( at_rain_highest_year_sql )
        at_rain_highest_year_tuple = (at_rain_highest_year_query[1], rain_unit, 'group_rain')
        at_rain_highest_year_converted = round( self.generator.converter.convert(at_rain_highest_year_tuple)[0], rain_round )
        at_rain_highest_year = [ at_rain_highest_year_query[0], at_rain_highest_year_converted ]
        
        
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
        at_rain_query = wx_manager.genSql( at_rain_data_sql )
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
        forecast_alert_text = ""
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
            
            # Weather Alerts (only if enabled)
            if forecast_alert_enabled == 1:
                if "alerts" in data:
                    for alert in data['alerts']:
                        alert_expires = time.strftime('%B %d, %Y %-I:%M %p', time.localtime( alert['expires'] )) # December 27, 2018, 9:00 PM
                        # Final alert string
                        forecast_alert_text += "<i class='fa fa-exclamation-triangle'></i> <a href='%s' target='_blank'>%s in effect until %s</a><br>" % ( alert['uri'], alert['title'], alert_expires )
            
            forecast_html_output = ""
            forecast_updated = time.strftime( "%B %d, %Y, %-I:%M %p %Z", time.localtime( data["currently"]["time"] ) )
            current_obs_summary = data["currently"]["summary"]
            visibility = data["currently"]["visibility"]
            
            # Get the unit label from the skin dict for speed. 
            windSpeedUnit = self.generator.skin_dict["Units"]["Groups"]["group_speed"]
            windSpeedUnitLabel = self.generator.skin_dict["Units"]["Labels"][windSpeedUnit]

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
                
            # Loop through each day and generate the forecast row HTML
            for daily_data in data["daily"]["data"]:
                # Setup some variables
                if daily_data["icon"] == "partly-cloudy-night":
                    image_url = belchertown_root_url + "/images/clear-day.png"
                else:
                    image_url = belchertown_root_url + "/images/" + daily_data["icon"] + ".png"
                
                condition_text = ""
                if daily_data["icon"] == "clear-day":
                    condition_text = "Clear"
                elif daily_data["icon"] == "clear-night":
                    condition_text = "Clear"
                elif daily_data["icon"] == "rain":
                    condition_text = "Rain"
                elif daily_data["icon"] == "snow":
                    condition_text = "Snow"
                elif daily_data["icon"] == "sleet":
                    condition_text = "Sleet"
                elif daily_data["icon"] == "wind":
                    condition_text = "Windy"
                elif daily_data["icon"] == "fog":
                    condition_text = "Fog"
                elif daily_data["icon"] == "cloudy":
                    condition_text = "Overcast"
                elif daily_data["icon"] == "partly-cloudy-day":
                    condition_text = "Partly Cloudy"
                elif daily_data["icon"] == "partly-cloudy-night":
                    # https://darksky.net/dev/docs/faq - So you can just treat partly-cloudy-night as an alias for clear-day.
                    condition_text = "Clear"
                elif daily_data["icon"] == "hail":
                    condition_text = "Hail"
                elif daily_data["icon"] == "thunderstorm":
                    condition_text = "Thunderstorm"
                elif daily_data["icon"] == "tornado":
                    condition_text = "Tornado"
            
                # Build html
                if time.strftime( "%a %m/%d", time.localtime( daily_data["time"] ) ) == time.strftime( "%a %m/%d", time.localtime( time.time() ) ):
                    # If the time in the darksky output is today, do not add border-left and say "Today" in the header
                    output = '<div class="col-sm-1-5 wuforecast">'
                    weekday = "Today"
                else:
                    output = '<div class="col-sm-1-5 wuforecast border-left">'
                    weekday = time.strftime( "%a %-m/%d", time.localtime( daily_data["time"] ) )
                
                output += '<span id="weekday">' + weekday + '</span>'
                output += '<br>'
                output += '<div class="forecast-conditions">'
                output += '<img id="icon" src="'+image_url+'">'
                output += '<span class="forecast-condition-text">'
                output += condition_text
                output += '</span>'
                output += '</div>'
                output += '<span class="forecast-high">'+str( int( daily_data["temperatureHigh"] ) )+'&deg;</span> | <span class="forecast-low">'+str( int( daily_data["temperatureLow"] ) )+'&deg;</span>'
                output += '<br>'
                output += '<div class="forecast-precip">'
                if "precipType" in daily_data:
                    if daily_data["precipType"] == "snow":
                        output += '<div class="snow-precip">'
                        output += '<img src="'+belchertown_root_url+'/images/snowflake-icon-15px.png"> <span>'+ str( '%.2f' % daily_data["precipAccumulation"] ) +'<span> in'
                        output += '</div>'
                    elif daily_data["precipType"] == "rain":
                        output += '<i class="wi wi-raindrop wi-rotate-45 rain-precip"></i> <span >'+str( int( daily_data["precipProbability"] * 100 ) )+'%</span>'
                else:
                    output += '<i class="wi wi-raindrop wi-rotate-45 rain-no-precip"></i> <span >0%</span>'
                output += '</div>'
                output += '<div class="forecast-wind">'
                output += '<i class="wi wi-strong-wind"></i> '+str( int( daily_data["windGust"] ) )+' '+ windSpeedUnitLabel
                output += '</div>'
                output += "</div> <!-- end .wuforecast -->"
                
                # Add to the output
                forecast_html_output += output
        else:
            forecast_updated = ""
            forecast_json_url = ""
            current_obs_icon = ""
            current_obs_summary = ""
            visibility = ""
            visibility_unit = ""
            forecast_html_output = ""
        
        
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
                eqtime = time.strftime( "%B %d, %Y, %-I:%M %p %Z", time.localtime( eqdata["features"][0]["properties"]["time"] / 1000 ) )
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
                  js.src = "//connect.facebook.net/en_US/sdk.js#xfbml=1&version=v2.5&appId=217237948331360";
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
                                  'moment_js_utc_offset': moment_js_utc_offset,
                                  'radar_html': radar_html,
                                  'about_page_text': about_page_text,
                                  'records_page_text': records_page_text,
                                  'index_hook_after_station_info_enabled': index_hook_after_station_info_enabled,
                                  'index_hook_after_station_info_text': index_hook_after_station_info_text,
                                  'index_hook_after_forecast_enabled': index_hook_after_forecast_enabled,
                                  'index_hook_after_forecast_text': index_hook_after_forecast_text,
                                  'index_hook_after_snapshot_enabled': index_hook_after_snapshot_enabled,
                                  'index_hook_after_snapshot_text': index_hook_after_snapshot_text,
                                  'index_hook_after_charts_enabled': index_hook_after_charts_enabled,
                                  'index_hook_after_charts_text': index_hook_after_charts_text,
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
                                  'forecast_updated': forecast_updated,
                                  'forecast_json_url': forecast_json_url,
                                  'current_obs_icon': current_obs_icon,
                                  'current_obs_summary': current_obs_summary,
                                  'visibility': visibility,
                                  'visibility_unit': visibility_unit,
                                  'forecast_alert_text': forecast_alert_text,
                                  'forecastHTML' : forecast_html_output,
                                  'earthquake_time': eqtime,
                                  'earthquake_url': equrl,
                                  'earthquake_place': eqplace,
                                  'earthquake_magnitude': eqmag,
                                  'earthquake_lat': eqlat,
                                  'earthquake_lon': eqlon,
                                  'social_html': social_html }

        # Finally, return our extension as a list:
        return [search_list_extension]
