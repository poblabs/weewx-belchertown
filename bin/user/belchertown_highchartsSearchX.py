#
#    Copyright (c) 2016 Gary Roderick
#    https://github.com/gjr80/weewx-highcharts
#
#    See the file LICENSE at the URL above for your full rights.
#
#    Revised for the BelchertownWeather.com weewx skin
#    Author: Gary Roderick and Pat O'Brien
#

import datetime
import time
import weewx
import syslog
import json


from weewx.cheetahgenerator import SearchList
from weeutil.weeutil import TimeSpan, genMonthSpans, startOfInterval, intervalgen
from weeutil.weeutil import intervalgen, archiveDaysAgoSpan
from weewx.units import ValueTuple
from datetime import date
# from user.highcharts import getStatsVectors

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

def roundInt(value, places):
    """round value to 'places' but return as an integer if places=0"""
    if places == 0:
        value = int(round(value, 0))
    else:
        value = round(value, places)
    return value

def get_ago(dt, d_years=0, d_months=0):
    """Function to return date object holding date d_years and d_months ago."""
    # Get year number, month number and day number applying offset as required
    _y, _m, _d = dt.year + d_years, dt.month + d_months, dt.day
    # Calculate actual month number taking into account EOY rollover
    _a, _m = divmod(_m-1, 12)
    # Calculate and return date object
    return date(_y+_a, _m+1, _d)

def get_today_start_end_time():
    start_str = time.strftime("%m/%d/%Y") + " 00:00:00"
    end_str = time.strftime("%m/%d/%Y") + " 23:59:59"
    start_ts = int(time.mktime(time.strptime(start_str, "%m/%d/%Y %H:%M:%S")))
    end_ts = int(time.mktime(time.strptime(end_str, "%m/%d/%Y %H:%M:%S")))
    return start_ts, end_ts

class highchartsDay(SearchList):

    def __init__(self, generator):
        SearchList.__init__(self, generator)

    def get_extension_list(self, timespan, db_lookup):
    
        # First make sure the user wants to use the extension. If not, return right away.
        if self.generator.skin_dict['Extras']['highcharts_enabled'] == "0":
            # Return an empty SLE
            search_list_extension = { }
            return [search_list_extension]
       
        # Get our start time, 24 hours ago but aligned with the (previous) hour
        #_start_ts = startOfInterval(timespan.stop-86400, 3600)
        _start_ts, _end_ts = get_today_start_end_time()
        
        # Get our temperature vector
        (time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'outTemp')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outTemp_vt[2], "1f")[-2])
        outTempRound_vt =  [roundNone(x, usageRound) for x in outTemp_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        outTemp_json = json.dumps(zip(time_ms, outTempRound_vt))
        
        # Get our dewpoint vector
        (time_start_vt, time_stop_vt, dewpoint_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'dewpoint')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(dewpoint_vt[2], "1f")[-2])
        dewpointRound_vt =  [roundNone(x, usageRound) for x in dewpoint_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        dewpoint_json = json.dumps(zip(time_ms, dewpointRound_vt))
        
        # Get our apparent temperature vector
        #(time_start_vt, time_stop_vt, appTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'appTemp_vt')
        #(time_vt, appTemp_vt) = archivedb.getSqlVectors(appTempKey, _start_ts, valid_timespan.stop)
        #appTemp_vt = self.generator.converter.convert(appTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #apptempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(appTemp_vt[2], "1f")[-2])
        # Do the rounding
        #appTempRound_vt = [round(x,apptempRound) if x is not None else None for x in appTemp_vt[0]]
        # loginf("appTempRound_vt=%s" % appTempRound_vt)
        
        # Get our wind chill vector
        (time_start_vt, time_stop_vt, windchill_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windchill')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windchill_vt[2], "1f")[-2])
        windchillRound_vt =  [roundNone(x, usageRound) for x in windchill_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        windchill_json = json.dumps(zip(time_ms, windchillRound_vt))
        
        # Get our heat index vector
        (time_start_vt, time_stop_vt, heatindex_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'heatindex')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(heatindex_vt[2], "1f")[-2])
        heatindexRound_vt =  [roundNone(x, usageRound) for x in heatindex_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        heatindex_json = json.dumps(zip(time_ms, heatindexRound_vt))
        
        # Get our humidity vector
        (time_start_vt, time_stop_vt, outHumidity_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'outHumidity')
        outHumidity_json = json.dumps(zip(time_ms, outHumidity_vt[0]))
        
        # Get our barometer vector
        (time_start_vt, time_stop_vt, barometer_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'barometer')
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
        (time_start_vt, time_stop_vt, windSpeed_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windSpeed')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windSpeed_vt[2], "1f")[-2])
        windSpeedRound_vt =  [roundNone(x, usageRound) for x in windSpeed_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        windSpeed_json = json.dumps(zip(time_ms, windSpeedRound_vt))
        
        # Get our wind gust vector
        (time_start_vt, time_stop_vt, windGust_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windGust')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windGust_vt[2], "1f")[-2])
        windGustRound_vt =  [roundNone(x, usageRound) for x in windGust_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        windGust_json = json.dumps(zip(time_ms, windGustRound_vt))
        
        # Get our wind direction vector
        (time_start_vt, time_stop_vt, windDir_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windDir')
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        windDir_json = json.dumps(zip(time_ms, windDir_vt[0]))
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our rain vector, need to sum over the hour
        ##(time_start_vt, time_stop_vt, rain_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'rain', 'sum', 3600)
        #(timeRain_vt, rain_vt) = archivedb.getSqlVectors('rain', _start_ts, valid_timespan.stop, 3600, 'sum')
        # Check if we have a partial hour at the end
        # If we do then set the last time in the time vector to the hour
        # Avoids display issues with the column chart
        #if timeRain_vt[0][-1] < timeRain_vt[0][-2]+3600:
        #    timeRain_vt[0][-1] = timeRain_vt[0][-2]+3600
        # Convert our rain vector
        ##rain_vt = self.generator.converter.convert(rain_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        ##rainRound = int(self.generator.skin_dict['Units']['StringFormats'].get(rain_vt[2], "2f")[-2])
        # Do the rounding
        #rainRound_vt =  [round(x,rainRound) if x is not None else None for x in rain_vt[0]]
        ##rainRound_vt =  [roundNone(x, rainRound) for x in rain_vt[0]]
        ##time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        ##rain_json = json.dumps(zip(time_ms, rainRound_vt))
        #print rain_json
        
        #POB rain vector 2.0
        _pob_rain_lookup = db_lookup().genSql("SELECT dateTime, rain FROM archive WHERE dateTime>=%s AND dateTime<=%s" % (_start_ts, timespan.stop) )
        rain_time_ms = []
        rain_round = []
        for rainsql in _pob_rain_lookup:
            rain_time_ms.append(float(rainsql[0]) * 1000)
            rain_round.append( round( rainsql[1], 2) )
        pob_rain_json = json.dumps(zip(rain_time_ms, rain_round))
        #print pob_rain_json

        # Rain accumulation totals using the timespan. For static 1 day, look at POB archive above.
        #_pob_rain_totals_lookup = db_lookup().genSql( "SELECT dateTime, @total:=@total+rain AS total FROM archive, (SELECT @total:=0) AS t WHERE dateTime>=%s AND dateTime<=%s" % (_start_ts, timespan.stop) )
        _pob_rain_totals_lookup = db_lookup().genSql( "SELECT dateTime, rain FROM archive WHERE dateTime>=%s AND dateTime<=%s" % (_start_ts, timespan.stop) )
        rain_time_ms = []
        rain_total = []
        rain_count = 0
        for rainsql in _pob_rain_totals_lookup:
            rain_time_ms.append(float(rainsql[0]) * 1000)
            rain_count = rain_count + rainsql[1]
            #rain_total.append( round( rainsql[1], 2) )
            rain_total.append( round( rain_count, 2) )
        pob_rain_total_json = json.dumps(zip(rain_time_ms, rain_total))
        #print pob_rain_total_json
        
        # Get our radiation vector
        (time_start_vt, time_stop_vt, radiation_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'radiation')
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
                                 'radiationDayjson' : radiation_json}
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

        # Get our start time, 7 days ago but aligned with start of day
        _start_ts = startOfInterval(timespan.stop - 604800, 86400)
        # _start_ts  = timespan.stop - 604800
        
        # Get our temperature vector
        #(time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                      'outTemp')
        (time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'outTemp', 'max', 3600)
        
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
        #(time_start_vt, time_stop_vt, dewpoint_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                       'dewpoint')
        (time_start_vt, time_stop_vt, dewpoint_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'dewpoint', 'max', 3600)

        dewpoint_vt = self.generator.converter.convert(dewpoint_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        dewpointRound = int(self.generator.skin_dict['Units']['StringFormats'].get(dewpoint_vt[2], "1f")[-2])
        # Do the rounding
        dewpointRound_vt =  [roundNone(x,dewpointRound) for x in dewpoint_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        dewpoint_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
       
        # ARCHIVE CODE. MAY BE USED ONE DAY?       
        # Get our apparent temperature vector
        #(time_start_vt, time_stop_vt, appTemp_vt) = db_lookup('wd_binding').getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                                  'appTemp')
        #appTemp_vt = self.generator.converter.convert(appTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #apptempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(appTemp_vt[2], "1f")[-2])
        # Do the rounding
        #appTempRound_vt =  [roundNone(x,apptempRound) for x in appTemp_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        #appTemp_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our wind chill vector
        #(time_start_vt, time_stop_vt, windchill_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'windchill')
        (time_start_vt, time_stop_vt, windchill_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windchill', 'max', 3600)
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
        #(time_start_vt, time_stop_vt, heatindex_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'heatindex')
        (time_start_vt, time_stop_vt, heatindex_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'heatindex', 'max', 3600)
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
        #(time_start_vt, time_stop_vt, outHumidity_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                          'outHumidity')
        (time_start_vt, time_stop_vt, outHumidity_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'outHumidity', 'max', 3600)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        outHumidityRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outHumidity_vt[2], "1f")[-2])
        # Do the rounding
        outHumidityRound_vt =  [roundNone(x,outHumidityRound) for x in outHumidity_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        outHumidity_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our barometer vector
        #(time_start_vt, time_stop_vt, barometer_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'barometer')
        (time_start_vt, time_stop_vt, barometer_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'barometer', 'max', 3600)
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
        #(time_start_vt, time_stop_vt, windSpeed_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'windSpeed')
        (time_start_vt, time_stop_vt, windSpeed_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windSpeed', 'max', 3600)
       
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
        #(time_start_vt, time_stop_vt, windGust_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                       'windGust')
        (time_start_vt, time_stop_vt, windGust_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windGust', 'max', 3600)
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
        #(time_start_vt, time_stop_vt, windDir_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                      'windDir')
        (time_start_vt, time_stop_vt, windDir_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windDir', 'max', 3600)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windDirRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windDir_vt[2], "1f")[-2])
        # Do the rounding
        windDirRound_vt =  [roundNone(x,windDirRound) for x in windDir_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windDir_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our rain vector, need to sum over the hour
        ##(time_start_vt, time_stop_vt, rain_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'rain', 'sum', 3600)
        # Check if we have a partial hour at the end
        # If we do then set the last time in the time vector to the hour
        # Avoids display issues with the column chart
        # Need to make sure we have at least 2 records though
        ##if len(time_stop_vt[0]) > 1:
        ##    if time_stop_vt[0][-1] < time_stop_vt[0][-2] + 3600:
        ##        time_stop_vt[0][-1] = time_stop_vt[0][-2] + 3600
        # Convert our rain vector
        #rain_vt = self.generator.converter.convert(rain_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        ##rainRound = int(self.generator.skin_dict['Units']['StringFormats'].get(rain_vt[2], "1f")[-2])
        # Do the rounding
        ##rainRound_vt =  [roundNone(x,rainRound) for x in rain_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        ##timeRain_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        #POB rain vector 2.0
        _pob_rain_lookup = db_lookup().genSql("SELECT dateTime, rain FROM archive WHERE dateTime>=%s AND dateTime<=%s" % (_start_ts, timespan.stop) )
        rain_time_ms = []
        rain_round = []
        for rainsql in _pob_rain_lookup:
            rain_time_ms.append(float(rainsql[0]) * 1000)
            rain_round.append( round( rainsql[1], 2) )
        pob_rain_json = json.dumps(zip(rain_time_ms, rain_round))
        #print pob_rain_json
        
        # Rain accumulation totals using the timespan. For static 1 day, look at POB archive above.
        #_pob_rain_totals_lookup = db_lookup().genSql( "SELECT dateTime, @total:=@total+rain AS total FROM archive, (SELECT @total:=0) AS t WHERE dateTime>=%s AND dateTime<=%s" % (_start_ts, timespan.stop) )
        _pob_rain_totals_lookup = db_lookup().genSql( "SELECT dateTime, rain FROM archive WHERE dateTime>=%s AND dateTime<=%s" % (_start_ts, timespan.stop) )
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
        #print pob_rain_total_json
        
        # Get our radiation vector
        #(time_start_vt, time_stop_vt, radiation_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'radiation')
        (time_start_vt, time_stop_vt, radiation_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'radiation', 'max', 3600)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        radiationRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "1f")[-2])
        # Do the rounding
        radiationRound_vt =  [roundNone(x,radiationRound) for x in radiation_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        radiation_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our insolation vector
        #(time_start_vt, time_stop_vt, insolation_vt) = db_lookup('wdsupp_binding').getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                                         'maxSolarRad')
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #insolationRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "1f")[-2])
        # Do the rounding
        #insolationRound_vt =  [roundNone(x,insolationRound) for x in insolation_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        #insolation_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our UV vector
        #(time_start_vt, time_stop_vt, uv_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'UV')
        #(time_start_vt, time_stop_vt, uv_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'UV', 'max', 3600)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #uvRound = int(self.generator.skin_dict['Units']['StringFormats'].get(uv_vt[2], "1f")[-2])
        # Do the rounding
        #uvRound_vt =  [roundNone(x,uvRound) for x in uv_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        #UV_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Format our vectors in json format. Need the zip() to get time/value pairs
        # Assumes all vectors have the same number of elements
        outTemp_json = json.dumps(zip(outTemp_time_ms, outTempRound_vt))
        dewpoint_json = json.dumps(zip(dewpoint_time_ms, dewpointRound_vt))
        #appTemp_json = json.dumps(zip(appTemp_time_ms, appTempRound_vt))
        windchill_json = json.dumps(zip(windchill_time_ms, windchillRound_vt))
        heatindex_json = json.dumps(zip(heatindex_time_ms, heatindexRound_vt))
        outHumidity_json = json.dumps(zip(outHumidity_time_ms, outHumidityRound_vt))
        barometer_json = json.dumps(zip(barometer_time_ms, barometerRound_vt))
        windSpeed_json = json.dumps(zip(windSpeed_time_ms, windSpeedRound_vt))
        windGust_json = json.dumps(zip(windGust_time_ms, windGustRound_vt))
        windDir_json = json.dumps(zip(windDir_time_ms, windDirRound_vt))
        radiation_json = json.dumps(zip(radiation_time_ms, radiationRound_vt))
        #insolation_json = json.dumps(zip(insolation_time_ms, insolationRound_vt))
        #uv_json = json.dumps(zip(UV_time_ms, uvRound_vt))
        ##rain_json = json.dumps(zip(timeRain_ms, rainRound_vt))
        
        # Put into a dictionary to return
        search_list_extension = {'outTempWeekjson' : outTemp_json,
                                 'dewpointWeekjson' : dewpoint_json,
                                 #'appTempWeekjson' : appTemp_json,
                                 'windchillWeekjson' : windchill_json,
                                 'heatindexWeekjson' : heatindex_json,
                                 'outHumidityWeekjson' : outHumidity_json,
                                 'barometerWeekjson' : barometer_json,
                                 'windSpeedWeekjson' : windSpeed_json,
                                 'windGustWeekjson' : windGust_json,
                                 'windDirWeekjson' : windDir_json,
                                 ##'rainWeekjson' : rain_json,
                                 'rainWeekjson' : pob_rain_json,
                                 'rainWeekTotaljson' : pob_rain_total_json,
                                 'radiationWeekjson' : radiation_json,
                                 #'insolationWeekjson' : insolation_json,
                                 #'uvWeekjson' : uv_json,
                                 'weekPlotStart' : _start_ts * 1000,
                                 'weekPlotEnd' : timespan.stop * 1000}
        
        #t2 = time.time()
        #logdbg2("highchartsWeek SLE executed in %0.3f seconds" % (t2 - t1))

        # Return our json data
        return [search_list_extension]
        
    
        
class highchartsWeek_original_archived(SearchList):

    def __init__(self, generator):
        SearchList.__init__(self, generator)

    def get_extension_list(self, timespan, db_lookup):

        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Do we have dedicated appTemp field or not? If so use it else revert to extraTemp2
        # as per original Weewx-WD schema
        #sqlkeys = archivedb._getTypes()
        #if 'appTemp' in sqlkeys:
        #    appTempKey = 'appTemp'
        #elif 'extraTemp2' in sqlkeys:
        #    appTempKey = 'extraTemp2'
        # Get our start time, 7 days ago but aligned with start of day
        
        #_start_ts = startOfInterval(valid_timespan.stop-604800, 86400)
        # _start_ts  = valid_timespan.stop - 604800
        _start_ts = startOfInterval(timespan.stop-604800, 86400)
        
        # Get our temperature vector
        (time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'outTemp')
        #(time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(archiveDaysAgoSpan(timespan.stop, days_ago=7), 'outTemp')
        #print len(outTemp_vt[0])
        # Weekly mode: select the sensor reading for only 1 hour a day
        # 168 total readings per sensor
        # 3600 = hour
        # 86400 = day
        #for span in intervalgen(_start_ts, timespan.stop, 86400):
            #print db_lookup().getSqlVectors(span, 'outTemp')
            #print span
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outTemp_vt[2], "1f")[-2])
        outTempRound_vt = [roundNone(x, usageRound) for x in outTemp_vt[0]]
        time_ms = [float(x) * 1000 for x in time_stop_vt[0]]
        outTemp_json = json.dumps(zip(time_ms, outTempRound_vt))
        #print outTemp_json
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our temperature vector
        #(time_vt, outTemp_vt) = archivedb.getSqlVectors('outTemp', _start_ts, valid_timespan.stop)
        # Convert our temperature vector
        #outTemp_vt = self.generator.converter.convert(outTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #tempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outTemp_vt[2], "1f")[-2])
        # Do the rounding
        #outTempRound_vt =  [round(x,tempRound) if x is not None else None for x in outTemp_vt[0]]
        
        # Get our dewpoint vector
        (time_start_vt, time_stop_vt, dewpoint_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'dewpoint')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(dewpoint_vt[2], "1f")[-2])
        dewpointRound_vt =  [roundNone(x, usageRound) for x in dewpoint_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        dewpoint_json = json.dumps(zip(time_ms, dewpointRound_vt))

        # ARCHIVE CODE. MAY BE USED ONE DAY?
        #(time_vt, dewpoint_vt) = archivedb.getSqlVectors('dewpoint', _start_ts, valid_timespan.stop)
        #dewpoint_vt = self.generator.converter.convert(dewpoint_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #dewpointRound = int(self.generator.skin_dict['Units']['StringFormats'].get(dewpoint_vt[2], "1f")[-2])
        # Do the rounding
        #dewpointRound_vt =  [round(x,dewpointRound) if x is not None else None for x in dewpoint_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our apparent temperature vector
        #(time_vt, appTemp_vt) = archivedb.getSqlVectors(appTempKey, _start_ts, valid_timespan.stop)
        #appTemp_vt = self.generator.converter.convert(appTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #apptempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(appTemp_vt[2], "1f")[-2])
        # Do the rounding
        #appTempRound_vt =  [round(x,apptempRound) if x is not None else None for x in appTemp_vt[0]]
        
        # Get our wind chill vector
        (time_start_vt, time_stop_vt, windchill_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windchill')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windchill_vt[2], "1f")[-2])
        windchillRound_vt =  [roundNone(x, usageRound) for x in windchill_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        windchill_json = json.dumps(zip(time_ms, windchillRound_vt))

        # ARCHIVE CODE. MAY BE USED ONE DAY?
        #(time_vt, windchill_vt) = archivedb.getSqlVectors('windchill', _start_ts, valid_timespan.stop)
        #windchill_vt = self.generator.converter.convert(windchill_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #windchillRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windchill_vt[2], "1f")[-2])
        # Do the rounding
        #windchillRound_vt =  [round(x,windchillRound) if x is not None else None for x in windchill_vt[0]]
        
        # Get our heat index vector
        (time_start_vt, time_stop_vt, heatindex_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'heatindex')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(heatindex_vt[2], "1f")[-2])
        heatindexRound_vt =  [roundNone(x, usageRound) for x in heatindex_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        heatindex_json = json.dumps(zip(time_ms, heatindexRound_vt))

        # ARCHIVE CODE. MAY BE USED ONE DAY?
        #(time_vt, heatindex_vt) = archivedb.getSqlVectors('heatindex', _start_ts, valid_timespan.stop)
        #heatindex_vt = self.generator.converter.convert(heatindex_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #heatindexRound = int(self.generator.skin_dict['Units']['StringFormats'].get(heatindex_vt[2], "1f")[-2])
        # Do the rounding
        #heatindexRound_vt =  [round(x,heatindexRound) if x is not None else None for x in heatindex_vt[0]]
        
        # Get our humidity vector
        (time_start_vt, time_stop_vt, outHumidity_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'outHumidity')
        outHumidity_json = json.dumps(zip(time_ms, outHumidity_vt[0]))

        #(time_vt, outHumidity_vt) = archivedb.getSqlVectors('outHumidity', _start_ts, valid_timespan.stop)
        
        # Get our barometer vector
        (time_start_vt, time_stop_vt, barometer_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'barometer')
        barometer_vt = self.generator.converter.convert(barometer_vt)
        barometerRound = int(self.generator.skin_dict['Units']['StringFormats'].get(barometer_vt[2], "1f")[-2])
        barometerRound_vt = [round(x,barometerRound) if x is not None else None for x in barometer_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        barometer_json = json.dumps(zip(time_ms, barometerRound_vt))

        # ARCHIVE CODE. MAY BE USED ONE DAY?
        #(time_vt, barometer_vt) = archivedb.getSqlVectors('barometer', _start_ts, valid_timespan.stop)
        #barometer_vt = self.generator.converter.convert(barometer_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #humidityRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outHumidity_vt[2], "1f")[-2])
        # Do the rounding
        #barometerRound_vt =  [round(x,humidityRound) if x is not None else None for x in barometer_vt[0]]
        
        # Get our wind speed vector
        (time_start_vt, time_stop_vt, windSpeed_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windSpeed')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windSpeed_vt[2], "1f")[-2])
        windSpeedRound_vt =  [roundNone(x, usageRound) for x in windSpeed_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        windSpeed_json = json.dumps(zip(time_ms, windSpeedRound_vt))

        # ARCHIVE CODE. MAY BE USED ONE DAY?
        #(time_vt, windSpeed_vt) = archivedb.getSqlVectors('windSpeed', _start_ts, valid_timespan.stop)
        #windSpeed_vt = self.generator.converter.convert(windSpeed_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #windspeedRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windSpeed_vt[2], "1f")[-2])
        # Do the rounding
        #windSpeedRound_vt =  [round(x,windspeedRound) if x is not None else None for x in windSpeed_vt[0]]
        
        # Get our wind gust vector
        (time_start_vt, time_stop_vt, windGust_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windGust')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windGust_vt[2], "1f")[-2])
        windGustRound_vt =  [roundNone(x, usageRound) for x in windGust_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        windGust_json = json.dumps(zip(time_ms, windGustRound_vt))

        # ARCHIVE CODE. MAY BE USED ONE DAY?
        #(time_vt, windGust_vt) = archivedb.getSqlVectors('windGust', _start_ts, valid_timespan.stop)
        #windGust_vt = self.generator.converter.convert(windGust_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #windgustRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windGust_vt[2], "1f")[-2])
        # Do the rounding
        #windGustRound_vt =  [round(x,windgustRound) if x is not None else None for x in windGust_vt[0]]
        
        # Get our wind direction vector
        (time_start_vt, time_stop_vt, windDir_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windDir')
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        windDir_json = json.dumps(zip(time_ms, windDir_vt[0]))

        #(time_vt, windDir_vt) = archivedb.getSqlVectors('windDir', _start_ts, valid_timespan.stop)
        
        # Get our rain vector, need to sum over the hour
        (time_start_vt, time_stop_vt, rain_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'rain', 'sum', 86400)
        #(timeRain_vt, rain_vt) = archivedb.getSqlVectors('rain', _start_ts, valid_timespan.stop, 3600, 'sum')
        # Check if we have a partial hour at the end
        # If we do then set the last time in the time vector to the hour
        # Avoids display issues with the column chart
        #if timeRain_vt[0][-1] < timeRain_vt[0][-2]+86400:
        #    timeRain_vt[0][-1] = timeRain_vt[0][-2]+86400
        # Convert our rain vector
        rain_vt = self.generator.converter.convert(rain_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        rainRound = int(self.generator.skin_dict['Units']['StringFormats'].get(rain_vt[2], "2f")[-2])
        # Do the rounding
        #rainRound_vt =  [round(x,rainRound) if x is not None else None for x in rain_vt[0]]
        rainRound_vt =  [roundNone(x, usageRound) for x in rain_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        rain_json = json.dumps(zip(time_ms, rainRound_vt))

        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our rain vector, need to sum over the day
        #(timeRain_vt, rain_vt) = archivedb.getSqlVectors('rain', _start_ts, valid_timespan.stop, 86400, 'sum')
        # Check if we have a partial day at the end
        # If we do then set the last time in the time vector to the next midnight
        # Avoids display issues with the column chart
        #if timeRain_vt[0][-1] < timeRain_vt[0][-2]+86400:
        #    timeRain_vt[0][-1] = timeRain_vt[0][-2]+86400
        # Convert our rain vector
        #rain_vt = self.generator.converter.convert(rain_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #rainRound = int(self.generator.skin_dict['Units']['StringFormats'].get(rain_vt[2], "1f")[-2])
        # Do the rounding
        #rainRound_vt =  [round(x,rainRound) if x is not None else None for x in rain_vt[0]]
        
        # Get our radiation vector
        (time_start_vt, time_stop_vt, radiation_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'radiation')
        usageRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "2f")[-2])
        radiationRound_vt =  [roundNone(x, usageRound) for x in radiation_vt[0]]
        time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        radiation_json = json.dumps(zip(time_ms, radiationRound_vt))
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        #(time_vt, radiation_vt) = archivedb.getSqlVectors('radiation', _start_ts, valid_timespan.stop)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #radiationRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "1f")[-2])
        # Do the rounding
        #radiationRound_vt =  [round(x,radiationRound) if x is not None else None for x in radiation_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our time vector in ms (highcharts requirement)
        #time_ms =  [float(x) * 1000 for x in time_vt[0]]
        # Rain time vector is different so get it in ms too
        # Need to subtract a day as Highcharts tool tip uses ts from end of day
        # which is midnight the following day - trust me it works!
        #timeRain_ms =  [(float(x)-86400) * 1000 for x in timeRain_vt[0]]
        # Format our vectors in json format. Need the zip() to get time/value pairs
        # Assumes all vectors have the same number of elements
        #outTemp_json = json.dumps(zip(time_ms, outTempRound_vt))
        #dewpoint_json = json.dumps(zip(time_ms, dewpointRound_vt))
        #appTemp_json = json.dumps(zip(time_ms, appTempRound_vt))
        #windchill_json = json.dumps(zip(time_ms, windchillRound_vt))
        #heatindex_json = json.dumps(zip(time_ms, heatindexRound_vt))
        # Use 1st field in our original _vt as we did not round this one
        #outHumidity_json = json.dumps(zip(time_ms, outHumidity_vt[0]))
        #barometer_json = json.dumps(zip(time_ms, barometerRound_vt))
        #windSpeed_json = json.dumps(zip(time_ms, windSpeedRound_vt))
        #windGust_json = json.dumps(zip(time_ms, windGustRound_vt))
        # Use 1st field in our original _vt as we did not round this one
        #windDir_json = json.dumps(zip(time_ms, windDir_vt[0]))
        #radiation_json = json.dumps(zip(time_ms, radiationRound_vt))
        #rain_json = json.dumps(zip(timeRain_ms, rainRound_vt))
                                 #'appTempWeekjson' : appTemp_json,
        
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
                                 'rainWeekjson' : rain_json,
                                 'radiationWeekjson' : radiation_json}
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

        # Get our start time, 7 days ago but aligned with start of day
        # POB: 2592000 = seconds in a month
        # 86400 = seconds in 24 hours
        _start_ts = startOfInterval(timespan.stop - 2592000, 86400)
        # _start_ts  = timespan.stop - 604800
        
        # Get our temperature vector
        #(time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                      'outTemp')
        (time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'outTemp', 'max', 86400)

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
        #(time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                      'outTemp')
        (time_start_vt, time_stop_vt, outTemp_min_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'outTemp', 'min', 86400)

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
        #(time_start_vt, time_stop_vt, dewpoint_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                       'dewpoint')
        (time_start_vt, time_stop_vt, dewpoint_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'dewpoint', 'max', 86400)

        dewpoint_vt = self.generator.converter.convert(dewpoint_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        dewpointRound = int(self.generator.skin_dict['Units']['StringFormats'].get(dewpoint_vt[2], "1f")[-2])
        # Do the rounding
        dewpointRound_vt =  [roundNone(x,dewpointRound) for x in dewpoint_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        dewpoint_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our apparent temperature vector
        #(time_start_vt, time_stop_vt, appTemp_vt) = db_lookup('wd_binding').getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                                  'appTemp')
        #appTemp_vt = self.generator.converter.convert(appTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #apptempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(appTemp_vt[2], "1f")[-2])
        # Do the rounding
        #appTempRound_vt =  [roundNone(x,apptempRound) for x in appTemp_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        #appTemp_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our wind chill vector
        #(time_start_vt, time_stop_vt, windchill_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'windchill')
        (time_start_vt, time_stop_vt, windchill_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windchill', 'max', 86400)
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
        #(time_start_vt, time_stop_vt, heatindex_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'heatindex')
        (time_start_vt, time_stop_vt, heatindex_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'heatindex', 'max', 86400)
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
        #(time_start_vt, time_stop_vt, outHumidity_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                          'outHumidity')
        (time_start_vt, time_stop_vt, outHumidity_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'outHumidity', 'max', 86400)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        outHumidityRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outHumidity_vt[2], "1f")[-2])
        # Do the rounding
        outHumidityRound_vt =  [roundNone(x,outHumidityRound) for x in outHumidity_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        outHumidity_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our barometer vector
        #(time_start_vt, time_stop_vt, barometer_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'barometer')
        (time_start_vt, time_stop_vt, barometer_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'barometer', 'max', 86400)
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
        #(time_start_vt, time_stop_vt, windSpeed_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'windSpeed')
        (time_start_vt, time_stop_vt, windSpeed_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windSpeed', 'max', 86400)
       
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
        (time_start_vt, time_stop_vt, windSpeedAvg_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windSpeed', 'avg', 86400)
       
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
        #(time_start_vt, time_stop_vt, windGust_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                       'windGust')
        (time_start_vt, time_stop_vt, windGust_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windGust', 'max', 86400)
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
        #(time_start_vt, time_stop_vt, windDir_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                      'windDir')
        (time_start_vt, time_stop_vt, windDir_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windDir', 'avg', 86400)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windDirRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windDir_vt[2], "1f")[-2])
        # Do the rounding
        windDirRound_vt =  [roundNone(x,windDirRound) for x in windDir_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windDir_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our rain vector, need to sum over the hour
        ##(time_start_vt, time_stop_vt, rain_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'rain', 'sum', 86400)
        # Check if we have a partial hour at the end
        # If we do then set the last time in the time vector to the hour
        # Avoids display issues with the column chart
        # Need to make sure we have at least 2 records though
        ##if len(time_stop_vt[0]) > 1:
        ##    if time_stop_vt[0][-1] < time_stop_vt[0][-2] + 3600:
        ##        time_stop_vt[0][-1] = time_stop_vt[0][-2] + 3600
        # Convert our rain vector
        ##rain_vt = self.generator.converter.convert(rain_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        ##rainRound = int(self.generator.skin_dict['Units']['StringFormats'].get(rain_vt[2], "1f")[-2])
        # Do the rounding
        ##rainRound_vt =  [roundNone(x,rainRound) for x in rain_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        ##timeRain_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        #POB rain vector 2.0
        _pob_rain_lookup = db_lookup().genSql("SELECT dateTime, rain FROM archive WHERE dateTime>=%s AND dateTime<=%s" % (_start_ts, timespan.stop) )
        rain_time_ms = []
        rain_round = []
        for rainsql in _pob_rain_lookup:
            rain_time_ms.append(float(rainsql[0]) * 1000)
            rain_round.append( round( rainsql[1], 2) )
        pob_rain_json = json.dumps(zip(rain_time_ms, rain_round))
        #print pob_rain_json
        
        # Rain accumulation totals using the timespan. For static 1 day, look at POB archive above.
        #_pob_rain_totals_lookup = db_lookup().genSql( "SELECT dateTime, @total:=@total+rain AS total FROM archive, (SELECT @total:=0) AS t WHERE dateTime>=%s AND dateTime<=%s" % (_start_ts, timespan.stop) )
        _pob_rain_totals_lookup = db_lookup().genSql( "SELECT dateTime, rain FROM archive WHERE dateTime>=%s AND dateTime<=%s" % (_start_ts, timespan.stop) )
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
        #print pob_rain_total_json
        
        # Get our radiation vector
        #(time_start_vt, time_stop_vt, radiation_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'radiation')
        (time_start_vt, time_stop_vt, radiation_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'radiation', 'max', 86400)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        radiationRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "1f")[-2])
        # Do the rounding
        radiationRound_vt =  [roundNone(x,radiationRound) for x in radiation_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        radiation_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our insolation vector
        #(time_start_vt, time_stop_vt, insolation_vt) = db_lookup('wdsupp_binding').getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                                         'maxSolarRad')
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #insolationRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "1f")[-2])
        # Do the rounding
        #insolationRound_vt =  [roundNone(x,insolationRound) for x in insolation_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        #insolation_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our UV vector
        #(time_start_vt, time_stop_vt, uv_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'UV')
        #(time_start_vt, time_stop_vt, uv_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'UV', 'max', 3600)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #uvRound = int(self.generator.skin_dict['Units']['StringFormats'].get(uv_vt[2], "1f")[-2])
        # Do the rounding
        #uvRound_vt =  [roundNone(x,uvRound) for x in uv_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        #UV_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Format our vectors in json format. Need the zip() to get time/value pairs
        # Assumes all vectors have the same number of elements
        outTemp_json = json.dumps(zip(outTemp_time_ms, outTempRound_vt))
        outTemp_min_json = json.dumps(zip(outTempMin_time_ms, outTempMinRound_vt))
        dewpoint_json = json.dumps(zip(dewpoint_time_ms, dewpointRound_vt))
        #appTemp_json = json.dumps(zip(appTemp_time_ms, appTempRound_vt))
        windchill_json = json.dumps(zip(windchill_time_ms, windchillRound_vt))
        heatindex_json = json.dumps(zip(heatindex_time_ms, heatindexRound_vt))
        outHumidity_json = json.dumps(zip(outHumidity_time_ms, outHumidityRound_vt))
        barometer_json = json.dumps(zip(barometer_time_ms, barometerRound_vt))
        windSpeed_json = json.dumps(zip(windSpeed_time_ms, windSpeedRound_vt))
        windSpeedAvg_json = json.dumps(zip(windSpeedAvg_time_ms, windSpeedAvgRound_vt))
        windGust_json = json.dumps(zip(windGust_time_ms, windGustRound_vt))
        windDir_json = json.dumps(zip(windDir_time_ms, windDirRound_vt))
        radiation_json = json.dumps(zip(radiation_time_ms, radiationRound_vt))
        #insolation_json = json.dumps(zip(insolation_time_ms, insolationRound_vt))
        #uv_json = json.dumps(zip(UV_time_ms, uvRound_vt))
        #rain_json = json.dumps(zip(timeRain_ms, rainRound_vt))
        
        # Put into a dictionary to return
        search_list_extension = {'outTempMonthjson' : outTemp_json,
                                 'outTempMinMonthjson' : outTemp_min_json,
                                 'dewpointMonthjson' : dewpoint_json,
                                 #'appTempMonthjson' : appTemp_json,
                                 'windchillMonthjson' : windchill_json,
                                 'heatindexMonthjson' : heatindex_json,
                                 'outHumidityMonthjson' : outHumidity_json,
                                 'barometerMonthjson' : barometer_json,
                                 'windSpeedMonthjson' : windSpeed_json,
                                 'windSpeedAvgMonthjson' : windSpeedAvg_json,
                                 'windGustMonthjson' : windGust_json,
                                 'windDirMonthjson' : windDir_json,
                                 #'rainMonthjson' : rain_json,
                                 'rainMonthjson' : pob_rain_json,
                                 'rainMonthTotaljson' : pob_rain_total_json,
                                 'radiationMonthjson' : radiation_json,
                                 #'insolationMonthjson' : insolation_json,
                                 #'uvMonthjson' : uv_json,
                                 'MonthPlotStart' : _start_ts * 1000,
                                 'MonthPlotEnd' : timespan.stop * 1000}
        
        #t2 = time.time()
        #logdbg2("highchartsWeek SLE executed in %0.3f seconds" % (t2 - t1))

        # Return our json data
        return [search_list_extension]
        
    
class highchartsMonth_original_archived(SearchList):

    def __init__(self, generator):
        SearchList.__init__(self, generator)

    def get_extension_list(self, timespan, db_lookup):

        # Do we have dedicated appTemp field or not? If so use it else revert to extraTemp2
        # as per original Weewx-WD schema
        sqlkeys = archivedb._getTypes()
        if 'appTemp' in sqlkeys:
            appTempKey = 'appTemp'
        elif 'extraTemp2' in sqlkeys:
            appTempKey = 'extraTemp2'
        # Our start time is midnight one month ago
        # Get a time object for midnight
        _mn_time = datetime.time(0)
        # Get a datetime object for our end datetime
        _day_date = datetime.datetime.fromtimestamp(valid_timespan.stop)
        # Calculate our start timestamp by combining date 1 month ago and midnight time
        _start_ts  = int(time.mktime(datetime.datetime.combine(get_ago(_day_date,0,-1),_mn_time).timetuple()))
        # Get our temperature vector
        (time_vt, outTemp_vt) = archivedb.getSqlVectors('outTemp', _start_ts, valid_timespan.stop, 3600, 'avg')
        # Convert our temperature vector
        outTemp_vt = self.generator.converter.convert(outTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        tempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outTemp_vt[2], "1f")[-2])
        # Do the rounding
        outTempRound_vt =  [round(x,tempRound) if x is not None else None for x in outTemp_vt[0]]
        # Get our dewpoint vector
        (time_vt, dewpoint_vt) = archivedb.getSqlVectors('dewpoint', _start_ts, valid_timespan.stop, 3600, 'avg')
        dewpoint_vt = self.generator.converter.convert(dewpoint_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        dewpointRound = int(self.generator.skin_dict['Units']['StringFormats'].get(dewpoint_vt[2], "1f")[-2])
        # Do the rounding
        dewpointRound_vt =  [round(x,dewpointRound) if x is not None else None for x in dewpoint_vt[0]]
        # Get our apparent temperature vector
        (time_vt, appTemp_vt) = archivedb.getSqlVectors(appTempKey, _start_ts, valid_timespan.stop, 3600, 'avg')
        appTemp_vt = self.generator.converter.convert(appTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        apptempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(appTemp_vt[2], "1f")[-2])
        # Do the rounding
        appTempRound_vt =  [round(x,apptempRound) if x is not None else None for x in appTemp_vt[0]]
        # Get our wind chill vector
        (time_vt, windchill_vt) = archivedb.getSqlVectors('windchill', _start_ts, valid_timespan.stop, 3600, 'avg')
        windchill_vt = self.generator.converter.convert(windchill_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windchillRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windchill_vt[2], "1f")[-2])
        # Do the rounding
        windchillRound_vt =  [round(x,windchillRound) if x is not None else None for x in windchill_vt[0]]
        # Get our heat index vector
        (time_vt, heatindex_vt) = archivedb.getSqlVectors('heatindex', _start_ts, valid_timespan.stop, 3600, 'avg')
        heatindex_vt = self.generator.converter.convert(heatindex_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        heatindexRound = int(self.generator.skin_dict['Units']['StringFormats'].get(heatindex_vt[2], "1f")[-2])
        # Do the rounding
        heatindexRound_vt =  [round(x,heatindexRound) if x is not None else None for x in heatindex_vt[0]]
        # Get our humidity vector
        (time_vt, outHumidity_vt) = archivedb.getSqlVectors('outHumidity', _start_ts, valid_timespan.stop, 3600, 'avg')
        # Get our barometer vector
        (time_vt, barometer_vt) = archivedb.getSqlVectors('barometer', _start_ts, valid_timespan.stop, 3600, 'avg')
        barometer_vt = self.generator.converter.convert(barometer_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        humidityRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outHumidity_vt[2], "1f")[-2])
        # Do the rounding
        barometerRound_vt =  [round(x,humidityRound) if x is not None else None for x in barometer_vt[0]]
        # Get our wind speed vector
        (time_vt, windSpeed_vt) = archivedb.getSqlVectors('windSpeed', _start_ts, valid_timespan.stop, 3600, 'avg')
        windSpeed_vt = self.generator.converter.convert(windSpeed_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windspeedRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windSpeed_vt[2], "1f")[-2])
        # Do the rounding
        windSpeedRound_vt =  [round(x,windspeedRound) if x is not None else None for x in windSpeed_vt[0]]
        # Get our wind gust vector
        (time_vt, windGust_vt) = archivedb.getSqlVectors('windGust', _start_ts, valid_timespan.stop, 3600, 'avg')
        windGust_vt = self.generator.converter.convert(windGust_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windgustRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windGust_vt[2], "1f")[-2])
        # Do the rounding
        windGustRound_vt =  [round(x,windgustRound) if x is not None else None for x in windGust_vt[0]]
        # Get our wind direction vector
        (time_vt, windDir_vt) = archivedb.getSqlVectors('windDir', _start_ts, valid_timespan.stop, 3600, 'avg')
        # Get our rain vector, need to sum over the day
        (timeRain_vt, rain_vt) = archivedb.getSqlVectors('rain', _start_ts, valid_timespan.stop, 86400, 'sum')
        # Check if we have a partial day at the end
        # If we do then set the last time in the time vector to the next midnight
        # Avoids display issues with the column chart
        if timeRain_vt[0][-1] < timeRain_vt[0][-2]+86400:
            timeRain_vt[0][-1] = timeRain_vt[0][-2]+86400
        # Convert our rain vector
        rain_vt = self.generator.converter.convert(rain_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        rainRound = int(self.generator.skin_dict['Units']['StringFormats'].get(rain_vt[2], "1f")[-2])
        # Do the rounding
        rainRound_vt =  [round(x,rainRound) if x is not None else None for x in rain_vt[0]]
        # Get our radiation vector
        (time_vt, radiation_vt) = archivedb.getSqlVectors('radiation', _start_ts, valid_timespan.stop, 3600, 'avg')
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        radiationRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "1f")[-2])
        # Do the rounding
        radiationRound_vt =  [round(x,radiationRound) if x is not None else None for x in radiation_vt[0]]
        # Get our time vector in ms (highcharts requirement)
        time_ms =  [float(x) * 1000 for x in time_vt[0]]
        # Rain time vector is different so get it in ms too
        # Need to subtract a day as Highcharts tool tip uses ts from end of day
        # which is midnight the following day - trust me it works!
        timeRain_ms =  [(float(x)-86400) * 1000 for x in timeRain_vt[0]]
        # Format our vectors in json format. Need the zip() to get time/value pairs
        # Assumes all vectors have the same number of elements
        outTemp_json = json.dumps(zip(time_ms, outTempRound_vt))
        dewpoint_json = json.dumps(zip(time_ms, dewpointRound_vt))
        appTemp_json = json.dumps(zip(time_ms, appTempRound_vt))
        windchill_json = json.dumps(zip(time_ms, windchillRound_vt))
        heatindex_json = json.dumps(zip(time_ms, heatindexRound_vt))
        # Use 1st field in our original _vt as we did not round this one
        outHumidity_json = json.dumps(zip(time_ms, outHumidity_vt[0]))
        barometer_json = json.dumps(zip(time_ms, barometerRound_vt))
        windSpeed_json = json.dumps(zip(time_ms, windSpeedRound_vt))
        windGust_json = json.dumps(zip(time_ms, windGustRound_vt))
        # Use 1st field in our original _vt as we did not round this one
        windDir_json = json.dumps(zip(time_ms, windDir_vt[0]))
        radiation_json = json.dumps(zip(time_ms, radiationRound_vt))
        rain_json = json.dumps(zip(timeRain_ms, rainRound_vt))
        
        # Put into a dictionary to return
        search_list_extension = {'outTempMonthjson' : outTemp_json,
                                 'dewpointMonthjson' : dewpoint_json,
                                 'appTempMonthjson' : appTemp_json,
                                 'windchillMonthjson' : windchill_json,
                                 'heatindexMonthjson' : heatindex_json,
                                 'outHumidityMonthjson' : outHumidity_json,
                                 'barometerMonthjson' : barometer_json,
                                 'windSpeedMonthjson' : windSpeed_json,
                                 'windGustMonthjson' : windGust_json,
                                 'windDirMonthjson' : windDir_json,
                                 'rainMonthjson' : rain_json,
                                 'radiationMonthjson' : radiation_json}
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

        # Get our start time, 7 days ago but aligned with start of day
        # POB: 31556952 = seconds in a year
        # 86400 = seconds in 24 hours
        #_start_ts = startOfInterval(timespan.stop - 31556952, 86400) # This gets the last 365 days
        # _start_ts  = timespan.stop - 604800
        now = datetime.datetime.now()
        date_time = '01/01/%s 00:00:00' % now.year
        pattern = '%m/%d/%Y %H:%M:%S'
        year_start_epoch = int(time.mktime(time.strptime(date_time, pattern)))
        _start_ts = startOfInterval(year_start_epoch ,86400) # This is the current calendar year
        #print _start_ts
        
        # Get our temperature vector
        #(time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                      'outTemp')
        (time_start_vt, time_stop_vt, outTemp_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'outTemp', 'max', 86400)

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
        (time_start_vt, time_stop_vt, outTempMin_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'outTemp', 'min', 86400)

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
        #(time_start_vt, time_stop_vt, dewpoint_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                       'dewpoint')
        (time_start_vt, time_stop_vt, dewpoint_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'dewpoint', 'max', 86400)

        dewpoint_vt = self.generator.converter.convert(dewpoint_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        dewpointRound = int(self.generator.skin_dict['Units']['StringFormats'].get(dewpoint_vt[2], "1f")[-2])
        # Do the rounding
        dewpointRound_vt =  [roundNone(x,dewpointRound) for x in dewpoint_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        dewpoint_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our apparent temperature vector
        #(time_start_vt, time_stop_vt, appTemp_vt) = db_lookup('wd_binding').getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                                  'appTemp')
        #appTemp_vt = self.generator.converter.convert(appTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #apptempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(appTemp_vt[2], "1f")[-2])
        # Do the rounding
        #appTempRound_vt =  [roundNone(x,apptempRound) for x in appTemp_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        #appTemp_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our wind chill vector
        #(time_start_vt, time_stop_vt, windchill_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'windchill')
        (time_start_vt, time_stop_vt, windchill_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windchill', 'max', 86400)
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
        #(time_start_vt, time_stop_vt, heatindex_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'heatindex')
        (time_start_vt, time_stop_vt, heatindex_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'heatindex', 'max', 86400)
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
        #(time_start_vt, time_stop_vt, outHumidity_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                          'outHumidity')
        (time_start_vt, time_stop_vt, outHumidity_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'outHumidity', 'max', 86400)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        outHumidityRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outHumidity_vt[2], "1f")[-2])
        # Do the rounding
        outHumidityRound_vt =  [roundNone(x,outHumidityRound) for x in outHumidity_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        outHumidity_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Get our barometer vector
        #(time_start_vt, time_stop_vt, barometer_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'barometer')
        (time_start_vt, time_stop_vt, barometer_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'barometer', 'max', 86400)
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
        #(time_start_vt, time_stop_vt, windSpeed_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'windSpeed')
        (time_start_vt, time_stop_vt, windSpeed_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windSpeed', 'max', 86400)
       
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
        (time_start_vt, time_stop_vt, windSpeedAvg_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windSpeed', 'avg', 86400)
       
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
        #(time_start_vt, time_stop_vt, windGust_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                       'windGust')
        (time_start_vt, time_stop_vt, windGust_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windGust', 'max', 86400)
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
        #(time_start_vt, time_stop_vt, windDir_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                      'windDir')
        (time_start_vt, time_stop_vt, windDir_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'windDir', 'max', 86400)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windDirRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windDir_vt[2], "1f")[-2])
        # Do the rounding
        windDirRound_vt =  [roundNone(x,windDirRound) for x in windDir_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        windDir_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our rain vector, need to sum over the hour
        ##(time_start_vt, time_stop_vt, rain_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'rain', 'sum', 86400)
        # Check if we have a partial hour at the end
        # If we do then set the last time in the time vector to the hour
        # Avoids display issues with the column chart
        # Need to make sure we have at least 2 records though
        ##if len(time_stop_vt[0]) > 1:
        ##    if time_stop_vt[0][-1] < time_stop_vt[0][-2] + 3600:
        ##        time_stop_vt[0][-1] = time_stop_vt[0][-2] + 3600
        # Convert our rain vector
        #rain_vt = self.generator.converter.convert(rain_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #rainRound = int(self.generator.skin_dict['Units']['StringFormats'].get(rain_vt[2], "1f")[-2])
        # Do the rounding
        #rainRound_vt =  [roundNone(x,rainRound) for x in rain_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        #timeRain_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        #POB rain vector 2.0
        _pob_rain_lookup = db_lookup().genSql("SELECT dateTime, rain FROM archive WHERE dateTime>=%s AND dateTime<=%s" % (_start_ts, timespan.stop) )
        rain_time_ms = []
        rain_round = []
        for rainsql in _pob_rain_lookup:
            rain_time_ms.append(float(rainsql[0]) * 1000)
            rain_round.append( rainsql[1] )
        pob_rain_json = json.dumps(zip(rain_time_ms, rain_round))
        #print pob_rain_json
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Rain accumulation totals using the timespan. For static 1 day, look at POB archive above.
        #_pob_rain_totals_lookup = db_lookup().genSql( "SELECT dateTime, @total:=@total+rain AS total FROM archive, (SELECT @total:=0) AS t WHERE dateTime>=%s AND dateTime<=%s" % (_start_ts, timespan.stop) )
        #rain_time_ms = []
        #rain_round = []
        #rain_total = []
        #for rainsql in _pob_rain_totals_lookup:
        #    rain_time_ms.append(float(rainsql[0]) * 1000)
        #    rain_total.append( rainsql[1] )
            #rain_total.append( round(rainsql[1], 2) ) # Need to automate this from skin_dict?
        #Now that the dicts are built, do some rounding
        #rainRound_vt =  [roundNone(x,2) for x in rain_total]
        #pob_rain_total_json = json.dumps(zip(rain_time_ms, rainRound_vt))
        #pob_rain_total_json = json.dumps(zip(rain_time_ms, rain_total))
        #print pob_rain_total_json
        
        # Get our radiation vector
        #(time_start_vt, time_stop_vt, radiation_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                        'radiation')
        (time_start_vt, time_stop_vt, radiation_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'radiation', 'max', 86400)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        radiationRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "1f")[-2])
        # Do the rounding
        radiationRound_vt =  [roundNone(x,radiationRound) for x in radiation_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        radiation_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our insolation vector
        #(time_start_vt, time_stop_vt, insolation_vt) = db_lookup('wdsupp_binding').getSqlVectors(TimeSpan(_start_ts, timespan.stop),
        #                                                                                         'maxSolarRad')
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #insolationRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "1f")[-2])
        # Do the rounding
        #insolationRound_vt =  [roundNone(x,insolationRound) for x in insolation_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        #insolation_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # ARCHIVE CODE. MAY BE USED ONE DAY?
        # Get our UV vector
        #(time_start_vt, time_stop_vt, uv_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'UV')
        #(time_start_vt, time_stop_vt, uv_vt) = db_lookup().getSqlVectors(TimeSpan(_start_ts, timespan.stop), 'UV', 'max', 3600)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        #uvRound = int(self.generator.skin_dict['Units']['StringFormats'].get(uv_vt[2], "1f")[-2])
        # Do the rounding
        #uvRound_vt =  [roundNone(x,uvRound) for x in uv_vt[0]]
        # Get our time vector in ms (Highcharts requirement)
        # Need to do it for each getSqlVectors result as they might be different
        #UV_time_ms =  [float(x) * 1000 for x in time_stop_vt[0]]
        
        # Format our vectors in json format. Need the zip() to get time/value pairs
        # Assumes all vectors have the same number of elements
        outTemp_json = json.dumps(zip(outTemp_time_ms, outTempRound_vt))
        outTempMin_json = json.dumps(zip(outTempMin_time_ms, outTempMinRound_vt))
        dewpoint_json = json.dumps(zip(dewpoint_time_ms, dewpointRound_vt))
        #appTemp_json = json.dumps(zip(appTemp_time_ms, appTempRound_vt))
        windchill_json = json.dumps(zip(windchill_time_ms, windchillRound_vt))
        heatindex_json = json.dumps(zip(heatindex_time_ms, heatindexRound_vt))
        outHumidity_json = json.dumps(zip(outHumidity_time_ms, outHumidityRound_vt))
        barometer_json = json.dumps(zip(barometer_time_ms, barometerRound_vt))
        windSpeed_json = json.dumps(zip(windSpeed_time_ms, windSpeedRound_vt))
        windSpeedAvg_json = json.dumps(zip(windSpeed_time_ms, windSpeedAvgRound_vt))
        windGust_json = json.dumps(zip(windGust_time_ms, windGustRound_vt))
        windDir_json = json.dumps(zip(windDir_time_ms, windDirRound_vt))
        radiation_json = json.dumps(zip(radiation_time_ms, radiationRound_vt))
        #insolation_json = json.dumps(zip(insolation_time_ms, insolationRound_vt))
        #uv_json = json.dumps(zip(UV_time_ms, uvRound_vt))
        #rain_json = json.dumps(zip(timeRain_ms, rainRound_vt))
        
        # Put into a dictionary to return
        search_list_extension = {'outTempYearjson' : outTemp_json,
                                 'outTempMinYearjson' : outTempMin_json,
                                 'dewpointYearjson' : dewpoint_json,
                                 #'appTempYearjson' : appTemp_json,
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
                                 #'insolationYearjson' : insolation_json,
                                 #'uvYearjson' : uv_json,
                                 'YearPlotStart' : _start_ts * 1000,
                                 'YearPlotEnd' : timespan.stop * 1000}
        
        #t2 = time.time()
        #logdbg2("highchartsWeek SLE executed in %0.3f seconds" % (t2 - t1))

        # Return our json data
        return [search_list_extension]
        
    
class highchartsYear_original_archived(SearchList):

    def __init__(self, generator):
        SearchList.__init__(self, generator)

    def get_extension_list(self, timespan, db_lookup):

        # Do we have dedicated appTemp field or not? If so use it else revert to extraTemp2
        # as per original Weewx-WD schema
        sqlkeys = archivedb._getTypes()
        if 'appTemp' in sqlkeys:
            appTempKey = 'appTemp'
        elif 'extraTemp2' in sqlkeys:
            appTempKey = 'extraTemp2'
        # Our start time is midnight one year ago
        # Get a time object for midnight
        _mn_time = datetime.time(0)
        # Get a datetime object for our end datetime
        _day_date = datetime.datetime.fromtimestamp(valid_timespan.stop)
        # Calculate our start timestamp by combining date 1 year ago and midnight time
        _start_ts  = int(time.mktime(datetime.datetime.combine(get_ago(_day_date, -1, 0),_mn_time).timetuple()))
        # Get our temperature vector
        (time_vt, outTemp_vt) = archivedb.getSqlVectors('outTemp', _start_ts, valid_timespan.stop, 86400, 'avg')
        # Convert our temperature vector
        outTemp_vt = self.generator.converter.convert(outTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        tempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outTemp_vt[2], "1f")[-2])
        # Do the rounding
        outTempRound_vt =  [roundNone(x,tempRound) if x is not None else None for x in outTemp_vt[0]]
        # Get our dewpoint vector
        (time_vt, dewpoint_vt) = archivedb.getSqlVectors('dewpoint', _start_ts, valid_timespan.stop, 86400, 'avg')
        dewpoint_vt = self.generator.converter.convert(dewpoint_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        dewpointRound = int(self.generator.skin_dict['Units']['StringFormats'].get(dewpoint_vt[2], "1f")[-2])
        # Do the rounding
        dewpointRound_vt =  [roundNone(x,dewpointRound) if x is not None else None for x in dewpoint_vt[0]]
        # Get our apparent temperature vector
        (time_vt, appTemp_vt) = archivedb.getSqlVectors(appTempKey, _start_ts, valid_timespan.stop, 86400, 'avg')
        appTemp_vt = self.generator.converter.convert(appTemp_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        apptempRound = int(self.generator.skin_dict['Units']['StringFormats'].get(appTemp_vt[2], "1f")[-2])
        # Do the rounding
        appTempRound_vt =  [roundNone(x,apptempRound) if x is not None else None for x in appTemp_vt[0]]
        # Get our wind chill vector
        (time_vt, windchill_vt) = archivedb.getSqlVectors('windchill', _start_ts, valid_timespan.stop, 86400, 'avg')
        windchill_vt = self.generator.converter.convert(windchill_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windchillRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windchill_vt[2], "1f")[-2])
        # Do the rounding
        windchillRound_vt =  [roundNone(x,windchillRound) if x is not None else None for x in windchill_vt[0]]
        # Get our heat index vector
        (time_vt, heatindex_vt) = archivedb.getSqlVectors('heatindex', _start_ts, valid_timespan.stop, 86400, 'avg')
        heatindex_vt = self.generator.converter.convert(heatindex_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        heatindexRound = int(self.generator.skin_dict['Units']['StringFormats'].get(heatindex_vt[2], "1f")[-2])
        # Do the rounding
        heatindexRound_vt =  [roundNone(x,heatindexRound) if x is not None else None for x in heatindex_vt[0]]
        # Get our humidity vector
        (time_vt, outHumidity_vt) = archivedb.getSqlVectors('outHumidity', _start_ts, valid_timespan.stop, 86400, 'avg')
        # Get our barometer vector
        (time_vt, barometer_vt) = archivedb.getSqlVectors('barometer', _start_ts, valid_timespan.stop, 86400, 'avg')
        barometer_vt = self.generator.converter.convert(barometer_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        humidityRound = int(self.generator.skin_dict['Units']['StringFormats'].get(outHumidity_vt[2], "1f")[-2])
        # Do the rounding
        barometerRound_vt =  [roundNone(x,humidityRound) if x is not None else None for x in barometer_vt[0]]
        # Get our wind speed vector
        (time_vt, windSpeed_vt) = archivedb.getSqlVectors('windSpeed', _start_ts, valid_timespan.stop, 86400, 'avg')
        windSpeed_vt = self.generator.converter.convert(windSpeed_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windspeedRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windSpeed_vt[2], "1f")[-2])
        # Do the rounding
        windSpeedRound_vt =  [roundNone(x,windspeedRound) if x is not None else None for x in windSpeed_vt[0]]
        # Get our wind gust vector
        (time_vt, windGust_vt) = archivedb.getSqlVectors('windGust', _start_ts, valid_timespan.stop, 86400, 'avg')
        windGust_vt = self.generator.converter.convert(windGust_vt)
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        windgustRound = int(self.generator.skin_dict['Units']['StringFormats'].get(windGust_vt[2], "1f")[-2])
        # Do the rounding
        windGustRound_vt =  [roundNone(x,windgustRound) if x is not None else None for x in windGust_vt[0]]
        # Get our wind direction vector
        (time_vt, windDir_vt) = archivedb.getSqlVectors('windDir', _start_ts, valid_timespan.stop, 86400, 'avg')
        # Get our radiation vector
        (time_vt, radiation_vt) = archivedb.getSqlVectors('radiation', _start_ts, valid_timespan.stop, 86400, 'avg')
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        radiationRound = int(self.generator.skin_dict['Units']['StringFormats'].get(radiation_vt[2], "1f")[-2])
        # Do the rounding
        radiationRound_vt =  [roundNone(x,radiationRound) if x is not None else None for x in radiation_vt[0]]
        # Get our time vector in ms (highcharts requirement)
        time_ms =  [float(x) * 1000 for x in time_vt[0]]
        # Our rain vector uses calendar months so we need to do something different:
        # Use genMonthSpans to generate month spans and sum  from statsdb - quicker than archivedb
        # getAggregagte does not retunr a vector so we need to contruct our value tuples manually
        # Set up our 2 lists to hold our rain and time data
        rain_list = []
        timeRain_list = []
        # Call generator to give us month timespand from first record time to last record time
        for _month_timespan in genMonthSpans(_start_ts, valid_timespan.stop):
            # Get the total rain for the month
            _month_rain = statsdb.getAggregate(_month_timespan, 'rain', 'sum', None)
            # Append it to our rain data list
            rain_list.append(_month_rain[0])
            # Append the time to our time data list
            # Use timespan.start so thathighcharts tool tip displays correct month
            timeRain_list.append(_month_timespan.start)
        # Construct our time value tuple
        timeRain_vt = ValueTuple(timeRain_list, ['unix_epoch'], ['group_time'])
        # Construct our rain data value tuple and convert it
        rain_vt = self.generator.converter.convert(ValueTuple(rain_list, _month_rain[1], _month_rain[2]))
        # Can't use ValueHelper so round our results manually
        # Get the number of decimal points
        rainRound = int(self.generator.skin_dict['Units']['StringFormats'].get(rain_vt[2], "1f")[-2])
        # Do the rounding
        rainRound_vt =  [roundNone(x,rainRound) if x is not None else None for x in rain_vt[0]]
        # Get our time vector in ms (highcharts requirement)
        timeRain_ms =  [float(x) * 1000 for x in timeRain_vt[0]]
        # Format our vectors in json format. Need the zip() to get time/value pairs
        # Assumes all vectors have the same number of elements
        outTemp_json = json.dumps(zip(time_ms, outTempRound_vt))
        dewpoint_json = json.dumps(zip(time_ms, dewpointRound_vt))
        appTemp_json = json.dumps(zip(time_ms, appTempRound_vt))
        windchill_json = json.dumps(zip(time_ms, windchillRound_vt))
        heatindex_json = json.dumps(zip(time_ms, heatindexRound_vt))
        # Use 1st field in our original _vt as we did not round this one
        outHumidity_json = json.dumps(zip(time_ms, outHumidity_vt[0]))
        barometer_json = json.dumps(zip(time_ms, barometerRound_vt))
        windSpeed_json = json.dumps(zip(time_ms, windSpeedRound_vt))
        windGust_json = json.dumps(zip(time_ms, windGustRound_vt))
        # Use 1st field in our original _vt as we did not round this one
        windDir_json = json.dumps(zip(time_ms, windDir_vt[0]))
        radiation_json = json.dumps(zip(time_ms, radiationRound_vt))
        rain_json = json.dumps(zip(timeRain_ms, rainRound_vt))
        
        # Put into a dictionary to return
        search_list_extension = {'outTempYearjson' : outTemp_json,
                                 'dewpointYearjson' : dewpoint_json,
                                 'appTempYearjson' : appTemp_json,
                                 'windchillYearjson' : windchill_json,
                                 'heatindexYearjson' : heatindex_json,
                                 'outHumidityYearjson' : outHumidity_json,
                                 'barometerYearjson' : barometer_json,
                                 'windSpeedYearjson' : windSpeed_json,
                                 'windGustYearjson' : windGust_json,
                                 'windDirYearjson' : windDir_json,
                                 'rainYearjson' : rain_json,
                                 'radiationYearjson' : radiation_json}
        # Return our json data
        return [search_list_extension]
