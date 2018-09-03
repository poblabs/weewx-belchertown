#
#    Copyright (c) 2016 Gary Roderick
#    https://github.com/gjr80/weewx-highcharts
#
#    See the file LICENSE at the URL above for your full rights.
#
#    Author: Gary Roderick 
#    Modified by: Pat O'Brien
#    Revised for the BelchertownWeather.com weewx skin
#

import calendar
import datetime
import time
import weewx
import syslog
import json

from weewx.cheetahgenerator import SearchList
from weeutil.weeutil import TimeSpan, startOfInterval, intervalgen, to_int, archiveDaySpan, archiveWeekSpan, archiveMonthSpan, archiveYearSpan
from weewx.units import ValueTuple
from datetime import date

def logmsg(level, msg):
    syslog.syslog(level, 'highchartsSearchX: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)

def roundNone(value, places):
    """round value to 'places' places but also permit a value of None"""
    if value is not None:
        try:
            value = round(value, places)
        except Exception, e:
            value = None
    return value


class highchartsDay(SearchList):

    def __init__(self, generator):
        SearchList.__init__(self, generator)

    def get_extension_list(self, timespan, db_lookup):
    
        # First make sure the user wants to use the extension. If not, return right away.
        if self.generator.skin_dict['Extras']['highcharts_enabled'] == "0":
            # Return an empty SLE
            search_list_extension = { }
            return [search_list_extension]
       
        # Get our start time
        _start_ts, _end_ts = archiveDaySpan( int( time.time() ) )
        
        stop_struct = time.localtime(_end_ts)
        utc_offset = (calendar.timegm(stop_struct) - calendar.timegm(time.gmtime(time.mktime(stop_struct))))/60
        
        # Get our temperature vector
        (time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'outTemp')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outTemp_vt[2], "1f")[-2])
        outTempRound_vt =  [roundNone(x, usageRound) for x in outTemp_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        outTemp_json = json.dumps(zip(time_ms, outTempRound_vt))
        
        # Get our dewpoint vector
        (time_start_vt, time_stop_vt, dewpoint_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'dewpoint')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(dewpoint_vt[2], "1f")[-2])
        dewpointRound_vt =  [roundNone(x, usageRound) for x in dewpoint_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        dewpoint_json = json.dumps(zip(time_ms, dewpointRound_vt))
                
        # Get our wind chill vector
        (time_start_vt, time_stop_vt, windchill_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windchill')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windchill_vt[2], "1f")[-2])
        windchillRound_vt =  [roundNone(x, usageRound) for x in windchill_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        windchill_json = json.dumps(zip(time_ms, windchillRound_vt))
        
        # Get our heat index vector
        (time_start_vt, time_stop_vt, heatindex_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'heatindex')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(heatindex_vt[2], "1f")[-2])
        heatindexRound_vt =  [roundNone(x, usageRound) for x in heatindex_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        heatindex_json = json.dumps(zip(time_ms, heatindexRound_vt))
        
        # Get our humidity vector
        (time_start_vt, time_stop_vt, outHumidity_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'outHumidity')
        outHumidity_json = json.dumps(zip(time_ms, outHumidity_vt[0]))
        
        # Get our barometer vector
        (time_start_vt, time_stop_vt, barometer_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'barometer')
        barometer_vt = self.generator.converter.convert(barometer_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        barometerRound = int(self.generator.skin_dict['Units']['StringFormats'].get(barometer_vt[1], "1f")[-2])
        # Do the rounding
        barometerRound_vt = [round(x,barometerRound) if x is not None else None for x in barometer_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        barometer_json = json.dumps(zip(time_ms, barometerRound_vt))

        # Get our wind speed vector
        (time_start_vt, time_stop_vt, windSpeed_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windSpeed')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windSpeed_vt[2], "1f")[-2])
        windSpeedRound_vt =  [roundNone(x, usageRound) for x in windSpeed_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        windSpeed_json = json.dumps(zip(time_ms, windSpeedRound_vt))
        
        # Get our wind gust vector
        (time_start_vt, time_stop_vt, windGust_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windGust')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windGust_vt[2], "1f")[-2])
        windGustRound_vt =  [roundNone(x, usageRound) for x in windGust_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        windGust_json = json.dumps(zip(time_ms, windGustRound_vt))
        
        # Get our wind direction vector
        (time_start_vt, time_stop_vt, windDir_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windDir')
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        windDir_json = json.dumps(zip(time_ms, windDir_vt[0]))
        
        #POB rain vector 2.0
        _pob_rain_lookup = db_lookup().genSql("SELECT dateTime, rain FROM archive WHERE rain IS NOT NULL and dateTime>=%s AND dateTime<=%s" % (_start_ts, _end_ts) )
        rain_time_ms = []
        rain_round = []
        for rainsql in _pob_rain_lookup:
            rain_time_ms.append(float(rainsql[0]) * 1000)
            rain_round.append( round( rainsql[1], 2) )
        pob_rain_json = json.dumps(zip(rain_time_ms, rain_round))

        # Rain accumulation totals using the timespan. For static 1 day, look at POB archive above.
        _pob_rain_totals_lookup = db_lookup().genSql( "SELECT dateTime, rain FROM archive WHERE rain IS NOT NULL and dateTime>=%s AND dateTime<=%s" % (_start_ts, _end_ts) )
        rain_time_ms = []
        rain_total = []
        rain_count = 0
        for rainsql in _pob_rain_totals_lookup:
            rain_time_ms.append(float(rainsql[0]) * 1000)
            rain_count = rain_count + rainsql[1]
            #rain_total.append( round( rainsql[1], 2) )
            rain_total.append( round( rain_count, 2) )
        pob_rain_total_json = json.dumps(zip(rain_time_ms, rain_total))
        
        # Get our radiation vector
        (time_start_vt, time_stop_vt, radiation_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'radiation')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "2f")[-2])
        radiationRound_vt =  [roundNone(x, usageRound) for x in radiation_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        radiation_json = json.dumps(zip(time_ms, radiationRound_vt))
                
        # Put into a dictionary to return
        search_list_extension = {'outTempDayjson' : outTemp_json,
                                 'outHumidityDayjson' : outHumidity_json,
                                 'dewpointDayjson' : dewpoint_json,
                                 'windchillDayjson' : windchill_json,
                                 'heatindexDayjson' : heatindex_json,
                                 'barometerDayjson' : barometer_json,
                                 'rainDayjson' : pob_rain_json,
                                 'rainDayTotaljson' : pob_rain_total_json,
                                 'windSpeedDayjson' : windSpeed_json,
                                 'windGustDayjson' : windGust_json,
                                 'windDirDayjson' : windDir_json,
                                 'radiationDayjson' : radiation_json,
                                 'utcOffset': utc_offset}
        # Return our json data
        return [search_list_extension]
        
class highchartsWeek(SearchList):
    """ SearchList class to generate a required JSON vectors for Highcharts 
        week plots.
    """
    def __init__(self, generator):
        SearchList.__init__(self, generator)

    def get_extension_list(self, timespan, db_lookup):
        """ Generate the required JSON vectors and return same as a dictionary 
            in a list.
        
        Parameters:
          timespan: An instance of weeutil.weeutil.TimeSpan. This will
                    hold the start and stop times of the domain of
                    valid times.

          db_lookup: This is a function that, given a data binding
                     as its only parameter, will return a database manager
                     object.
         """

        # First make sure the user wants to use the extension. If not, return right away.
        if self.generator.skin_dict['Extras']['highcharts_enabled'] == "0":
            # Return an empty SLE
            search_list_extension = { }
            return [search_list_extension]

        t1 = time.time()

        # Get our start time. This returns "last 7 days". If you want "this week starting at 'week_start' from config", see below.
        _start_ts = startOfInterval(timespan.stop - 604800, 86400)
        _end_ts = timespan.stop
        
        # If you want "this week", uncomment this
        #week_start = to_int(self.generator.config_dict["Station"].get('week_start', 6))
        #_start_ts, _end_ts = archiveWeekSpan( int(time.time()), week_start)

        stop_struct = time.localtime(timespan.stop)
        utc_offset = (calendar.timegm(stop_struct) - calendar.timegm(time.gmtime(time.mktime(stop_struct))))/60
        
        # Get our temperature vector
        (time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'outTemp', 'max', 3600)
        
        # Convert our temperature vector
        outTemp_vt = self.generator.converter.convert(outTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        tempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outTemp_vt[2], "1f")[-2])
        # Do the rounding
        outTempRound_vt =  [roundNone(x,tempRound) for x in outTemp_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        outTemp_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our dewpoint vector
        (time_start_vt, time_stop_vt, dewpoint_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'dewpoint', 'max', 3600)

        dewpoint_vt = self.generator.converter.convert(dewpoint_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        dewpointRound = int(self.generator.skin_dict['Units']['StringFormats'].get(dewpoint_vt[2], "1f")[-2])
        # Do the rounding
        dewpointRound_vt =  [roundNone(x,dewpointRound) for x in dewpoint_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        dewpoint_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
       
        # Get our wind chill vector
        (time_start_vt, time_stop_vt, windchill_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windchill', 'max', 3600)
        windchill_vt = self.generator.converter.convert(windchill_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windchillRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windchill_vt[2], "1f")[-2])
        # Do the rounding
        windchillRound_vt =  [roundNone(x,windchillRound) for x in windchill_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windchill_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our heat index vector
        (time_start_vt, time_stop_vt, heatindex_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'heatindex', 'max', 3600)
        heatindex_vt = self.generator.converter.convert(heatindex_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        heatindexRound = int(self.generator.skin_dict['Units']['StringFormats'].get(heatindex_vt[2], "1f")[-2])
        # Do the rounding
        heatindexRound_vt =  [roundNone(x,heatindexRound) for x in heatindex_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        heatindex_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our humidity vector
        (time_start_vt, time_stop_vt, outHumidity_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'outHumidity', 'max', 3600)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        outHumidityRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outHumidity_vt[2], "1f")[-2])
        # Do the rounding
        outHumidityRound_vt =  [roundNone(x,outHumidityRound) for x in outHumidity_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        outHumidity_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our barometer vector
        (time_start_vt, time_stop_vt, barometer_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'barometer', 'max', 3600)
        barometer_vt = self.generator.converter.convert(barometer_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        barometerRound = int(self.generator.skin_dict['Units']['StringFormats'].get(barometer_vt[1], "1f")[-2])
        # Do the rounding
        barometerRound_vt =  [roundNone(x,barometerRound) for x in barometer_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        barometer_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our wind speed vector
        (time_start_vt, time_stop_vt, windSpeed_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windSpeed', 'max', 3600)
       
        windSpeed_vt = self.generator.converter.convert(windSpeed_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windspeedRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windSpeed_vt[2], "1f")[-2])
        # Do the rounding
        windSpeedRound_vt =  [roundNone(x,windspeedRound) for x in windSpeed_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windSpeed_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our wind gust vector
        (time_start_vt, time_stop_vt, windGust_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windGust', 'max', 3600)
        windGust_vt = self.generator.converter.convert(windGust_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windgustRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windGust_vt[2], "1f")[-2])
        # Do the rounding
        windGustRound_vt =  [roundNone(x,windgustRound) for x in windGust_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windGust_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our wind direction vector
        (time_start_vt, time_stop_vt, windDir_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windDir', 'max', 3600)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windDirRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windDir_vt[2], "1f")[-2])
        # Do the rounding
        windDirRound_vt =  [roundNone(x,windDirRound) for x in windDir_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windDir_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
                
        #POB rain vector 2.0
        _pob_rain_lookup = db_lookup().genSql("SELECT dateTime, rain FROM archive WHERE rain IS NOT NULL and dateTime>=%s AND dateTime<=%s" % (_start_ts, _end_ts) )
        rain_time_ms = []
        rain_round = []
        for rainsql in _pob_rain_lookup:
            rain_time_ms.append(float(rainsql[0]) * 1000)
            rain_round.append( round( rainsql[1], 2) )
        pob_rain_json = json.dumps(zip(rain_time_ms, rain_round))
        
        # Rain accumulation totals using the timespan. For static 1 day, look at POB archive above.
        _pob_rain_totals_lookup = db_lookup().genSql( "SELECT dateTime, rain FROM archive WHERE rain IS NOT NULL and dateTime>=%s AND dateTime<=%s" % (_start_ts, _end_ts) )
        rain_time_ms = []
        rain_total = []
        rain_count = 0
        for rainsql in _pob_rain_totals_lookup:
            rain_time_ms.append(float(rainsql[0]) * 1000)
            rain_count = rain_count + rainsql[1]
            rain_total.append( round( rain_count, 2) )
            #rain_total.append( round(rainsql[1], 2) ) # Need to automate this from skin_dict?
        #Now that the dicts are built, do some rounding
        #rainRound_vt =  [roundNone(x,2) for x in rain_total]
        #pob_rain_total_json = json.dumps(zip(rain_time_ms, rainRound_vt))
        pob_rain_total_json = json.dumps(zip(rain_time_ms, rain_total))
        
        # Get our radiation vector
        (time_start_vt, time_stop_vt, radiation_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'radiation', 'max', 3600)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        radiationRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "1f")[-2])
        # Do the rounding
        radiationRound_vt =  [roundNone(x,radiationRound) for x in radiation_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        radiation_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
                
        # Format our vectors in json format. Need the zip() to get time/value pairs
        # Assumes all vectors have the same number of elements
        outTemp_json = json.dumps(zip(outTemp_time_ms, outTempRound_vt))
        dewpoint_json = json.dumps(zip(dewpoint_time_ms, dewpointRound_vt))
        windchill_json = json.dumps(zip(windchill_time_ms, windchillRound_vt))
        heatindex_json = json.dumps(zip(heatindex_time_ms, heatindexRound_vt))
        outHumidity_json = json.dumps(zip(outHumidity_time_ms, outHumidityRound_vt))
        barometer_json = json.dumps(zip(barometer_time_ms, barometerRound_vt))
        windSpeed_json = json.dumps(zip(windSpeed_time_ms, windSpeedRound_vt))
        windGust_json = json.dumps(zip(windGust_time_ms, windGustRound_vt))
        windDir_json = json.dumps(zip(windDir_time_ms, windDirRound_vt))
        radiation_json = json.dumps(zip(radiation_time_ms, radiationRound_vt))
        
        # Put into a dictionary to return
        search_list_extension = {'outTempWeekjson' : outTemp_json,
                                 'dewpointWeekjson' : dewpoint_json,
                                 'windchillWeekjson' : windchill_json,
                                 'heatindexWeekjson' : heatindex_json,
                                 'outHumidityWeekjson' : outHumidity_json,
                                 'barometerWeekjson' : barometer_json,
                                 'windSpeedWeekjson' : windSpeed_json,
                                 'windGustWeekjson' : windGust_json,
                                 'windDirWeekjson' : windDir_json,
                                 'rainWeekjson' : pob_rain_json,
                                 'rainWeekTotaljson' : pob_rain_total_json,
                                 'radiationWeekjson' : radiation_json,
                                 'utcOffset': utc_offset,
                                 'weekPlotStart' : _start_ts * 1000,
                                 'weekPlotEnd' : _end_ts * 1000}
        
        # Return our json data
        return [search_list_extension]
        
        
class highchartsMonth(SearchList):
    """ SearchList class to generate a required JSON vectors for Highcharts 
        week plots.
    """
    def __init__(self, generator):
        SearchList.__init__(self, generator)

    def get_extension_list(self, timespan, db_lookup):
        """ Generate the required JSON vectors and return same as a dictionary 
            in a list.
        
        Parameters:
          timespan: An instance of weeutil.weeutil.TimeSpan. This will
                    hold the start and stop times of the domain of
                    valid times.

          db_lookup: This is a function that, given a data binding
                     as its only parameter, will return a database manager
                     object.
         """
        
        # First make sure the user wants to use the extension. If not, return right away.
        if self.generator.skin_dict['Extras']['highcharts_enabled'] == "0":
            # Return an empty SLE
            search_list_extension = { }
            return [search_list_extension]
         
        t1 = time.time()
        
        # Get our start time. This is "last 30 days". If you want "this month from day 1, see below"
        # POB: 2592000 = seconds in a month
        # 86400 = seconds in 24 hours
        _start_ts = startOfInterval(timespan.stop - 2592000, 86400)
        _end_ts = timespan.stop

        # Start at day 1 of the current month. 
        #_start_ts, _end_ts = archiveMonthSpan( int( time.time() ) )
        
        stop_struct = time.localtime(timespan.stop)
        utc_offset = (calendar.timegm(stop_struct) - calendar.timegm(time.gmtime(time.mktime(stop_struct))))/60
        
        # Get our temperature vector
        (time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'outTemp', 'max', 86400)

        # Convert our temperature vector
        outTemp_vt = self.generator.converter.convert(outTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        tempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outTemp_vt[2], "1f")[-2])
        # Do the rounding
        outTempRound_vt =  [roundNone(x,tempRound) for x in outTemp_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        outTemp_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
       
        # Min temp vector
        (time_start_vt, time_stop_vt, outTemp_min_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'outTemp', 'min', 86400)

        # Convert our temperature vector
        outTemp_min_vt = self.generator.converter.convert(outTemp_min_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        tempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outTemp_min_vt[2], "1f")[-2])
        # Do the rounding
        outTempMinRound_vt =  [roundNone(x,tempRound) for x in outTemp_min_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        outTempMin_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        
        # Get our dewpoint vector
        (time_start_vt, time_stop_vt, dewpoint_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'dewpoint', 'max', 86400)

        dewpoint_vt = self.generator.converter.convert(dewpoint_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        dewpointRound = int(self.generator.skin_dict['Units']['StringFormats'].get(dewpoint_vt[2], "1f")[-2])
        # Do the rounding
        dewpointRound_vt =  [roundNone(x,dewpointRound) for x in dewpoint_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        dewpoint_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
                
        # Get our wind chill vector
        (time_start_vt, time_stop_vt, windchill_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windchill', 'max', 86400)
        windchill_vt = self.generator.converter.convert(windchill_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windchillRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windchill_vt[2], "1f")[-2])
        # Do the rounding
        windchillRound_vt =  [roundNone(x,windchillRound) for x in windchill_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windchill_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our heat index vector
        (time_start_vt, time_stop_vt, heatindex_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'heatindex', 'max', 86400)
        heatindex_vt = self.generator.converter.convert(heatindex_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        heatindexRound = int(self.generator.skin_dict['Units']['StringFormats'].get(heatindex_vt[2], "1f")[-2])
        # Do the rounding
        heatindexRound_vt =  [roundNone(x,heatindexRound) for x in heatindex_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        heatindex_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our humidity vector
        (time_start_vt, time_stop_vt, outHumidity_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'outHumidity', 'max', 86400)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        outHumidityRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outHumidity_vt[2], "1f")[-2])
        # Do the rounding
        outHumidityRound_vt =  [roundNone(x,outHumidityRound) for x in outHumidity_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        outHumidity_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our barometer vector
        (time_start_vt, time_stop_vt, barometer_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'barometer', 'max', 86400)
        barometer_vt = self.generator.converter.convert(barometer_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        barometerRound = int(self.generator.skin_dict['Units']['StringFormats'].get(barometer_vt[2], "1f")[-2])
        # Do the rounding
        barometerRound_vt =  [roundNone(x,barometerRound) for x in barometer_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        barometer_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our wind speed vector
        (time_start_vt, time_stop_vt, windSpeed_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windSpeed', 'max', 86400)
        windSpeed_vt = self.generator.converter.convert(windSpeed_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windspeedRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windSpeed_vt[2], "1f")[-2])
        # Do the rounding
        windSpeedRound_vt =  [roundNone(x,windspeedRound) for x in windSpeed_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windSpeed_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Average Wind Speed
        (time_start_vt, time_stop_vt, windSpeedAvg_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windSpeed', 'avg', 86400)
        windSpeedAvg_vt = self.generator.converter.convert(windSpeedAvg_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windspeedAvgRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windSpeedAvg_vt[2], "1f")[-2])
        # Do the rounding
        windSpeedAvgRound_vt =  [roundNone(x,windspeedAvgRound) for x in windSpeedAvg_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windSpeedAvg_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our wind gust vector
        (time_start_vt, time_stop_vt, windGust_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windGust', 'max', 86400)
        windGust_vt = self.generator.converter.convert(windGust_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windgustRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windGust_vt[2], "1f")[-2])
        # Do the rounding
        windGustRound_vt =  [roundNone(x,windgustRound) for x in windGust_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windGust_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our wind direction vector
        (time_start_vt, time_stop_vt, windDir_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windDir', 'avg', 86400)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windDirRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windDir_vt[2], "1f")[-2])
        # Do the rounding
        windDirRound_vt =  [roundNone(x,windDirRound) for x in windDir_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windDir_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
                
        #POB rain vector 2.0
        _pob_rain_lookup = db_lookup().genSql("SELECT dateTime, rain FROM archive WHERE rain IS NOT NULL and dateTime>=%s AND dateTime<=%s" % (_start_ts, _end_ts) )
        rain_time_ms = []
        rain_round = []
        for rainsql in _pob_rain_lookup:
            rain_time_ms.append(float(rainsql[0]) * 1000)
            rain_round.append( round( rainsql[1], 2) )
        pob_rain_json = json.dumps(zip(rain_time_ms, rain_round))
        
        # Rain accumulation totals using the timespan. For static 1 day, look at POB archive above.
        _pob_rain_totals_lookup = db_lookup().genSql( "SELECT dateTime, rain FROM archive WHERE rain IS NOT NULL and dateTime>=%s AND dateTime<=%s" % (_start_ts, _end_ts) )
        rain_time_ms = []
        rain_total = []
        rain_count = 0
        for rainsql in _pob_rain_totals_lookup:
            rain_time_ms.append(float(rainsql[0]) * 1000)
            rain_count = rain_count + rainsql[1]
            rain_total.append( round( rain_count, 2) )
            #rain_total.append( rainsql[1] )
            #rain_total.append( round(rainsql[1], 2) ) # Need to automate this from skin_dict?
        #Now that the dicts are built, do some rounding
        #rainRound_vt =  [roundNone(x,2) for x in rain_total]
        #pob_rain_total_json = json.dumps(zip(rain_time_ms, rainRound_vt))
        pob_rain_total_json = json.dumps(zip(rain_time_ms, rain_total))
        
        # Get our radiation vector
        (time_start_vt, time_stop_vt, radiation_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'radiation', 'max', 86400)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        radiationRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "1f")[-2])
        # Do the rounding
        radiationRound_vt =  [roundNone(x,radiationRound) for x in radiation_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        radiation_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
                
        # Format our vectors in json format. Need the zip() to get time/value pairs
        # Assumes all vectors have the same number of elements
        outTemp_json = json.dumps(zip(outTemp_time_ms, outTempRound_vt))
        outTemp_min_json = json.dumps(zip(outTempMin_time_ms, outTempMinRound_vt))
        dewpoint_json = json.dumps(zip(dewpoint_time_ms, dewpointRound_vt))
        windchill_json = json.dumps(zip(windchill_time_ms, windchillRound_vt))
        heatindex_json = json.dumps(zip(heatindex_time_ms, heatindexRound_vt))
        outHumidity_json = json.dumps(zip(outHumidity_time_ms, outHumidityRound_vt))
        barometer_json = json.dumps(zip(barometer_time_ms, barometerRound_vt))
        windSpeed_json = json.dumps(zip(windSpeed_time_ms, windSpeedRound_vt))
        windSpeedAvg_json = json.dumps(zip(windSpeedAvg_time_ms, windSpeedAvgRound_vt))
        windGust_json = json.dumps(zip(windGust_time_ms, windGustRound_vt))
        windDir_json = json.dumps(zip(windDir_time_ms, windDirRound_vt))
        radiation_json = json.dumps(zip(radiation_time_ms, radiationRound_vt))
        
        # Put into a dictionary to return
        search_list_extension = {'outTempMonthjson' : outTemp_json,
                                 'outTempMinMonthjson' : outTemp_min_json,
                                 'dewpointMonthjson' : dewpoint_json,
                                 'windchillMonthjson' : windchill_json,
                                 'heatindexMonthjson' : heatindex_json,
                                 'outHumidityMonthjson' : outHumidity_json,
                                 'barometerMonthjson' : barometer_json,
                                 'windSpeedMonthjson' : windSpeed_json,
                                 'windSpeedAvgMonthjson' : windSpeedAvg_json,
                                 'windGustMonthjson' : windGust_json,
                                 'windDirMonthjson' : windDir_json,
                                 'rainMonthjson' : pob_rain_json,
                                 'rainMonthTotaljson' : pob_rain_total_json,
                                 'radiationMonthjson' : radiation_json,
                                 'utcOffset': utc_offset,
                                 'MonthPlotStart' : _start_ts * 1000,
                                 'MonthPlotEnd' : _end_ts * 1000}
        
        # Return our json data
        return [search_list_extension]
        
    
class highchartsYear(SearchList):
    """ SearchList class to generate a required JSON vectors for Highcharts 
        week plots.
    """
    def __init__(self, generator):
        SearchList.__init__(self, generator)

    def get_extension_list(self, timespan, db_lookup):
        """ Generate the required JSON vectors and return same as a dictionary 
            in a list.
        
        Parameters:
          timespan: An instance of weeutil.weeutil.TimeSpan. This will
                    hold the start and stop times of the domain of
                    valid times.

          db_lookup: This is a function that, given a data binding
                     as its only parameter, will return a database manager
                     object.
         """

        # First make sure the user wants to use the extension. If not, return right away.
        if self.generator.skin_dict['Extras']['highcharts_enabled'] == "0":
            # Return an empty SLE
            search_list_extension = { }
            return [search_list_extension]

        t1 = time.time()
        
        # Start at day 1 of current year
        _start_ts, _end_ts = archiveYearSpan( int( time.time() ) )
        
        stop_struct = time.localtime(timespan.stop)
        utc_offset = (calendar.timegm(stop_struct) - calendar.timegm(time.gmtime(time.mktime(stop_struct))))/60
        
        # Get our temperature vector
        (time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'outTemp', 'max', 86400)
        # Convert our temperature vector
        outTemp_vt = self.generator.converter.convert(outTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        tempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outTemp_vt[2], "1f")[-2])
        # Do the rounding
        outTempRound_vt =  [roundNone(x,tempRound) for x in outTemp_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        outTemp_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Min temp vector
        (time_start_vt, time_stop_vt, outTempMin_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'outTemp', 'min', 86400)
        # Convert our temperature vector
        outTempMin_vt = self.generator.converter.convert(outTempMin_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        tempMinRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outTempMin_vt[2], "1f")[-2])
        # Do the rounding
        outTempMinRound_vt =  [roundNone(x,tempMinRound) for x in outTempMin_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        outTempMin_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our dewpoint vector
        (time_start_vt, time_stop_vt, dewpoint_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'dewpoint', 'max', 86400)
        dewpoint_vt = self.generator.converter.convert(dewpoint_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        dewpointRound = int(self.generator.skin_dict['Units']['StringFormats'].get(dewpoint_vt[2], "1f")[-2])
        # Do the rounding
        dewpointRound_vt =  [roundNone(x,dewpointRound) for x in dewpoint_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        dewpoint_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
                
        # Get our wind chill vector
        (time_start_vt, time_stop_vt, windchill_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windchill', 'max', 86400)
        windchill_vt = self.generator.converter.convert(windchill_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windchillRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windchill_vt[2], "1f")[-2])
        # Do the rounding
        windchillRound_vt =  [roundNone(x,windchillRound) for x in windchill_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windchill_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our heat index vector
        (time_start_vt, time_stop_vt, heatindex_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'heatindex', 'max', 86400)
        heatindex_vt = self.generator.converter.convert(heatindex_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        heatindexRound = int(self.generator.skin_dict['Units']['StringFormats'].get(heatindex_vt[2], "1f")[-2])
        # Do the rounding
        heatindexRound_vt =  [roundNone(x,heatindexRound) for x in heatindex_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        heatindex_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our humidity vector
        (time_start_vt, time_stop_vt, outHumidity_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'outHumidity', 'max', 86400)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        outHumidityRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outHumidity_vt[2], "1f")[-2])
        # Do the rounding
        outHumidityRound_vt =  [roundNone(x,outHumidityRound) for x in outHumidity_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        outHumidity_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our barometer vector
        (time_start_vt, time_stop_vt, barometer_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'barometer', 'max', 86400)
        barometer_vt = self.generator.converter.convert(barometer_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        barometerRound = int(self.generator.skin_dict['Units']['StringFormats'].get(barometer_vt[2], "1f")[-2])
        # Do the rounding
        barometerRound_vt =  [roundNone(x,barometerRound) for x in barometer_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        barometer_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our wind speed vector
        (time_start_vt, time_stop_vt, windSpeed_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windSpeed', 'max', 86400)
        windSpeed_vt = self.generator.converter.convert(windSpeed_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windspeedRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windSpeed_vt[2], "1f")[-2])
        # Do the rounding
        windSpeedRound_vt =  [roundNone(x,windspeedRound) for x in windSpeed_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windSpeed_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Average wind speed vector
        (time_start_vt, time_stop_vt, windSpeedAvg_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windSpeed', 'avg', 86400)
        windSpeedAvg_vt = self.generator.converter.convert(windSpeedAvg_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windspeedAvgRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windSpeedAvg_vt[2], "1f")[-2])
        # Do the rounding
        windSpeedAvgRound_vt =  [roundNone(x,windspeedAvgRound) for x in windSpeedAvg_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windSpeedAvg_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our wind gust vector
        (time_start_vt, time_stop_vt, windGust_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windGust', 'max', 86400)
        windGust_vt = self.generator.converter.convert(windGust_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windgustRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windGust_vt[2], "1f")[-2])
        # Do the rounding
        windGustRound_vt =  [roundNone(x,windgustRound) for x in windGust_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windGust_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our wind direction vector
        (time_start_vt, time_stop_vt, windDir_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'windDir', 'max', 86400)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windDirRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windDir_vt[2], "1f")[-2])
        # Do the rounding
        windDirRound_vt =  [roundNone(x,windDirRound) for x in windDir_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windDir_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
                
        #POB rain vector 2.0
        _pob_rain_lookup = db_lookup().genSql("SELECT dateTime, rain FROM archive WHERE dateTime>=%s AND dateTime<=%s" % (_start_ts, _end_ts) )
        rain_time_ms = []
        rain_round = []
        for rainsql in _pob_rain_lookup:
            rain_time_ms.append(float(rainsql[0]) * 1000)
            rain_round.append( rainsql[1] )
        pob_rain_json = json.dumps(zip(rain_time_ms, rain_round))
                
        # Get our radiation vector
        (time_start_vt, time_stop_vt, radiation_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, _end_ts), 'radiation', 'max', 86400)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        radiationRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "1f")[-2])
        # Do the rounding
        radiationRound_vt =  [roundNone(x,radiationRound) for x in radiation_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        radiation_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
                
        # Format our vectors in json format. Need the zip() to get time/value pairs
        # Assumes all vectors have the same number of elements
        outTemp_json = json.dumps(zip(outTemp_time_ms, outTempRound_vt))
        outTempMin_json = json.dumps(zip(outTempMin_time_ms, outTempMinRound_vt))
        dewpoint_json = json.dumps(zip(dewpoint_time_ms, dewpointRound_vt))
        windchill_json = json.dumps(zip(windchill_time_ms, windchillRound_vt))
        heatindex_json = json.dumps(zip(heatindex_time_ms, heatindexRound_vt))
        outHumidity_json = json.dumps(zip(outHumidity_time_ms, outHumidityRound_vt))
        barometer_json = json.dumps(zip(barometer_time_ms, barometerRound_vt))
        windSpeed_json = json.dumps(zip(windSpeed_time_ms, windSpeedRound_vt))
        windSpeedAvg_json = json.dumps(zip(windSpeed_time_ms, windSpeedAvgRound_vt))
        windGust_json = json.dumps(zip(windGust_time_ms, windGustRound_vt))
        windDir_json = json.dumps(zip(windDir_time_ms, windDirRound_vt))
        radiation_json = json.dumps(zip(radiation_time_ms, radiationRound_vt))
        
        # Put into a dictionary to return
        search_list_extension = {'outTempYearjson' : outTemp_json,
                                 'outTempMinYearjson' : outTempMin_json,
                                 'dewpointYearjson' : dewpoint_json,
                                 'windchillYearjson' : windchill_json,
                                 'heatindexYearjson' : heatindex_json,
                                 'outHumidityYearjson' : outHumidity_json,
                                 'barometerYearjson' : barometer_json,
                                 'windSpeedYearjson' : windSpeed_json,
                                 'windSpeedAvgYearjson' : windSpeedAvg_json,
                                 'windGustYearjson' : windGust_json,
                                 'windDirYearjson' : windDir_json,
                                 'rainYearjson' : pob_rain_json,
                                 'radiationYearjson' : radiation_json,
                                 'utcOffset': utc_offset,
                                 'YearPlotStart' : _start_ts * 1000,
                                 'YearPlotEnd' : _end_ts * 1000}
        
        # Return our json data
        return [search_list_extension]
