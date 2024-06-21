"""
Extension for the Belchertown skin.
This extension builds search list extensions as well
as a crude "cron" to download necessary files.

Pat O'Brien, August 19, 2018
"""

from __future__ import print_function  # Python 2/3 compatibility
from __future__ import with_statement

import calendar
import datetime
import json
import locale
import os
import os.path
import sys
import syslog
import time
from collections import OrderedDict
from math import asin, atan2, cos, degrees, pi, radians, sin, sqrt
from re import match

import configobj

import weeutil.weeutil
import weewx
import weewx.reportengine
import weewx.station
import weewx.tags
import weewx.units
from weeutil.weeutil import (
    TimeSpan,
    archiveDaySpan,
    archiveMonthSpan,
    archiveSpanSpan,
    archiveWeekSpan,
    archiveYearSpan,
    isStartOfDay,
    startOfDay,
    to_bool,
    to_float,
    to_int,
)
from weewx.cheetahgenerator import SearchList
from weewx.tags import TimespanBinder

if sys.version_info[0] >= 3:
    from weeutil.config import search_up

# Check weewx version. Many things like search_up, weeutil.weeutil.KeyDict
# (label_dict) are from 3.9
if weewx.__version__ < "3.9":
    raise weewx.UnsupportedFeature(
        "weewx 3.9 and newer is required, found %s" % weewx.__version__
    )

if weewx.__version__ < "4":

    def logmsg(level, msg):
        syslog.syslog(level, "Belchertown Extension: %s" % msg)

    def logdbg(msg):
        logmsg(syslog.LOG_DEBUG, msg)

    def loginf(msg):
        logmsg(syslog.LOG_INFO, msg)

    def logerr(msg):
        logmsg(syslog.LOG_ERR, msg)

    from weeutil.weeutil import accumulateLeaves
    import syslog
else:
    # weewx 4.0+
    from weeutil.config import accumulateLeaves
    import weeutil.logger
    import logging

    log = logging.getLogger(__name__)

    def logdbg(msg):
        log.debug(msg)

    def loginf(msg):
        log.info(msg)

    def logerr(msg):
        log.error(msg)


# Print version in syslog for easier troubleshooting
VERSION = "1.3.1"
loginf("version %s" % VERSION)

# Define these as global so they can be used in both the search list extension
# and custom graphs section
aqi = ""
aqi_category = ""
aqi_time = 0
aqi_location = ""


class getData(SearchList):
    """
    Collect all custom data and calculations, then return search list extension
    """

    def __init__(self, generator):
        SearchList.__init__(self, generator)

    def get_gps_distance(self, pointA, pointB, distance_unit):
        """
        https://www.geeksforgeeks.org/program-distance-two-points-earth/ and
        https://stackoverflow.com/a/43960736 The math module contains a
        function named radians which converts from degrees to radians.
        """

        if not isinstance((pointA, pointB), tuple):
            raise TypeError("Only tuples are supported as arguments")
        lat1 = pointA[0]
        lon1 = pointA[1]
        lat2 = pointB[0]
        lon2 = pointB[1]
        # convert decimal degrees to radians
        lat1r, lon1r, lat2r, lon2r = map(radians, [lat1, lon1, lat2, lon2])
        # Haversine formula
        dlat = lat2r - lat1r
        dlon = lon2r - lon1r
        a = sin(dlat / 2) ** 2 + cos(lat1r) * cos(lat2r) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        # Radius of earth in kilometers is 6371. Use 3956 for miles
        if distance_unit == "km":
            r = 6371
        else:
            # Assume mile
            r = 3956
        bearing = self.get_gps_bearing(pointA, pointB)
        # Returns distance as object 0 and bearing as object 1
        return [(c * r), self.get_cardinal_direction(bearing), bearing]

    def get_gps_bearing(self, pointA, pointB):
        """
        https://gist.github.com/jeromer/2005586
        Calculates the bearing between two points.
        :Parameters:
          - pointA: The tuple representing the latitude/longitude for the
            first point. Latitude and longitude must be in decimal degrees
          - pointB: The tuple representing the latitude/longitude for the
            second point. Latitude and longitude must be in decimal degrees
        :Returns:
          The bearing in degrees
        :Returns Type:
          float
        """
        if not isinstance((pointA, pointB), tuple):
            raise TypeError("Only tuples are supported as arguments")
        lat1 = radians(pointA[0])
        lat2 = radians(pointB[0])
        diffLong = radians(pointB[1] - pointA[1])
        x = sin(diffLong) * cos(lat2)
        y = cos(lat1) * sin(lat2) - (sin(lat1) * cos(lat2) * cos(diffLong))
        initial_bearing = atan2(x, y)
        # Now we have the initial bearing but math.atan2 return values
        # from -180 to + 180 degrees which is not what we want for a compass bearing
        # The solution is to normalize the initial bearing as shown below
        initial_bearing = degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360
        return compass_bearing

    def get_cardinal_direction(self, degree, return_only_labels=False):
        default_ordinate_names = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
            "N/A",
        ]
        try:
            ordinate_names = weeutil.weeutil.option_as_list(
                self.generator.skin_dict["Units"]["Ordinates"]["directions"]
            )
        except KeyError:
            ordinate_names = default_ordinate_names

        if return_only_labels:
            return ordinate_names

        if 0 <= degree <= 11.25:
            return ordinate_names[0]
        if 11.26 <= degree <= 33.75:
            return ordinate_names[1]
        if 33.76 <= degree <= 56.25:
            return ordinate_names[2]
        if 56.26 <= degree <= 78.75:
            return ordinate_names[3]
        if 78.76 <= degree <= 101.25:
            return ordinate_names[4]
        if 101.26 <= degree <= 123.75:
            return ordinate_names[5]
        if 123.76 <= degree <= 146.25:
            return ordinate_names[6]
        if 146.26 <= degree <= 168.75:
            return ordinate_names[7]
        if 168.76 <= degree <= 191.25:
            return ordinate_names[8]
        if 191.26 <= degree <= 213.75:
            return ordinate_names[9]
        if 213.76 <= degree <= 236.25:
            return ordinate_names[10]
        if 236.26 <= degree <= 258.75:
            return ordinate_names[11]
        if 258.76 <= degree <= 281.25:
            return ordinate_names[12]
        if 281.26 <= degree <= 303.75:
            return ordinate_names[13]
        if 303.76 <= degree <= 326.25:
            return ordinate_names[14]
        if 326.26 <= degree <= 348.75:
            return ordinate_names[15]
        if 348.76 <= degree <= 360:
            return ordinate_names[0]

    def get_extension_list(self, timespan, db_lookup):
        """
        Build the data needed for the Belchertown skin
        """

        global aqi
        global aqi_category
        global aqi_time
        global aqi_location

        # Look for the debug flag which can be used to show more logging
        weewx.debug = int(self.generator.config_dict.get("debug", 0))

        # Setup label dict for text and titles
        try:
            d = self.generator.skin_dict["Labels"]["Generic"]
        except KeyError:
            d = {}
        label_dict = weeutil.weeutil.KeyDict(d)

        # Setup database manager
        binding = self.generator.config_dict["StdReport"].get(
            "data_binding", "wx_binding"
        )
        manager = self.generator.db_binder.get_manager(binding)

        belchertown_debug = self.generator.skin_dict["Extras"].get(
            "belchertown_debug", 0
        )

        # Find the right HTML ROOT
        if "HTML_ROOT" in self.generator.skin_dict:
            html_root = os.path.join(
                self.generator.config_dict["WEEWX_ROOT"],
                self.generator.skin_dict["HTML_ROOT"],
            )
        else:
            html_root = os.path.join(
                self.generator.config_dict["WEEWX_ROOT"],
                self.generator.config_dict["StdReport"]["HTML_ROOT"],
            )

        # Setup UTC offset hours for moment.js in index.html
        moment_js_stop_struct = time.localtime(time.time())
        moment_js_utc_offset = (
            calendar.timegm(moment_js_stop_struct)
            - calendar.timegm(time.gmtime(time.mktime(moment_js_stop_struct)))
        ) / 60

        try:
            moment_js_tz = self.generator.skin_dict["Units"]["TimeZone"].get("time_zone")
        except KeyError:
            moment_js_tz = ""

# Highcharts UTC offset is the opposite of normal. Positive values are
        # west, negative values are east of UTC.
        # https://api.highcharts.com/highcharts/time.timezoneOffset Multiplying
        # by -1 will reverse the number sign and keep 0 (not -0).
        # https://stackoverflow.com/a/14053631/1177153
        highcharts_timezoneoffset = moment_js_utc_offset * -1

        # If theme locale is auto, get the system locale for use with
        # moment.js, and the system decimal for use with highcharts
        if self.generator.skin_dict["Extras"]["belchertown_locale"] == "auto":
            system_locale, locale_encoding = locale.getdefaultlocale()
        else:
            try:
                # Try setting the locale. Locale needs to be in locale.encoding
                # format. Example: "en_US.UTF-8", or "de_DE.UTF-8"
                locale.setlocale(
                    locale.LC_ALL,
                    self.generator.skin_dict["Extras"]["belchertown_locale"],
                )
                system_locale, locale_encoding = locale.getlocale()
            except Exception as error:
                # The system can't find the locale requested, so just set the
                # variables anyways for JavaScript's use.
                system_locale, locale_encoding = self.generator.skin_dict["Extras"][
                    "belchertown_locale"
                ].split(".")
                if belchertown_debug:
                    logerr(
                        "Locale: Error using locale %s. "
                        "This locale may not be installed on your system and you may see unexpected results. "
                        "Belchertown skin JavaScript will try to use this locale. Full error: %s"
                        % (
                            self.generator.skin_dict["Extras"]["belchertown_locale"],
                            error,
                        )
                    )

        if system_locale is None:
            # Unable to determine locale. Fallback to en_US
            system_locale = "en_US"

        if locale_encoding is None:
            # Unable to determine locale_encoding. Fallback to UTF-8
            locale_encoding = "UTF-8"

        try:
            system_locale_js = system_locale.replace(
                "_", "-"
            )  # Python's locale is underscore. JS uses dashes.
        except:
            system_locale_js = "en-US"  # Error finding locale, set to en-US

        highcharts_decimal = self.generator.skin_dict["Extras"].get(
            "highcharts_decimal", None
        )
        # Change the Highcharts decimal to the locale if the option is missing
        # or on auto mode, otherwise use whats defined in Extras
        if highcharts_decimal is None or highcharts_decimal == "auto":
            try:
                highcharts_decimal = locale.localeconv()["decimal_point"]
            except:
                # Locale not found, default back to a period
                highcharts_decimal = "."

        highcharts_thousands = self.generator.skin_dict["Extras"].get(
            "highcharts_thousands", None
        )
        # Change the Highcharts thousands separator to the locale if the option
        # is missing or on auto mode, otherwise use whats defined in Extras
        if highcharts_thousands is None or highcharts_thousands == "auto":
            try:
                highcharts_thousands = locale.localeconv()["thousands_sep"]
            except:
                # Locale not found, default back to a comma
                highcharts_thousands = ","

        # Get the archive interval for the highcharts gapsize
        try:
            archive_interval_ms = (
                int(self.generator.config_dict["StdArchive"]["archive_interval"]) * 1000
            )
        except KeyError:
            archive_interval_ms = (
                300000  # 300*1000 for archive_interval emulated to millis
            )

        # Get the ordinal labels
        ordinate_names = self.get_cardinal_direction("", True)

        # Build the chart array for the HTML.  Outputs a dict of nested lists
        # which allow you to have different charts for different timespans on
        # the site in different order with different names.
        # OrderedDict([('day', ['chart1', 'chart2', 'chart3', 'chart4']),
        # ('week', ['chart1', 'chart5', 'chart6', 'chart2', 'chart3', 'chart4']),
        # ('month', ['this_is_chart1', 'chart2_is_here', 'chart3', 'windSpeed_and_windDir', 'chart5', 'chart6', 'chart7']),
        # ('year', ['chart1', 'chart2', 'chart3', 'chart4', 'chart5'])])
        chart_config_path = os.path.join(
            self.generator.config_dict["WEEWX_ROOT"],
            self.generator.skin_dict["SKIN_ROOT"],
            self.generator.skin_dict.get("skin", ""),
            "graphs.conf",
        )
        default_chart_config_path = os.path.join(
            self.generator.config_dict["WEEWX_ROOT"],
            self.generator.skin_dict["SKIN_ROOT"],
            self.generator.skin_dict.get("skin", ""),
            "graphs.conf.example",
        )
        if os.path.exists(chart_config_path):
            chart_dict = configobj.ConfigObj(chart_config_path, file_error=True)
        else:
            chart_dict = configobj.ConfigObj(default_chart_config_path, file_error=True)
        charts = OrderedDict()
        for chart_timespan in chart_dict.sections:
            timespan_chart_list = []
            for plotname in chart_dict[chart_timespan].sections:
                if plotname not in timespan_chart_list:
                    timespan_chart_list.append(plotname)
            charts[chart_timespan] = timespan_chart_list

        # Create a dict of chart group titles for use on the graphs page
        # header. If no title defined, use the chart group name
        graphpage_titles = OrderedDict()
        for chartgroup in chart_dict.sections:
            if "title" in chart_dict[chartgroup]:
                graphpage_titles[chartgroup] = chart_dict[chartgroup]["title"]
            else:
                graphpage_titles[chartgroup] = chartgroup

        # Create a dict of chart group page content for use on the graphs page
        # below the header.
        graphpage_content = OrderedDict()
        for chartgroup in chart_dict.sections:
            if "page_content" in chart_dict[chartgroup]:
                graphpage_content[chartgroup] = chart_dict[chartgroup]["page_content"]

        # Setup the Graphs page button row based on the skin extras option and
        # the button_text from graphs.conf
        graph_page_buttons = ""
        graph_page_graphgroup_buttons = []
        for chartgroup in chart_dict.sections:
            if (
                "show_button" in chart_dict[chartgroup]
                and chart_dict[chartgroup]["show_button"].lower() == "true"
            ):
                graph_page_graphgroup_buttons.append(chartgroup)
        for gg in graph_page_graphgroup_buttons:
            if "button_text" in chart_dict[gg]:
                button_text = chart_dict[gg]["button_text"]
            else:
                button_text = gg
            graph_page_buttons += (
                '<a href="./?graph='
                + gg
                + '"><button type="button" class="btn btn-primary">'
                + button_text
                + "</button></a>"
            )
            graph_page_buttons += " "  # Spacer between the button

        # Set a default radar URL using station's lat/lon. Moved from skin.conf
        # so we can get station lat/lon from weewx.conf. A lot of stations out
        # there with Belchertown 0.1 through 0.7 are showing the visitor's
        # location and not the proper station location because nobody edited
        # the radar_html which did not have lat/lon set previously.
        lat = self.generator.config_dict["Station"]["latitude"]
        lon = self.generator.config_dict["Station"]["longitude"]
        radar_width = self.generator.skin_dict["Extras"]["radar_width"]
        radar_height = self.generator.skin_dict["Extras"]["radar_height"]
        if "radar_zoom" in self.generator.skin_dict["Extras"]:
            zoom = self.generator.skin_dict["Extras"]["radar_zoom"]
        else:
            zoom = "8"
        if (
            "radar_marker" in self.generator.skin_dict["Extras"]
            and self.generator.skin_dict["Extras"]["radar_marker"] == "1"
        ):
            marker = "true"
        else:
            marker = ""

        # Set default radar html code, and override with user-specified value
        if self.generator.skin_dict["Extras"].get("radar_html") == "":
            if self.generator.skin_dict["Extras"].get("aeris_map") == "1":
                radar_html = '<img style="object-fit:cover;width:{}px;height:{}px" src="https://maps.aerisapi.com/{}_{}/flat,water-depth,counties:60,rivers,interstates:60,admin-cities,alerts-severe:50:blend(darken),radar:blend(darken)/{}x{}/{},{},{}/current.png"></img>'.format(
                    radar_width,
                    radar_height,
                    self.generator.skin_dict["Extras"]["forecast_api_id"],
                    self.generator.skin_dict["Extras"]["forecast_api_secret"],
                    radar_width,
                    radar_height,
                    lat,
                    lon,
                    zoom,
                )
            else:
                radar_html = '<iframe width="{}px" height="{}px" src="https://embed.windy.com/embed2.html?lat={}&lon={}&zoom={}&level=surface&overlay=radar&menu=&message=true&marker={}&calendar=&pressure=&type=map&location=coordinates&detail=&detailLat={}&detailLon={}&metricWind=&metricTemp=&radarRange=-1" frameborder="0"></iframe>'.format(
                    radar_width, radar_height, lat, lon, zoom, marker, lat, lon
                )
        else:
            radar_html = self.generator.skin_dict["Extras"]["radar_html"]

        if self.generator.skin_dict["Extras"].get("radar_html_dark") == "":
            if self.generator.skin_dict["Extras"].get("aeris_map") == "1":
                radar_html_dark = '<img style="object-fit:cover;width:{}px;height:{}px" src="https://maps.aerisapi.com/{}_{}/flat-dk,water-depth-dk,counties:60,rivers,interstates:60,admin-cities-dk,alerts-severe:50:blend(lighten),radar:blend(lighten)/{}x{}/{},{},{}/current.png"></img>'.format(
                    radar_width,
                    radar_height,
                    self.generator.skin_dict["Extras"]["forecast_api_id"],
                    self.generator.skin_dict["Extras"]["forecast_api_secret"],
                    radar_width,
                    radar_height,
                    lat,
                    lon,
                    zoom,
                )
            else:
                radar_html_dark = "None"
        else:
            radar_html_dark = self.generator.skin_dict["Extras"]["radar_html_dark"]

        # If the kiosk radar is different then the homepage one.
        if self.generator.skin_dict["Extras"].get("radar_html_kiosk") == "":
            radar_html_kiosk = radar_html
        else:
            radar_width_kiosk = self.generator.skin_dict["Extras"]["radar_width_kiosk"]
            radar_height_kiosk = self.generator.skin_dict["Extras"]["radar_height_kiosk"]
            radar_html_kiosk = '<iframe width="{}px" height="{}px" src="{}" frameborder="0"></iframe>'.format(
                radar_width_kiosk,
                radar_height_kiosk,
                self.generator.skin_dict["Extras"]["radar_html_kiosk"]
            )


        # ==============================================================================
        # Build the all time stats.
        # ==============================================================================

        wx_manager = db_lookup()

        # Find the beginning of the current year
        now = datetime.datetime.now()
        date_time = "01/01/%s 00:00:00" % now.year
        pattern = "%m/%d/%Y %H:%M:%S"
        year_start_epoch = int(time.mktime(time.strptime(date_time, pattern)))

        date_time = "%s/%s/%s 00:00:00" % (now.month, now.day, now.year)
        today_start_epoch = int(time.mktime(time.strptime(date_time, pattern)))

        # Setup the converter
        # Get the target unit nickname (something like 'US' or 'METRIC'):
        target_unit_nickname = self.generator.config_dict["StdConvert"]["target_unit"]
        # Get the target unit: weewx.US, weewx.METRIC, weewx.METRICWX
        target_unit = weewx.units.unit_constants[target_unit_nickname.upper()]
        # Bind to the appropriate standard converter units
        converter = weewx.units.StdUnitConverters[target_unit]

        # Temperature Range Lookups

        # 1. The database query finds the result based off the total column.
        # 2. We need to convert the min, max to the site's requested unit.
        # 3. We need to recalculate the min/max range because the unit may have changed.

        year_outTemp_max_range_query = wx_manager.getSql(
            "SELECT dateTime, ROUND( (max - min), 1 ) as total, ROUND( min, 1 ) as min, ROUND( max, 1 ) as max FROM archive_day_outTemp WHERE dateTime >= %s AND dateTime < %s AND min IS NOT NULL AND max IS NOT NULL ORDER BY total DESC LIMIT 1;"
            % (year_start_epoch, today_start_epoch)
        )
        year_outTemp_min_range_query = wx_manager.getSql(
            "SELECT dateTime, ROUND( (max - min), 1 ) as total, ROUND( min, 1 ) as min, ROUND( max, 1 ) as max FROM archive_day_outTemp WHERE dateTime >= %s AND dateTime < %s AND min IS NOT NULL AND max IS NOT NULL ORDER BY total ASC LIMIT 1;"
            % (year_start_epoch, today_start_epoch)
        )
        at_outTemp_max_range_query = wx_manager.getSql(
            "SELECT dateTime, ROUND( (max - min), 1 ) as total, ROUND( min, 1 ) as min, ROUND( max, 1 ) as max FROM archive_day_outTemp WHERE dateTime < %s AND min IS NOT NULL AND max IS NOT NULL ORDER BY total DESC LIMIT 1;"
            % today_start_epoch
        )
        at_outTemp_min_range_query = wx_manager.getSql(
            "SELECT dateTime, ROUND( (max - min), 1 ) as total, ROUND( min, 1 ) as min, ROUND( max, 1 ) as max FROM archive_day_outTemp WHERE dateTime < %s AND min IS NOT NULL AND max IS NOT NULL ORDER BY total ASC LIMIT 1;"
            % today_start_epoch
        )

        # Find the group_name for outTemp in database
        outTemp_unit = converter.group_unit_dict["group_temperature"]

        # Find the group_name for outTemp from the skin.conf
        skin_outTemp_unit = self.generator.converter.group_unit_dict[
            "group_temperature"
        ]

        # Find the number of decimals to round to based on the skin.conf
        outTemp_round = self.generator.skin_dict["Units"]["StringFormats"].get(
            skin_outTemp_unit, "%.1f"
        )

        # Largest Daily Temperature Range Conversions
        # Max temperature for this day
        if year_outTemp_max_range_query is not None:
            year_outTemp_max_range_max_tuple = (
                year_outTemp_max_range_query[3],
                outTemp_unit,
                "group_temperature",
            )
            year_outTemp_max_range_max = (
                outTemp_round
                % self.generator.converter.convert(year_outTemp_max_range_max_tuple)[0]
            )
            # Min temperature for this day
            year_outTemp_max_range_min_tuple = (
                year_outTemp_max_range_query[2],
                outTemp_unit,
                "group_temperature",
            )
            year_outTemp_max_range_min = (
                outTemp_round
                % self.generator.converter.convert(year_outTemp_max_range_min_tuple)[0]
            )
            # Largest Daily Temperature Range total
            year_outTemp_max_range_total = outTemp_round % (
                float(year_outTemp_max_range_max) - float(year_outTemp_max_range_min)
            )
            # Replace the SQL Query output with the converted values
            year_outTemp_range_max = [
                year_outTemp_max_range_query[0],
                locale.format_string("%g", float(year_outTemp_max_range_total)),
                locale.format_string("%g", float(year_outTemp_max_range_min)),
                locale.format_string("%g", float(year_outTemp_max_range_max)),
            ]
        else:
            year_outTemp_range_max = [
                calendar.timegm(time.gmtime()),
                locale.format_string("%.1f", 0),
                locale.format_string("%.1f", 0),
                locale.format_string("%.1f", 0),
            ]

        # Smallest Daily Temperature Range Conversions
        # Max temperature for this day
        if year_outTemp_min_range_query is not None:
            year_outTemp_min_range_max_tuple = (
                year_outTemp_min_range_query[3],
                outTemp_unit,
                "group_temperature",
            )
            year_outTemp_min_range_max = (
                outTemp_round
                % self.generator.converter.convert(year_outTemp_min_range_max_tuple)[0]
            )
            # Min temperature for this day
            year_outTemp_min_range_min_tuple = (
                year_outTemp_min_range_query[2],
                outTemp_unit,
                "group_temperature",
            )
            year_outTemp_min_range_min = (
                outTemp_round
                % self.generator.converter.convert(year_outTemp_min_range_min_tuple)[0]
            )
            # Smallest Daily Temperature Range total
            year_outTemp_min_range_total = outTemp_round % (
                float(year_outTemp_min_range_max) - float(year_outTemp_min_range_min)
            )
            # Replace the SQL Query output with the converted values
            year_outTemp_range_min = [
                year_outTemp_min_range_query[0],
                locale.format_string("%g", float(year_outTemp_min_range_total)),
                locale.format_string("%g", float(year_outTemp_min_range_min)),
                locale.format_string("%g", float(year_outTemp_min_range_max)),
            ]
        else:
            year_outTemp_range_min = [
                calendar.timegm(time.gmtime()),
                locale.format_string("%.1f", 0),
                locale.format_string("%.1f", 0),
                locale.format_string("%.1f", 0),
            ]

        # All Time - Largest Daily Temperature Range Conversions
        # Max temperature
        if at_outTemp_max_range_query is not None:
            at_outTemp_max_range_max_tuple = (
                at_outTemp_max_range_query[3],
                outTemp_unit,
                "group_temperature",
            )
            at_outTemp_max_range_max = (
                outTemp_round
                % self.generator.converter.convert(at_outTemp_max_range_max_tuple)[0]
            )
            # Min temperature for this day
            at_outTemp_max_range_min_tuple = (
                at_outTemp_max_range_query[2],
                outTemp_unit,
                "group_temperature",
            )
            at_outTemp_max_range_min = (
                outTemp_round
                % self.generator.converter.convert(at_outTemp_max_range_min_tuple)[0]
            )
            # Largest Daily Temperature Range total
            at_outTemp_max_range_total = outTemp_round % (
                float(at_outTemp_max_range_max) - float(at_outTemp_max_range_min)
            )
            # Replace the SQL Query output with the converted values
            at_outTemp_range_max = [
                at_outTemp_max_range_query[0],
                locale.format_string("%g", float(at_outTemp_max_range_total)),
                locale.format_string("%g", float(at_outTemp_max_range_min)),
                locale.format_string("%g", float(at_outTemp_max_range_max)),
            ]
        else:
            at_outTemp_range_max = [
                calendar.timegm(time.gmtime()),
                locale.format_string("%.1f", 0),
                locale.format_string("%.1f", 0),
                locale.format_string("%.1f", 0),
            ]

        # All Time - Smallest Daily Temperature Range Conversions
        # Max temperature for this day
        if at_outTemp_min_range_query is not None:
            at_outTemp_min_range_max_tuple = (
                at_outTemp_min_range_query[3],
                outTemp_unit,
                "group_temperature",
            )
            at_outTemp_min_range_max = (
                outTemp_round
                % self.generator.converter.convert(at_outTemp_min_range_max_tuple)[0]
            )
            # Min temperature for this day
            at_outTemp_min_range_min_tuple = (
                at_outTemp_min_range_query[2],
                outTemp_unit,
                "group_temperature",
            )
            at_outTemp_min_range_min = (
                outTemp_round
                % self.generator.converter.convert(at_outTemp_min_range_min_tuple)[0]
            )
            # Smallest Daily Temperature Range total
            at_outTemp_min_range_total = outTemp_round % (
                float(at_outTemp_min_range_max) - float(at_outTemp_min_range_min)
            )
            # Replace the SQL Query output with the converted values
            at_outTemp_range_min = [
                at_outTemp_min_range_query[0],
                locale.format_string("%g", float(at_outTemp_min_range_total)),
                locale.format_string("%g", float(at_outTemp_min_range_min)),
                locale.format_string("%g", float(at_outTemp_min_range_max)),
            ]
        else:
            at_outTemp_range_min = [
                calendar.timegm(time.gmtime()),
                locale.format_string("%.1f", 0),
                locale.format_string("%.1f", 0),
                locale.format_string("%.1f", 0),
            ]

        # Rain lookups
        # Find the group_name for rain in database
        rain_unit = converter.group_unit_dict["group_rain"]

        # Find the group_name for rain in the skin.conf
        skin_rain_unit = self.generator.converter.group_unit_dict["group_rain"]

        # Find the number of decimals to round the result based on the skin.conf
        rain_round = self.generator.skin_dict["Units"]["StringFormats"].get(
            skin_rain_unit, "%.2f"
        )

        # Rainiest Day
        rainiest_day_query = wx_manager.getSql(
            "SELECT dateTime, sum FROM archive_day_rain WHERE dateTime >= %s ORDER BY sum DESC LIMIT 1;"
            % year_start_epoch
        )
        if rainiest_day_query is not None:
            rainiest_day_tuple = (rainiest_day_query[1], rain_unit, "group_rain")
            rainiest_day_converted = (
                rain_round % self.generator.converter.convert(rainiest_day_tuple)[0]
            )
            rainiest_day = [
                rainiest_day_query[0],
                locale.format_string("%g", float(rainiest_day_converted)),
            ]
        else:
            rainiest_day = [calendar.timegm(time.gmtime()), locale.format_string("%.2f", 0)]

        # All Time Rainiest Day
        at_rainiest_day_query = wx_manager.getSql(
            "SELECT dateTime, sum FROM archive_day_rain ORDER BY sum DESC LIMIT 1"
        )
        at_rainiest_day_tuple = (at_rainiest_day_query[1], rain_unit, "group_rain")
        at_rainiest_day_converted = (
            rain_round % self.generator.converter.convert(at_rainiest_day_tuple)[0]
        )
        at_rainiest_day = [
            at_rainiest_day_query[0],
            locale.format_string("%g", float(at_rainiest_day_converted)),
        ]

        # Find what kind of database we're working with and specify the
        # correctly tailored SQL Query for each type of database
        data_binding = self.generator.config_dict["StdArchive"]["data_binding"]
        database = self.generator.config_dict["DataBindings"][data_binding]["database"]
        database_type = self.generator.config_dict["Databases"][database][
            "database_type"
        ]
        driver = self.generator.config_dict["DatabaseTypes"][database_type]["driver"]
        if driver == "weedb.sqlite":
            year_rainiest_month_sql = (
                'SELECT strftime("%%m", datetime(dateTime, "unixepoch", "localtime")) as month, SUM( sum ) as total FROM archive_day_rain WHERE strftime("%%Y", datetime(dateTime, "unixepoch", "localtime")) = "%s" GROUP BY month ORDER BY total DESC LIMIT 1;'
                % time.strftime("%Y", time.localtime(time.time()))
            )
            at_rainiest_month_sql = 'SELECT strftime("%m", datetime(dateTime, "unixepoch", "localtime")) as month, strftime("%Y", datetime(dateTime, "unixepoch", "localtime")) as year, SUM( sum ) as total FROM archive_day_rain GROUP BY month, year ORDER BY total DESC LIMIT 1;'
            year_rain_data_sql = (
                'SELECT dateTime, sum FROM archive_day_rain WHERE strftime("%%Y", datetime(dateTime, "unixepoch", "localtime")) = "%s" AND count > 0;'
                % time.strftime("%Y", time.localtime(time.time()))
            )
            # The all stats from http://www.weewx.com/docs/customizing.htm
            # doesn't seem to calculate "Total Rainfall for" all time stat
            # correctly.
            at_rain_highest_year_sql = 'SELECT strftime("%Y", datetime(dateTime, "unixepoch", "localtime")) as year, SUM( sum ) as total FROM archive_day_rain GROUP BY year ORDER BY total DESC LIMIT 1;'
        elif driver == "weedb.mysql":
            year_rainiest_month_sql = 'SELECT FROM_UNIXTIME( dateTime, "%%m" ) AS month, ROUND( SUM( sum ), 2 ) AS total FROM archive_day_rain WHERE year( FROM_UNIXTIME( dateTime ) ) = "{0}" GROUP BY month ORDER BY total DESC LIMIT 1;'.format(
                time.strftime("%Y", time.localtime(time.time()))
            )  # Why does this one require .format() but the other's don't?
            at_rainiest_month_sql = 'SELECT FROM_UNIXTIME( dateTime, "%%m" ) AS month, FROM_UNIXTIME( dateTime, "%%Y" ) AS year, ROUND( SUM( sum ), 2 ) AS total FROM archive_day_rain GROUP BY month, year ORDER BY total DESC LIMIT 1;'
            year_rain_data_sql = (
                'SELECT dateTime, ROUND( sum, 2 ) FROM archive_day_rain WHERE year( FROM_UNIXTIME( dateTime ) ) = "%s" AND count > 0;'
                % time.strftime("%Y", time.localtime(time.time()))
            )
            # The all stats from http://www.weewx.com/docs/customizing.htm
            # doesn't seem to calculate "Total Rainfall for" all time stat
            # correctly.
            at_rain_highest_year_sql = 'SELECT FROM_UNIXTIME( dateTime, "%%Y" ) AS year, ROUND( SUM( sum ), 2 ) AS total FROM archive_day_rain GROUP BY year ORDER BY total DESC LIMIT 1;'

        # Rainiest month
        year_rainiest_month_query = wx_manager.getSql(year_rainiest_month_sql)
        if year_rainiest_month_query is not None:
            year_rainiest_month_tuple = (
                year_rainiest_month_query[1],
                rain_unit,
                "group_rain",
            )
            year_rainiest_month_converted = (
                rain_round
                % self.generator.converter.convert(year_rainiest_month_tuple)[0]
            )
            year_rainiest_month_name = calendar.month_name[
                int(year_rainiest_month_query[0])
            ]
            year_rainiest_month = [
                year_rainiest_month_name,
                locale.format_string("%g", float(year_rainiest_month_converted)),
            ]
        else:
            year_rainiest_month = ["N/A", 0.0]

        # All time rainiest month
        at_rainiest_month_query = wx_manager.getSql(at_rainiest_month_sql)
        at_rainiest_month_tuple = (at_rainiest_month_query[2], rain_unit, "group_rain")
        at_rainiest_month_converted = (
            rain_round % self.generator.converter.convert(at_rainiest_month_tuple)[0]
        )
        at_rainiest_month_name = calendar.month_name[int(at_rainiest_month_query[0])]
        at_rainiest_month = [
            "%s, %s" % (at_rainiest_month_name, at_rainiest_month_query[1]),
            locale.format_string("%g", float(at_rainiest_month_converted)),
        ]

        # All time rainiest year
        at_rain_highest_year_query = wx_manager.getSql(at_rain_highest_year_sql)
        at_rain_highest_year_tuple = (
            at_rain_highest_year_query[1],
            rain_unit,
            "group_rain",
        )
        at_rain_highest_year_converted = (
            rain_round % self.generator.converter.convert(at_rain_highest_year_tuple)[0]
        )
        at_rain_highest_year = [
            at_rain_highest_year_query[0],
            locale.format_string("%g", float(at_rain_highest_year_converted)),
        ]

        # Consecutive days with/without rainfall
        # dateTime needs to be epoch. Conversion done in the template using #echo
        year_days_with_rain_total = 0
        year_days_without_rain_total = 0
        year_days_with_rain_output = {}
        year_days_without_rain_output = {}
        year_rain_query = wx_manager.genSql(year_rain_data_sql)
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
            year_days_with_rain = max(
                zip(
                    year_days_with_rain_output.values(),
                    year_days_with_rain_output.keys(),
                )
            )
        else:
            year_days_with_rain = [
                locale.format_string("%.1f", 0),
                calendar.timegm(time.gmtime()),
            ]

        if year_days_without_rain_output:
            year_days_without_rain = max(
                zip(
                    year_days_without_rain_output.values(),
                    year_days_without_rain_output.keys(),
                )
            )
        else:
            year_days_without_rain = [
                locale.format_string("%.1f", 0),
                calendar.timegm(time.gmtime()),
            ]

        at_days_with_rain_total = 0
        at_days_without_rain_total = 0
        at_days_with_rain_output = {}
        at_days_without_rain_output = {}
        at_rain_query = wx_manager.genSql(
            "SELECT dateTime, ROUND( sum, 2 ) FROM archive_day_rain WHERE count > 0;"
        )
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

        if len(at_days_with_rain_output) > 0:
            at_days_with_rain = max(
                zip(at_days_with_rain_output.values(), at_days_with_rain_output.keys())
            )
        else:
            at_days_with_rain = (0, 0)
        if len(at_days_without_rain_output) > 0:
            at_days_without_rain = max(
                zip(
                    at_days_without_rain_output.values(),
                    at_days_without_rain_output.keys(),
                )
            )
        else:
            at_days_without_rain = (0, 0)

        # This portion is right from the weewx sample
        # http://www.weewx.com/docs/customizing.htm

        all_stats = TimespanBinder(
            timespan,
            db_lookup,
            formatter=self.generator.formatter,
            converter=self.generator.converter,
            skin_dict=self.generator.skin_dict,
        )

        # Get the unit label from the skin dict for speed.
        windSpeed_unit = self.generator.skin_dict["Units"]["Groups"]["group_speed"]
        windSpeed_unit_label = self.generator.skin_dict["Units"]["Labels"][
            windSpeed_unit
        ]

        # ==============================================================================
        # Get NOAA Data
        # ==============================================================================
        years = []
        noaa_header_html = ""
        default_noaa_file = ""
        noaa_dir = html_root + "/NOAA/"

        try:
            noaa_file_list = os.listdir(noaa_dir)

            # Generate a list of years based on file name
            for f in noaa_file_list:
                filename = f.split(".")[0]  # Drop the .txt
                year = filename.split("-")[1]
                years.append(year)

            # Remove duplicates with set, and sort numerically, then reverse
            # sort with [::-1] oldest year last
            # first_year = years[0]
            # final_year = years[-1]
            years = sorted(set(years))[::-1]

            for y in years:
                # Link to the year file
                if os.path.exists(noaa_dir + "NOAA-%s.txt" % y):
                    noaa_header_html += (
                        '<a href="?yr=%s" class="noaa_rep_nav"><b>%s</b></a>:' % (y, y)
                    )
                else:
                    noaa_header_html += (
                        '<span class="noaa_rep_nav"><b>%s</b></span>:' % y
                    )

                # Loop through all 12 months and find if the file exists.  If
                # the file doesn't exist, just show the month name in the
                # header without a href link.  There is no month 13, but we
                # need to loop to 12, so 13 is where it stops.
                for i in range(1, 13):
                    month_num = format(
                        i, "02"
                    )  # Pad the number with a 0 since the NOAA files use 2 digit month
                    month_abbr = calendar.month_abbr[i]
                    if os.path.exists(noaa_dir + "NOAA-%s-%s.txt" % (y, month_num)):
                        noaa_header_html += (
                            ' <a href="?yr=%s&amp;mo=%s" class="noaa_rep_nav"><b>%s</b></a>'
                            % (y, month_num, month_abbr)
                        )
                    else:
                        noaa_header_html += (
                            ' <span class="noaa_rep_nav"><b>%s</b></span>' % month_abbr
                        )

                # Row build complete, push next row to new line
                noaa_header_html += "<br>"

            # Find the current month's NOAA file for the default file to show
            # on JavaScript page load.  The NOAA files are generated as part of
            # this skin, but if for some reason that the month file doesn't
            # exist, use the year file.
            now = datetime.datetime.now()
            current_year = str(now.year)
            current_month = str(format(now.month, "02"))
            if os.path.exists(
                noaa_dir + "NOAA-%s-%s.txt" % (current_year, current_month)
            ):
                default_noaa_file = "NOAA-%s-%s.txt" % (current_year, current_month)
            else:
                default_noaa_file = "NOAA-%s.txt" % current_year
        except:
            # There's an error - I've seen this on first run and the NOAA
            # folder is not created yet. Skip this section.
            pass

        # ==============================================================================
        # Forecast Data
        # ==============================================================================

        if (
            self.generator.skin_dict["Extras"]["forecast_enabled"] == "1"
            and self.generator.skin_dict["Extras"]["forecast_api_id"] != ""
            or "forecast_dev_file" in self.generator.skin_dict["Extras"]
        ):

            forecast_file = html_root + "/json/forecast.json"
            forecast_api_id = self.generator.skin_dict["Extras"]["forecast_api_id"]
            forecast_api_secret = self.generator.skin_dict["Extras"][
                "forecast_api_secret"
            ]
            forecast_units = self.generator.skin_dict["Extras"][
                "forecast_units"
            ].lower()
            latitude = self.generator.config_dict["Station"]["latitude"]
            longitude = self.generator.config_dict["Station"]["longitude"]
            forecast_stale_timer = self.generator.skin_dict["Extras"]["forecast_stale"]
            forecast_is_stale = False

            def aeris_coded_weather(data):
                # https://www.aerisweather.com/support/docs/api/reference/weather-codes/
                output = ""
                coverage_code = data.split(":")[0]
                intensity_code = data.split(":")[1]
                weather_code = data.split(":")[2]

                cloud_dict = {
                    "CL": label_dict["forecast_cloud_code_CL"],
                    "FW": label_dict["forecast_cloud_code_FW"],
                    "SC": label_dict["forecast_cloud_code_SC"],
                    "BK": label_dict["forecast_cloud_code_BK"],
                    "OV": label_dict["forecast_cloud_code_OV"],
                }

                coverage_dict = {
                    "AR": label_dict["forecast_coverage_code_AR"],
                    "BR": label_dict["forecast_coverage_code_BR"],
                    "C": label_dict["forecast_coverage_code_C"],
                    "D": label_dict["forecast_coverage_code_D"],
                    "FQ": label_dict["forecast_coverage_code_FQ"],
                    "IN": label_dict["forecast_coverage_code_IN"],
                    "IS": label_dict["forecast_coverage_code_IS"],
                    "L": label_dict["forecast_coverage_code_L"],
                    "NM": label_dict["forecast_coverage_code_NM"],
                    "O": label_dict["forecast_coverage_code_O"],
                    "PA": label_dict["forecast_coverage_code_PA"],
                    "PD": label_dict["forecast_coverage_code_PD"],
                    "S": label_dict["forecast_coverage_code_S"],
                    "SC": label_dict["forecast_coverage_code_SC"],
                    "VC": label_dict["forecast_coverage_code_VC"],
                    "WD": label_dict["forecast_coverage_code_WD"],
                }

                intensity_dict = {
                    "VL": label_dict["forecast_intensity_code_VL"],
                    "L": label_dict["forecast_intensity_code_L"],
                    "H": label_dict["forecast_intensity_code_H"],
                    "VH": label_dict["forecast_intensity_code_VH"],
                }

                weather_dict = {
                    "A": label_dict["forecast_weather_code_A"],
                    "BD": label_dict["forecast_weather_code_BD"],
                    "BN": label_dict["forecast_weather_code_BN"],
                    "BR": label_dict["forecast_weather_code_BR"],
                    "BS": label_dict["forecast_weather_code_BS"],
                    "BY": label_dict["forecast_weather_code_BY"],
                    "F": label_dict["forecast_weather_code_F"],
                    "FR": label_dict["forecast_weather_code_FR"],
                    "H": label_dict["forecast_weather_code_H"],
                    "IC": label_dict["forecast_weather_code_IC"],
                    "IF": label_dict["forecast_weather_code_IF"],
                    "IP": label_dict["forecast_weather_code_IP"],
                    "K": label_dict["forecast_weather_code_K"],
                    "L": label_dict["forecast_weather_code_L"],
                    "R": label_dict["forecast_weather_code_R"],
                    "RW": label_dict["forecast_weather_code_RW"],
                    "RS": label_dict["forecast_weather_code_RS"],
                    "SI": label_dict["forecast_weather_code_SI"],
                    "WM": label_dict["forecast_weather_code_WM"],
                    "S": label_dict["forecast_weather_code_S"],
                    "SW": label_dict["forecast_weather_code_SW"],
                    "T": label_dict["forecast_weather_code_T"],
                    "UP": label_dict["forecast_weather_code_UP"],
                    "VA": label_dict["forecast_weather_code_VA"],
                    "WP": label_dict["forecast_weather_code_WP"],
                    "ZF": label_dict["forecast_weather_code_ZF"],
                    "ZL": label_dict["forecast_weather_code_ZL"],
                    "ZR": label_dict["forecast_weather_code_ZR"],
                    "ZY": label_dict["forecast_weather_code_ZY"],
                }

                # Check if the weather_code is in the cloud_dict and use that
                # if it's there. If not then it's a combined weather code.
                if weather_code in cloud_dict:
                    return cloud_dict[weather_code]

                # Add the coverage if it's present, and full observation
                # forecast is requested
                if coverage_code:
                    output += coverage_dict[coverage_code] + " "
                # Add the intensity if it's present
                if intensity_code:
                    output += intensity_dict[intensity_code] + " "
                # Weather output
                output += weather_dict[weather_code]
                return output

            def aeris_icon(data):
                # https://www.aerisweather.com/support/docs/api/reference/icon-list/
                iconlist_file_path = os.path.join(
                    self.generator.config_dict["WEEWX_ROOT"],
                    self.generator.skin_dict["SKIN_ROOT"],
                    self.generator.skin_dict.get("skin", ""),
                    "images/aeris-icon-list.json",
                )
                if os.path.exists(iconlist_file_path):
                    icon_name = data.split(".")[0]  # Remove .png
                    with open(iconlist_file_path, "r") as dict:
                        icon_dict = json.load(dict)
                    return icon_dict[icon_name]
                else:
                    logerr("aeris-icon-list.json is missing in " + iconlist_file_path)
                    return 'unknown'

            forecast_lang = self.generator.skin_dict["Extras"]["forecast_lang"].lower()
            if self.generator.skin_dict["Extras"]["forecast_aeris_use_metar"] == "1":
                forecast_current_url = (
                    "https://api.aerisapi.com/observations/%s,%s?&format=json&filter=allstations&filter=metar&limit=1&client_id=%s&client_secret=%s"
                    % (latitude, longitude, forecast_api_id, forecast_api_secret)
                )
            else:
                forecast_current_url = (
                    "https://api.aerisapi.com/observations/%s,%s?&format=json&filter=allstations&limit=1&client_id=%s&client_secret=%s"
                    % (latitude, longitude, forecast_api_id, forecast_api_secret)
                )
            forecast_24hr_url = (
                "https://api.aerisapi.com/forecasts/%s,%s?&format=json&filter=day&limit=7&client_id=%s&client_secret=%s"
                % (latitude, longitude, forecast_api_id, forecast_api_secret)
            )
            forecast_3hr_url = (
                "https://api.aerisapi.com/forecasts/%s,%s?&format=json&filter=3hr&limit=8&client_id=%s&client_secret=%s"
                % (latitude, longitude, forecast_api_id, forecast_api_secret)
            )
            forecast_1hr_url = (
                "https://api.aerisapi.com/forecasts/%s,%s?&format=json&filter=1hr&limit=16&client_id=%s&client_secret=%s"
                % (latitude, longitude, forecast_api_id, forecast_api_secret)
            )
            aqi_url = (
                "https://api.aerisapi.com/airquality/closest?p=%s,%s&format=json&radius=50mi&limit=1&client_id=%s&client_secret=%s"
                % (latitude, longitude, forecast_api_id, forecast_api_secret)
            )
            if self.generator.skin_dict["Extras"]["forecast_alert_limit"]:
                forecast_alert_limit = self.generator.skin_dict["Extras"][
                    "forecast_alert_limit"
                ]
                forecast_alerts_url = "https://api.aerisapi.com/alerts/%s,%s?&format=json&limit=%s&lang=%s&client_id=%s&client_secret=%s" % (
                    latitude,
                    longitude,
                    forecast_alert_limit,
                    forecast_lang,
                    forecast_api_id,
                    forecast_api_secret,
                )
            else:
                # Default to 1 alerts to show if the option is missing. Can go up to 10
                forecast_alerts_url = "https://api.aerisapi.com/alerts/%s,%s?&format=json&limit=1&lang=%s&client_id=%s&client_secret=%s" % (
                    latitude,
                    longitude,
                    forecast_lang,
                    forecast_api_id,
                    forecast_api_secret,
                )

            # Determine if the file exists and get it's modified time, enhanced
            # for 1 hr forecast to load close to the hour
            if os.path.isfile(forecast_file):
                if (int(time.time()) - int(os.path.getmtime(forecast_file))) > int(
                    forecast_stale_timer
                ):
                    forecast_is_stale = True
                else:
                    # catches repeated calls every archive interval (300secs)
                    if (
                        time.strftime("%M") < "05"
                        and int(time.time()) - int(os.path.getmtime(forecast_file))
                    ) > int(300):
                        forecast_is_stale = True
            else:
                # File doesn't exist, download a new copy
                forecast_is_stale = True

            # File is stale, download a new copy
            if forecast_is_stale:
                try:
                    if sys.version_info[0] >= 3:
                        from urllib.request import Request, urlopen
                    else:
                        # Python 2
                        from urllib2 import Request, urlopen

                    user_agent = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3"
                    headers = {"User-Agent": user_agent}
                    if "forecast_dev_file" in self.generator.skin_dict["Extras"]:
                        # Hidden option to use a pre-downloaded forecast file
                        # rather than using API calls for no reason
                        dev_forecast_file = self.generator.skin_dict["Extras"][
                            "forecast_dev_file"
                        ]
                        req = Request(dev_forecast_file, None, headers)
                        response = urlopen(req)
                        forecast_file_result = response.read()
                        response.close()
                    else:
                        # Current conditions
                        req = Request(forecast_current_url, None, headers)
                        response = urlopen(req)
                        current_page = response.read()
                        response.close()
                        # 24hr forecast (was Forecast)
                        req = Request(forecast_24hr_url, None, headers)
                        response = urlopen(req)
                        forecast_24hr_page = response.read()
                        response.close()
                        # 3hr forecast
                        req = Request(forecast_3hr_url, None, headers)
                        response = urlopen(req)
                        forecast_3hr_page = response.read()
                        response.close()
                        # 1hr forecast
                        req = Request(forecast_1hr_url, None, headers)
                        response = urlopen(req)
                        forecast_1hr_page = response.read()
                        response.close()
                        # AQI
                        req = Request(aqi_url, None, headers)
                        response = urlopen(req)
                        aqi_page = response.read()
                        response.close()
                        if (
                            self.generator.skin_dict["Extras"]["forecast_alert_enabled"]
                            == "1"
                        ):
                            # Alerts
                            req = Request(forecast_alerts_url, None, headers)
                            response = urlopen(req)
                            alerts_page = response.read()
                            response.close()

                        # Combine all into 1 file
                        if (
                            self.generator.skin_dict["Extras"]["forecast_alert_enabled"]
                            == "1"
                        ):
                            try:
                                forecast_file_result = json.dumps(
                                    {
                                        "timestamp": int(time.time()),
                                        "current": [json.loads(current_page)],
                                        "forecast_24hr": [
                                            json.loads(forecast_24hr_page)
                                        ],
                                        "forecast_3hr": [json.loads(forecast_3hr_page)],
                                        "forecast_1hr": [json.loads(forecast_1hr_page)],
                                        "alerts": [json.loads(alerts_page)],
                                        "aqi": [json.loads(aqi_page)],
                                    }
                                )
                            except:
                                forecast_file_result = json.dumps(
                                    {
                                        "timestamp": int(time.time()),
                                        "current": [
                                            json.loads(current_page.decode("utf-8"))
                                        ],
                                        "forecast_24hr": [
                                            json.loads(
                                                forecast_24hr_page.decode("utf-8")
                                            )
                                        ],
                                        "forecast_3hr": [
                                            json.loads(
                                                forecast_3hr_page.decode("utf-8")
                                            )
                                        ],
                                        "forecast_1hr": [
                                            json.loads(
                                                forecast_1hr_page.decode("utf-8")
                                            )
                                        ],
                                        "alerts": [
                                            json.loads(alerts_page.decode("utf-8"))
                                        ],
                                        "aqi": [json.loads(aqi_page.decode("utf-8"))],
                                    }
                                )
                        else:
                            try:
                                forecast_file_result = json.dumps(
                                    {
                                        "timestamp": int(time.time()),
                                        "current": [json.loads(current_page)],
                                        "forecast_24hr": [
                                            json.loads(forecast_24hr_page)
                                        ],
                                        "forecast_3hr": [json.loads(forecast_3hr_page)],
                                        "forecast_1hr": [json.loads(forecast_1hr_page)],
                                        "aqi": [json.loads(aqi_page)],
                                    }
                                )
                            except:
                                forecast_file_result = json.dumps(
                                    {
                                        "timestamp": int(time.time()),
                                        "current": [
                                            json.loads(current_page.decode("utf-8"))
                                        ],
                                        "forecast_24hr": [
                                            json.loads(
                                                forecast_24hr_page.decode("utf-8")
                                            )
                                        ],
                                        "forecast_3hr": [
                                            json.loads(
                                                forecast_3hr_page.decode("utf-8")
                                            )
                                        ],
                                        "forecast_1hr": [
                                            json.loads(
                                                forecast_1hr_page.decode("utf-8")
                                            )
                                        ],
                                        "aqi": [json.loads(aqi_page.decode("utf-8"))],
                                    }
                                )
                except Exception as error:
                    raise Warning(
                        "Error downloading forecast data. "
                        "Check the URL in your configuration and try again. "
                        "You are trying to use URL: %s, and the error is: %s"
                        % (forecast_24hr_url, error)
                    )

                # Save forecast data to file. w+ creates the file if it doesn't
                # exist, and truncates the file and re-writes it everytime
                try:
                    with open(forecast_file, "wb+") as file:
                        try:
                            # Python 2/3
                            file.write(forecast_file_result.encode("utf-8"))
                        except:
                            # Catch errors caused by ASCII characters in Python2
                            file.write(forecast_file_result)
                        loginf("New forecast file downloaded to %s" % forecast_file)
                except IOError as e:
                    raise Warning(
                        "Error writing forecast info to %s. Reason: %s"
                        % (forecast_file, e)
                    )

            # Process the forecast file
            with open(forecast_file, "r") as read_file:
                data = json.load(read_file)

            try:
                cloud_cover = "{}%".format(data["current"][0]["response"]["ob"]["sky"])
            except Exception:
                loginf("No cloud cover data from Aeris weather")
                cloud_cover = ""

            try:
                if (
                    len(data["aqi"][0]["response"]) > 0
                ):
                    aqi = data["aqi"][0]["response"][0]["periods"][0]["aqi"]
                    aqi_category = data["aqi"][0]["response"][0]["periods"][0]["category"]
                    aqi_time = data["aqi"][0]["response"][0]["periods"][0]["timestamp"]
                    aqi_location = data["aqi"][0]["response"][0]["place"]["name"].title()
                elif (
                    data["aqi"][0]["error"]["code"] == "warn_no_data"
                ):
                    aqi = "No Data"
                    aqi_category = ""
                    aqi_time = 0
                    aqi_location = ""
            except Exception as error:
                logerr(
                    "Error getting AQI from Aeris weather. The error was: %s" % (error)
                )
                aqi = ""
                aqi_category = ""
                aqi_time = 0
                aqi_location = ""
                pass

            # https://www.aerisweather.com/support/docs/api/reference/endpoints/airquality/
            if aqi_category == "good":
                aqi_category = label_dict["aqi_good"]
            elif aqi_category == "moderate":
                aqi_category = label_dict["aqi_moderate"]
            elif aqi_category == "usg":
                aqi_category = label_dict["aqi_usg"]
            elif aqi_category == "unhealthy":
                aqi_category = label_dict["aqi_unhealthy"]
            elif aqi_category == "very unhealthy":
                aqi_category = label_dict["aqi_very_unhealthy"]
            elif aqi_category == "hazardous":
                aqi_category = label_dict["aqi_hazardous"]
            else:
                aqi_category = label_dict["aqi_unknown"]

            if (
                len(data["current"][0]["response"]) > 0
                and self.generator.skin_dict["Extras"]["forecast_aeris_use_metar"]
                == "0"
            ):
                # Non-metar responses do not contain these values. Set them to empty.
                current_obs_summary = ""
                current_obs_icon = ""
                visibility = "N/A"
                visibility_unit = ""
            elif (
                len(data["current"][0]["response"]) > 0
                and self.generator.skin_dict["Extras"]["forecast_aeris_use_metar"]
                == "1"
            ):
                current_obs_summary = aeris_coded_weather(
                    data["current"][0]["response"]["ob"]["weatherPrimaryCoded"]
                )
                current_obs_icon = (
                    aeris_icon(data["current"][0]["response"]["ob"]["icon"]) + ".png"
                )

                if forecast_units in ("si", "ca"):
                    if data["current"][0]["response"]["ob"]["visibilityKM"] is not None:
                        visibility = locale.format_string(
                            "%g", data["current"][0]["response"]["ob"]["visibilityKM"]
                        )
                        visibility_unit = "km"
                    else:
                        visibility = "N/A"
                        visibility_unit = ""
                else:
                    # us, uk2 and default to miles per hour
                    if data["current"][0]["response"]["ob"]["visibilityMI"] is not None:
                        visibility = locale.format_string(
                            "%g",
                            float(data["current"][0]["response"]["ob"]["visibilityMI"]),
                        )
                        visibility_unit = "miles"
                    else:
                        visibility = "N/A"
                        visibility_unit = ""
            else:
                # If the user selected to not use METAR, then these
                # observations are null.  If there's no data in the ob array
                # then it's probably because of an error.
                # Example:
                # "code": "warn_no_data",
                # "description": "Valid request. No results available based on
                # your query parameters."
                current_obs_summary = ""
                current_obs_icon = ""
                visibility = "N/A"
                visibility_unit = ""
        else:
            current_obs_icon = ""
            current_obs_summary = ""
            visibility = "N/A"
            visibility_unit = ""
            cloud_cover = ""

        # ==============================================================================
        # Earthquake Data
        # ==============================================================================

        # Only process if Earthquake data is enabled
        if self.generator.skin_dict["Extras"]["earthquake_enabled"] == "1":
            earthquake_file = html_root + "/json/earthquake.json"
            earthquake_stale_timer = self.generator.skin_dict["Extras"][
                "earthquake_stale"
            ]
            latitude = self.generator.config_dict["Station"]["latitude"]
            longitude = self.generator.config_dict["Station"]["longitude"]
            distance_unit = self.generator.converter.group_unit_dict["group_distance"]
            eq_distance_label = self.generator.skin_dict["Units"]["Labels"].get(
                distance_unit, ""
            )
            eq_distance_round = self.generator.skin_dict["Units"]["StringFormats"].get(
                distance_unit, "%.1f"
            )
            earthquake_maxradiuskm = self.generator.skin_dict["Extras"][
                "earthquake_maxradiuskm"
            ]
            # Sample URL from Belchertown Weather:
            # http://earthquake.usgs.gov/fdsnws/event/1/query?limit=1&lat=42.223&lon=-72.374&maxradiuskm=1000&format=geojson&nodata=204&minmag=2
            if self.generator.skin_dict["Extras"]["earthquake_server"] == "USGS":
                earthquake_url = (
                    "http://earthquake.usgs.gov/fdsnws/event/1/query?limit=1&lat=%s&lon=%s&maxradiuskm=%s&format=geojson&nodata=204&minmag=2"
                    % (latitude, longitude, earthquake_maxradiuskm)
                )
            elif self.generator.skin_dict["Extras"]["earthquake_server"] == "GeoNet":
                earthquake_url = (
                    "https://api.geonet.org.nz/quake?MMI=%s"
                    % self.generator.skin_dict["Extras"]["geonet_mmi"]
                )
            elif self.generator.skin_dict["Extras"]["earthquake_server"] == "ReNaSS":
                # Calculate min/max latitude and min/max longitude from radius and station location. https://stackoverflow.com/a/23118314
                lat = float(latitude)
                long = float(longitude)
                radiusInKm = int(earthquake_maxradiuskm)

                kmInLongitudeDegree = 111.320 * cos( lat / 180.0 * pi)

                deltaLat = radiusInKm / 111.1
                deltaLong = radiusInKm / kmInLongitudeDegree

                minLat = lat - deltaLat
                maxLat = lat + deltaLat
                minLong = long - deltaLong
                maxLong = long + deltaLong

                earthquake_url = (
                    "https://api.franceseisme.fr/fdsnws/event/1/query?eventtype=earthquake&minmagnitude=2&minlatitude=%.2f&minlongitude=%.2f&maxlatitude=%.2f&maxlongitude=%.2f&format=json&limit=1&orderby=time"
                    % (minLat, minLong, maxLat, maxLong) 
                )
            earthquake_is_stale = False

            # Determine if the file exists and get it's modified time
            if os.path.isfile(earthquake_file):
                if (int(time.time()) - int(os.path.getmtime(earthquake_file))) > int(
                    earthquake_stale_timer
                ):
                    earthquake_is_stale = True
            else:
                # File doesn't exist, download a new copy
                earthquake_is_stale = True

            # File is stale, download a new copy
            if earthquake_is_stale:
                # Download new earthquake data
                try:
                    if sys.version_info[0] >= 3:
                        from urllib.request import Request, urlopen
                    else:
                        # Python 2
                        from urllib2 import Request, urlopen

                    user_agent = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3"
                    headers = {"User-Agent": user_agent}
                    req = Request(earthquake_url, None, headers)
                    response = urlopen(req)
                    page = response.read()
                    response.close()
                    if weewx.debug:
                        logdbg(
                            "Downloading earthquake data using urllib2 was successful"
                        )
                except Exception as forecast_error:
                    if weewx.debug:
                        logdbg(
                            "Error downloading earthquake data with urllib2, reverting to curl and subprocess. "
                            "Full error: %s" % forecast_error
                        )
                    # Nested try - only execute if the urllib2 method fails
                    try:
                        import subprocess

                        command = 'curl -L --silent "%s"' % earthquake_url
                        p = subprocess.Popen(
                            command,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                        )
                        page = p.communicate()[0]
                        if weewx.debug:
                            logdbg(
                                "Downloading earthquake data with curl was successful."
                            )
                    except Exception as error:
                        raise Warning(
                            "Error downloading earthquake data using urllib2 and subprocess curl. "
                            "Your software may need to be updated, or the URL is incorrect. "
                            "You are trying to use URL: %s, and the error is: %s"
                            % (earthquake_url, error)
                        )

                # Save earthquake data to file. w+ creates the file if it
                # doesn't exist, and truncates the file and re-writes it
                # everytime
                try:
                    with open(earthquake_file, "wb+") as file:
                        try:
                            # Python 2/3
                            file.write(page.encode("utf-8"))
                        except:
                            # Catch errors caused by ASCII characters in Python2
                            file.write(page)
                        if weewx.debug:
                            logdbg("Earthquake data saved to %s" % earthquake_file)
                except IOError as e:
                    raise Warning(
                        "Error writing earthquake data to %s. Reason: %s"
                        % (earthquake_file, e)
                    )

            # Process the earthquake file
            with open(earthquake_file, "r") as read_file:
                try:
                    eqdata = json.load(read_file)
                except:
                    eqdata = ""

            try:
                if self.generator.skin_dict["Extras"]["earthquake_server"] == "USGS":
                    eqtime = eqdata["features"][0]["properties"]["time"] / 1000
                    equrl = eqdata["features"][0]["properties"]["url"]
                    if distance_unit == "km":
                        eqplace = eqdata["features"][0]["properties"]["place"]
                    else:  # assume miles
                        try:
                            eqmatched = match(
                                "(?P<distance>[0-9]*\.?[0-9]+) km(?P<rest>.*)$",
                                eqdata["features"][0]["properties"]["place"],
                            )
                            eqdist_km = eqmatched.group("distance")
                            eqdist_miles = round(float(eqdist_km) / 1.609, 1)
                            eqplace = (
                                str(eqdist_miles) + " miles" + eqmatched.group("rest")
                            )
                        except:
                            eqplace = eqdata["features"][0]["properties"]["place"]
                    eqmag = locale.format_string(
                        "%g", float(eqdata["features"][0]["properties"]["mag"])
                    )
                elif (
                    self.generator.skin_dict["Extras"]["earthquake_server"] == "ReNaSS"
                ):
                    eqtime = eqdata["features"][0]["properties"]["time"]
                    # convert time to UNIX format
                    eqtime = datetime.datetime.strptime(eqtime, "%Y-%m-%dT%H:%M:%S.%fZ")
                    eqtime = int(
                        (eqtime - datetime.datetime(1970, 1, 1)).total_seconds()
                    )
                    if match("fr_.*", system_locale):
                        equrl = eqdata["features"][0]["properties"]["url"]["fr"]
                        eqplace = eqdata["features"][0]["properties"]["description"]["fr"]
                    else:
                        equrl = eqdata["features"][0]["properties"]["url"]["en"]
                        eqplace = eqdata["features"][0]["properties"]["description"]["en"]
                    eqmag = format(
                         eqdata["features"][0]["properties"]["mag"], ".1f"
                    )
                elif (
                    self.generator.skin_dict["Extras"]["earthquake_server"] == "GeoNet"
                ):
                    eqtime = eqdata["features"][0]["properties"]["time"]
                    # convert time to UNIX format
                    eqtime = datetime.datetime.strptime(eqtime, "%Y-%m-%dT%H:%M:%S.%fZ")
                    eqtime = int(
                        (eqtime - datetime.datetime(1970, 1, 1)).total_seconds()
                    )
                    equrl = (
                        "https://www.geonet.org.nz/earthquake/"
                        + eqdata["features"][0]["properties"]["publicID"]
                    )
                    eqplace = eqdata["features"][0]["properties"]["locality"]
                    eqmag = locale.format_string(
                        "%g",
                        float(
                            round(eqdata["features"][0]["properties"]["magnitude"], 1)
                        ),
                    )
                eqlat = str(
                    round(eqdata["features"][0]["geometry"]["coordinates"][1], 4)
                )
                eqlon = str(
                    round(eqdata["features"][0]["geometry"]["coordinates"][0], 4)
                )
                eqdistance_bearing = self.get_gps_distance(
                    (float(latitude), float(longitude)),
                    (float(eqlat), float(eqlon)),
                    distance_unit,
                )
                eqdistance = locale.format_string(
                    "%g", float(eq_distance_round % eqdistance_bearing[0])
                )
                eqbearing = eqdistance_bearing[1]
                eqbearing_raw = eqdistance_bearing[2]
            except:
                # No earthquake data
                eqtime = label_dict["earthquake_no_data"]
                equrl = ""
                eqplace = ""
                eqmag = ""
                eqlat = ""
                eqlon = ""
                eqdistance = ""
                eqbearing = ""
                eqbearing_raw = ""

        else:
            eqtime = ""
            equrl = ""
            eqplace = ""
            eqmag = ""
            eqlat = ""
            eqlon = ""
            eqdistance = ""
            eqbearing = ""
            eqbearing_raw = ""
            eq_distance_label = ""

        # ==============================================================================
        # Get Current Station Observation Data for the table html
        # ==============================================================================

        station_obs_binding = None
        station_obs_json = OrderedDict()
        station_obs_html = ""
        station_observations = self.generator.skin_dict["Extras"][
            "station_observations"
        ]
        # Check if this is a list. If not then we have 1 item, so force it into a list
        if isinstance(station_observations, list) is False:
            station_observations = station_observations.split()
        current_stamp = manager.lastGoodStamp()
        current_record = manager.getRecord(current_stamp)
        current = weewx.tags.CurrentObj(
            db_lookup,
            station_obs_binding,
            current_stamp,
            self.generator.formatter,
            self.generator.converter,
            None,
            current_record
        )
        for obs in station_observations:
            if "data_binding" in obs:
                station_obs_binding = obs[obs.find("(") + 1 : obs.rfind(")")].split(
                    "="
                )[
                    1
                ]  # Thanks https://stackoverflow.com/a/40811994/1177153
                obs = obs.split("(")[0]
            if station_obs_binding is not None:
                obs_binding_manager = self.generator.db_binder.get_manager(
                    station_obs_binding
                )
                current_stamp = obs_binding_manager.lastGoodStamp()
                current_record = obs_binding_manager.getRecord(current_stamp)
                current = weewx.tags.CurrentObj(
                    db_lookup,
                    station_obs_binding,
                    current_stamp,
                    self.generator.formatter,
                    self.generator.converter,
                    None,
                    current_record
                )

            if obs == "visibility":
                try:
                    obs_output = str(visibility) + " " + str(visibility_unit)
                except:
                    raise Warning(
                        "Error adding visiblity to station observations table. "
                        "Check that you have forecast data, or remove visibility from your station_observations Extras option."
                    )
            elif obs == "rainWithRainRate":
                # rainWithRainRate Rain shows rain daily sum and rain rate
                obs_binder = weewx.tags.ObservationBinder(
                    "rain",
                    archiveDaySpan(current_stamp),
                    db_lookup,
                    None,
                    "day",
                    self.generator.formatter,
                    self.generator.converter,
                )
                dayRain_sum = getattr(obs_binder, "sum")
                # Need to use dayRain for class name since that is weewx-mqtt
                # payload's name
                obs_rain_output = "<span class='dayRain'>%s</span><!-- AJAX -->" % str(
                    dayRain_sum
                )
                obs_rain_output += "&nbsp;<span class='border-left'>&nbsp;</span>"
                obs_rain_output += (
                    "<span class='rainRate'>%s</span><!-- AJAX -->"
                    % str(getattr(current, "rainRate"))
                )

                # Empty field for the JSON "current" output
                obs_output = ""
            elif obs == "cloud_cover":
                obs_output = cloud_cover
            elif obs == "aqi":
                obs_output = aqi
            else:
                obs_output = getattr(current, obs)
                if "?" in str(obs_output):
                    # Try to catch those invalid observations, like 'uv' needs
                    # to be 'UV'.
                    obs_output = "Invalid observation"

            # Build the json "current" array for weewx_data.json for JavaScript
            if obs not in station_obs_json:
                station_obs_json[obs] = str(obs_output)

            # Build the HTML for the front page
            station_obs_html += "<tr>"
            station_obs_html += (
                "<td class='station-observations-label'>%s</td>" % label_dict[obs]
            )
            station_obs_html += "<td>"
            if obs == "rainWithRainRate":
                # Add special rain + rainRate one liner
                station_obs_html += obs_rain_output
            else:
                station_obs_html += "<span class=%s>%s</span><!-- AJAX -->" % (
                    obs,
                    obs_output,
                )
            if obs in ("barometer", "pressure", "altimeter"):
                # Append the trend arrow to the pressure observation. Need this
                # for non-mqtt pages
                trend = weewx.tags.TrendObj(
                    10800,
                    300,
                    db_lookup,
                    None,
                    current_stamp,
                    self.generator.formatter,
                    self.generator.converter,
                )
                obs_trend = getattr(trend, obs)
                station_obs_html += (
                    ' <span class="pressure-trend">'  # Maintain leading spacing
                )
                if str(obs_trend) == "N/A":
                    pass
                elif "-" in str(obs_trend):
                    station_obs_html += (
                        '<i class="fa fa-arrow-down barometer-down"></i>'
                    )
                else:
                    station_obs_html += '<i class="fa fa-arrow-up barometer-up"></i>'
                station_obs_html += "</span>"  # Close the span
            station_obs_html += "</td>"
            station_obs_html += "</tr>"

        # ==============================================================================
        # Get all observations and their rounding values
        # ==============================================================================

        all_obs_rounding_json = OrderedDict()
        all_obs_unit_labels_json = OrderedDict()
        for obs in sorted(weewx.units.obs_group_dict):
            try:
                # Find the unit from group (like group_temperature = degree_F)
                obs_group = weewx.units.obs_group_dict[obs]
                obs_unit = self.generator.converter.group_unit_dict[obs_group]
            except:
                # Something's wrong. Continue this loop to ignore this group
                # (like group_dust or something non-standard)
                continue
            try:
                # Find the number of decimals to round to based on group name
                obs_round = self.generator.skin_dict["Units"]["StringFormats"].get(
                    obs_unit, "0"
                )[2]
            except:
                obs_round = self.generator.skin_dict["Units"]["StringFormats"].get(
                    obs_unit, "0"
                )
            # Add to the rounding array
            if obs not in all_obs_rounding_json:
                all_obs_rounding_json[obs] = str(obs_round)
            # Get the unit's label
            # Add to label array and strip whitespace if possible
            if obs not in all_obs_unit_labels_json:
                obs_unit_label = weewx.units.get_label_string(
                    self.generator.formatter, self.generator.converter, obs
                )
                all_obs_unit_labels_json[obs] = obs_unit_label

            # Special handling items
            if visibility:
                all_obs_rounding_json["visibility"] = "2"
                all_obs_unit_labels_json["visibility"] = visibility_unit
            else:
                all_obs_rounding_json["visibility"] = ""
                all_obs_unit_labels_json["visibility"] = ""

        # ==============================================================================
        # Social Share
        # ==============================================================================

        facebook_enabled = self.generator.skin_dict["Extras"]["facebook_enabled"]
        twitter_enabled = self.generator.skin_dict["Extras"]["twitter_enabled"]
        social_share_html = self.generator.skin_dict["Extras"]["social_share_html"]
        twitter_text = label_dict["twitter_text"]
        twitter_owner = label_dict["twitter_owner"]
        twitter_hashtags = label_dict["twitter_hashtags"]

        if facebook_enabled == "1":
            facebook_html = (
                """
                <div id="fb-root"></div>
                <script>(function(d, s, id) {
                  var js, fjs = d.getElementsByTagName(s)[0];
                  if (d.getElementById(id)) return;
                  js = d.createElement(s); js.id = id;
                  js.src = "//connect.facebook.net/en_US/sdk.js#xfbml=1&version=v2.5";
                  fjs.parentNode.insertBefore(js, fjs);
                }(document, 'script', 'facebook-jssdk'));</script>
                <div class="fb-like" data-href="%s" data-width="500px" data-layout="button_count" data-action="like" data-show-faces="false" data-share="true"></div>
            """
                % social_share_html
            )
        else:
            facebook_html = ""

        if twitter_enabled == "1":
            twitter_html = """
                <script>
                    !function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0],p=/^http:/.test(d.location)?'http':'https';if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src=p+'://platform.twitter.com/widgets.js';fjs.parentNode.insertBefore(js,fjs);}}(document, 'script', 'twitter-wjs');
                </script>
                <a href="https://twitter.com/share" class="twitter-share-button" data-url="%s" data-text="%s" data-via="%s" data-hashtags="%s">Tweet</a>
            """ % (
                social_share_html,
                twitter_text,
                twitter_owner,
                twitter_hashtags,
            )
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

        #==============================================================================
        # MQTT settings for Kiosk page
        # ==============================================================================

        if self.generator.skin_dict["Extras"]["mqtt_websockets_host_kiosk"] != "":
            if self.generator.skin_dict["Extras"]["mqtt_websockets_port_kiosk"] != "":
                mqtt_websockets_port_kiosk = self.generator.skin_dict["Extras"]["mqtt_websockets_port_kiosk"]
            else:
                mqtt_websockets_port_kiosk = self.generator.skin_dict["Extras"]["mqtt_websockets_port"]
            if self.generator.skin_dict["Extras"]["mqtt_websockets_ssl_kiosk"] != "":
                mqtt_websockets_ssl_kiosk = self.generator.skin_dict["Extras"]["mqtt_websockets_ssl_kiosk"]
            else:
                mqtt_websockets_ssl_kiosk = self.generator.skin_dict["Extras"]["mqtt_websockets_ssl"]
        else:
            mqtt_websockets_port_kiosk = self.generator.skin_dict["Extras"]["mqtt_websockets_host"]
            mqtt_websockets_port_kiosk = self.generator.skin_dict["Extras"]["mqtt_websockets_port"]
            mqtt_websockets_ssl_kiosk = self.generator.skin_dict["Extras"]["mqtt_websockets_ssl"]



        # Include custom.css if it exists in the HTML_ROOT folder
        custom_css_file = html_root + "/custom.css"
        # Determine if the file exists
        custom_css_exists = os.path.isfile(custom_css_file)

        # Build the search list with the new values
        search_list_extension = {
            "belchertown_version": VERSION,
            "belchertown_debug": belchertown_debug,
            "moment_js_utc_offset": moment_js_utc_offset,
            "moment_js_tz": moment_js_tz,
            "highcharts_timezoneoffset": highcharts_timezoneoffset,
            "system_locale": system_locale,
            "system_locale_js": system_locale_js,
            "locale_encoding": locale_encoding,
            "highcharts_decimal": highcharts_decimal,
            "highcharts_thousands": highcharts_thousands,
            "radar_html": radar_html,
            "radar_html_dark": radar_html_dark,
            "radar_html_kiosk": radar_html_kiosk,
            "archive_interval_ms": archive_interval_ms,
            "ordinate_names": ordinate_names,
            "charts": json.dumps(charts),
            "graphpage_titles": json.dumps(graphpage_titles),
            "graphpage_titles_dict": graphpage_titles,
            "graphpage_content": json.dumps(graphpage_content),
            "graph_page_buttons": graph_page_buttons,
            "alltime": all_stats,
            "year_outTemp_range_max": year_outTemp_range_max,
            "year_outTemp_range_min": year_outTemp_range_min,
            "at_outTemp_range_max": at_outTemp_range_max,
            "at_outTemp_range_min": at_outTemp_range_min,
            "rainiest_day": rainiest_day,
            "at_rainiest_day": at_rainiest_day,
            "year_rainiest_month": year_rainiest_month,
            "at_rainiest_month": at_rainiest_month,
            "at_rain_highest_year": at_rain_highest_year,
            "year_days_with_rain": year_days_with_rain,
            "year_days_without_rain": year_days_without_rain,
            "at_days_with_rain": at_days_with_rain,
            "at_days_without_rain": at_days_without_rain,
            "windSpeedUnitLabel": windSpeed_unit_label,
            "noaa_header_html": noaa_header_html,
            "default_noaa_file": default_noaa_file,
            "current_obs_icon": current_obs_icon,
            "current_obs_summary": current_obs_summary,
            "visibility": visibility,
            "visibility_unit": visibility_unit,
            "cloud_cover": cloud_cover,
            "station_obs_json": json.dumps(station_obs_json),
            "station_obs_html": station_obs_html,
            "all_obs_rounding_json": json.dumps(all_obs_rounding_json),
            "all_obs_unit_labels_json": json.dumps(all_obs_unit_labels_json),
            "earthquake_time": eqtime,
            "earthquake_url": equrl,
            "earthquake_place": eqplace,
            "earthquake_magnitude": eqmag,
            "earthquake_lat": eqlat,
            "earthquake_lon": eqlon,
            "earthquake_distance_away": eqdistance,
            "earthquake_distance_label": eq_distance_label,
            "earthquake_bearing": eqbearing,
            "earthquake_bearing_raw": eqbearing_raw,
            "social_html": social_html,
            "custom_css_exists": custom_css_exists,
            "aqi": aqi,
            "aqi_category": aqi_category,
            "aqi_location": aqi_location,
            "beaufort0": label_dict["beaufort0"],
            "beaufort1": label_dict["beaufort1"],
            "beaufort2": label_dict["beaufort2"],
            "beaufort3": label_dict["beaufort3"],
            "beaufort4": label_dict["beaufort4"],
            "beaufort5": label_dict["beaufort5"],
            "beaufort6": label_dict["beaufort6"],
            "beaufort7": label_dict["beaufort7"],
            "beaufort8": label_dict["beaufort8"],
            "beaufort9": label_dict["beaufort9"],
            "beaufort10": label_dict["beaufort10"],
            "beaufort11": label_dict["beaufort11"],
            "beaufort12": label_dict["beaufort12"],
            "mqtt_websockets_port_kiosk": mqtt_websockets_port_kiosk,
            "mqtt_websockets_ssl_kiosk": mqtt_websockets_ssl_kiosk,
        }
        # Finally, return our extension as a list:
        return [search_list_extension]


# ======================================================================================
# HighchartsJsonGenerator
# ======================================================================================


class HighchartsJsonGenerator(weewx.reportengine.ReportGenerator):
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

        chart_config_path = os.path.join(
            self.config_dict["WEEWX_ROOT"],
            self.skin_dict["SKIN_ROOT"],
            self.skin_dict.get("skin", ""),
            "graphs.conf",
        )
        default_chart_config_path = os.path.join(
            self.config_dict["WEEWX_ROOT"],
            self.skin_dict["SKIN_ROOT"],
            self.skin_dict.get("skin", ""),
            "graphs.conf.example",
        )
        if os.path.exists(chart_config_path):
            self.chart_dict = configobj.ConfigObj(chart_config_path, file_error=True)
        else:
            self.chart_dict = configobj.ConfigObj(
                default_chart_config_path, file_error=True
            )

        self.converter = weewx.units.Converter.fromSkinDict(self.skin_dict)
        self.formatter = weewx.units.Formatter.fromSkinDict(self.skin_dict)

        # Setup title dict for plot titles
        try:
            d = self.skin_dict["Labels"]["Generic"]
        except KeyError:
            d = {}
        label_dict = weeutil.weeutil.KeyDict(d)

        # Final output dict
        output = {}

        # Loop through each [section]. This is the first bracket group of
        # options including global options.
        for chart_group in self.chart_dict.sections:
            output[
                chart_group
            ] = (
                OrderedDict()
            )  # This retains the order in which to load the charts on the page.
            chart_options = accumulateLeaves(self.chart_dict[chart_group])

            output[chart_group]["belchertown_version"] = VERSION
            output[chart_group]["generated_timestamp"] = time.strftime(
                "%m/%d/%Y %H:%M:%S"
            )

            # Setup the JSON file name for each chart group
            html_dest_dir = os.path.join(
                self.config_dict["WEEWX_ROOT"], self.skin_dict["HTML_ROOT"], "json"
            )
            json_filename = html_dest_dir + "/" + chart_group + ".json"

            # Default back to Highcharts standards
            colors = chart_options.get(
                "colors",
                "#7cb5ec, #b2df8a, #f7a35c, #8c6bb1, #dd3497, #e4d354, #268bd2, #f45b5b, #6a3d9a, #33a02c",
            )
            output[chart_group]["colors"] = colors

            # chartgroup_title is used on the graphs page
            chartgroup_title = chart_options.get("title", None)
            if chartgroup_title:
                output[chart_group]["chartgroup_title"] = chartgroup_title

            # Define the default tooltip datetime format from the global options
            tooltip_date_format = chart_options.get("tooltip_date_format", "LLLL")
            output[chart_group]["tooltip_date_format"] = tooltip_date_format

            # Credits Text
            credits = chart_options.get("credits", "highcharts_default")
            output[chart_group]["credits"] = credits

            # Credits URL
            credits_url = chart_options.get("credits_url", "highcharts_default")
            output[chart_group]["credits_url"] = credits_url

            # Credits position
            credits_position = chart_options.get(
                "credits_position", "highcharts_default"
            )
            output[chart_group]["credits_position"] = credits_position

            # Check if there are any user override on generation periods.
            # Takes the crontab approach. If the words hourly, daily, monthly,
            # yearly are present use them, otherwise use an integer interval if
            # available.  Since weewx could be restarted, we'll lose our
            # end-timestamp to trigger off of for chart staleness.  So we have
            # to use the timestamp of the file to generate this. If the file
            # does not exist, we need to create it first.  Once created we use
            # that to see if we need to generate a fresh data set for the
            # chart.
            generate = chart_options.get("generate", None)
            if generate is not None:
                # Default to not making a new chart
                create_new_chart = False

                # Get our intervals. Minus 60 seconds so that it'll run a
                # little more reliably on the next interval.
                if generate.lower() == "hourly":
                    chart_stale_timer = 3540
                elif generate.lower() == "daily":
                    chart_stale_timer = 86340
                elif generate.lower() == "weekly":
                    chart_stale_timer = 604740
                elif generate.lower() == "monthly":
                    chart_stale_timer = 2629686
                elif generate.lower() == "yearly":
                    chart_stale_timer = 31556892
                else:
                    chart_stale_timer = int(generate)

                if not os.path.isfile(json_filename):
                    # File doesn't exist. Chart is stale no matter what.
                    create_new_chart = True
                else:
                    # The file exists get timestamp to compare against what the
                    # user wants for an interval
                    if (int(time.time()) - int(os.path.getmtime(json_filename))) >= int(
                        chart_stale_timer
                    ):
                        create_new_chart = True

                # Chart isn't stale, so continue to next chart (this current
                # chart_group is skipped and not generated)
                if not create_new_chart:
                    continue

            # Loop through each [[chart_group]] within the section.
            for plotname in self.chart_dict[chart_group].sections:
                output[chart_group][plotname] = {}

                # This retains the observation position in the dictionary to
                # match the order in the conf so the chart is in the right
                # user-defined order
                output[chart_group][plotname]["series"] = OrderedDict()

                output[chart_group][plotname]["options"] = {}
                # output[chart_group][plotname]["options"]["renderTo"] = chart_group + plotname # daychart1, weekchart1, etc.
                # Used for the graphs page and the different chart_groups
                output[chart_group][plotname]["options"][
                    "renderTo"
                ] = plotname  # daychart1, weekchart1, etc. Used for the graphs page and the different chart_groups
                output[chart_group][plotname]["options"]["chart_group"] = chart_group

                plot_options = accumulateLeaves(self.chart_dict[chart_group][plotname])

                # Setup the database binding, default to weewx.conf's binding
                # if none supplied.
                binding = plot_options.get(
                    "data_binding",
                    self.config_dict["StdReport"].get("data_binding", "wx_binding"),
                )
                archive = self.db_binder.get_manager(binding)

                # Generate timespan for the string time windows
                start_ts = archive.firstGoodStamp()
                stop_ts = archive.lastGoodStamp()
                timespan = weeutil.weeutil.TimeSpan(start_ts, stop_ts)

                # Find timestamps for the rolling window
                plotgen_ts = self.gen_ts
                if not plotgen_ts:
                    plotgen_ts = stop_ts
                    if not plotgen_ts:
                        plotgen_ts = time.time()

                chart_title = plot_options.get("title", "")
                output[chart_group][plotname]["options"]["title"] = chart_title

                chart_subtitle = plot_options.get("subtitle", "")
                output[chart_group][plotname]["options"]["subtitle"] = chart_subtitle

                # Get the type of plot ("bar', 'line', 'spline', or 'scatter')
                plottype = plot_options.get("type", "line")
                output[chart_group][plotname]["options"]["type"] = plottype

                # gapsize has to be in milliseconds. Take the graphs.conf value
                # and multiply by 1000
                gapsize = plot_options.get(
                    "gapsize", 300
                )  # Default to 5 minutes in millis
                if gapsize:
                    output[chart_group][plotname]["options"]["gapsize"] = int(gapsize) * 1000

                connectNulls = plot_options.get("connectNulls", "false")
                output[chart_group][plotname]["options"]["connectNulls"] = connectNulls

                xAxis_groupby = plot_options.get("xAxis_groupby", None)
                xAxis_categories = plot_options.get("xAxis_categories", "")
                # Check if this is a list. If not then we have 1 item, so force
                # it into a list
                if isinstance(xAxis_categories, list) is False:
                    xAxis_categories = xAxis_categories.split()
                output[chart_group][plotname]["options"][
                    "xAxis_categories"
                ] = xAxis_categories

                # Grab any per-chart tooltip date format overrides
                plot_tooltip_date_format = plot_options.get("tooltip_date_format", None)
                output[chart_group][plotname]["options"][
                    "plot_tooltip_date_format"
                ] = plot_tooltip_date_format

                # Width and height specific CSS overrides
                output[chart_group][plotname]["options"][
                    "css_width"
                ] = plot_options.get("width", "")
                output[chart_group][plotname]["options"][
                    "css_height"
                ] = plot_options.get("height", "")

                # Setup legend option
                legend = plot_options.get("legend", None)
                if legend is None:
                    # Default to true if the option is missing
                    output[chart_group][plotname]["options"]["legend"] = "true"
                else:
                    output[chart_group][plotname]["options"]["legend"] = legend

                # Setup exporting option
                exporting = plot_options.get("exporting", None)
                if exporting is not None and to_bool(exporting):
                    # Only turn on exporting if it's not none and it's true (1 or True)
                    output[chart_group][plotname]["options"]["exporting"] = "true"
                else:
                    output[chart_group][plotname]["options"]["exporting"] = "false"

                # Loop through each [[[observation]]] within the chart_group.
                for line_name in self.chart_dict[chart_group][plotname].sections:
                    output[chart_group][plotname]["series"][line_name] = {}
                    output[chart_group][plotname]["series"][line_name][
                        "obsType"
                    ] = line_name

                    line_options = accumulateLeaves(
                        self.chart_dict[chart_group][plotname][line_name]
                    )

                    # Look for any keyword timespans first and default to those
                    # start/stop times for the chart
                    time_length = line_options.get("time_length", 86400)
                    time_ago = int(line_options.get("time_ago", 1))
                    day_specific = line_options.get(
                        "day_specific", 1
                    )  # Force a day so we don't error out
                    month_specific = line_options.get(
                        "month_specific", 8
                    )  # Force a month so we don't error out
                    year_specific = line_options.get(
                        "year_specific", 2019
                    )  # Force a year so we don't error out
                    start_at_midnight = to_bool(
                        line_options.get("start_at_midnight", False)
                    )  # Should our timespan start at midnight?
                    start_at_whole_hour = to_bool(
                        line_options.get("start_at_whole_hour", False)
                    )  # Should our timespan start at a whole hour?
                    start_at_beginning_of_month = to_bool(
                        line_options.get("start_at_beginning_of_month", False)
                    )  # Should our timespan start at the beginning of a month?
                    if time_length == "today":
                        minstamp, maxstamp = archiveDaySpan(timespan.stop)
                    elif time_length == "week":
                        week_start = to_int(
                            self.config_dict["Station"].get("week_start", 6)
                        )
                        minstamp, maxstamp = archiveWeekSpan(timespan.stop, week_start)
                    elif time_length == "month":
                        minstamp, maxstamp = archiveMonthSpan(timespan.stop)
                    elif time_length == "year":
                        minstamp, maxstamp = archiveYearSpan(timespan.stop)
                    elif time_length == "days_ago":
                        minstamp, maxstamp = archiveDaySpan(
                            timespan.stop, days_ago=time_ago
                        )
                    elif time_length == "weeks_ago":
                        week_start = to_int(
                            self.config_dict["Station"].get("week_start", 6)
                        )
                        minstamp, maxstamp = archiveWeekSpan(
                            timespan.stop, week_start, weeks_ago=time_ago
                        )
                    elif time_length == "months_ago":
                        minstamp, maxstamp = archiveMonthSpan(
                            timespan.stop, months_ago=time_ago
                        )
                    elif time_length == "years_ago":
                        minstamp, maxstamp = archiveYearSpan(
                            timespan.stop, years_ago=time_ago
                        )
                    elif time_length == "day_specific":
                        # Set an arbitrary hour within the specific day to get
                        # that full day timespan and not the day before.
                        # e.g. 1pm
                        day_dt = datetime.datetime.strptime(
                            str(year_specific)
                            + "-"
                            + str(month_specific)
                            + "-"
                            + str(day_specific)
                            + " 13",
                            "%Y-%m-%d %H",
                        )
                        daystamp = int(time.mktime(day_dt.timetuple()))
                        minstamp, maxstamp = archiveDaySpan(daystamp)
                    elif time_length == "month_specific":
                        # Set an arbitrary day within the specific month to get
                        # that full month timespan and not the day before.
                        # e.g. 5th day
                        month_dt = datetime.datetime.strptime(
                            str(year_specific) + "-" + str(month_specific) + "-5",
                            "%Y-%m-%d",
                        )
                        monthstamp = int(time.mktime(month_dt.timetuple()))
                        minstamp, maxstamp = archiveMonthSpan(monthstamp)
                    elif time_length == "year_specific":
                        # Get a date in the middle of the year to get the full
                        # year epoch so weewx can find the year timespan.
                        year_dt = datetime.datetime.strptime(
                            str(year_specific) + "-8-1", "%Y-%m-%d"
                        )
                        yearstamp = int(time.mktime(year_dt.timetuple()))
                        minstamp, maxstamp = archiveYearSpan(yearstamp)
                    elif time_length == "year_to_now":
                        minstamp, maxstamp = self.timespan_year_to_now(timespan.stop)
                    elif time_length == "hour_ago_to_now":
                        if start_at_midnight:
                            span_start, span_stop = archiveSpanSpan(
                                timespan.stop, hour_delta=time_ago
                            )
                            minstamp, maxstamp = TimeSpan(
                                startOfDay(span_start), span_stop
                            )
                        else:
                            minstamp, maxstamp = archiveSpanSpan(
                                timespan.stop, hour_delta=time_ago
                            )
                    elif time_length == "day_ago_to_now":
                        if start_at_midnight:
                            span_start, span_stop = archiveSpanSpan(
                                timespan.stop, day_delta=time_ago
                            )
                            minstamp, maxstamp = TimeSpan(
                                startOfDay(span_start), span_stop
                            )
                        else:
                            minstamp, maxstamp = archiveSpanSpan(
                                timespan.stop, day_delta=time_ago
                            )
                    elif time_length == "week_ago_to_now":
                        if start_at_midnight:
                            span_start, span_stop = archiveSpanSpan(
                                timespan.stop, week_delta=time_ago
                            )
                            minstamp, maxstamp = TimeSpan(
                                startOfDay(span_start), span_stop
                            )
                        else:
                            minstamp, maxstamp = archiveSpanSpan(
                                timespan.stop, week_delta=time_ago
                            )
                    elif time_length == "month_ago_to_now":
                        if start_at_midnight:
                            span_start, span_stop = archiveSpanSpan(
                                timespan.stop, month_delta=time_ago
                            )
                            minstamp, maxstamp = TimeSpan(
                                startOfDay(span_start), span_stop
                            )
                        else:
                            minstamp, maxstamp = archiveSpanSpan(
                                timespan.stop, month_delta=time_ago
                            )
                    elif time_length == "year_ago_to_now":
                        if start_at_midnight:
                            span_start, span_stop = archiveSpanSpan(
                                timespan.stop, year_delta=time_ago
                            )
                            minstamp, maxstamp = TimeSpan(
                                startOfDay(span_start), span_stop
                            )
                        else:
                            minstamp, maxstamp = archiveSpanSpan(
                                timespan.stop, year_delta=time_ago
                            )
                    elif time_length == "timestamp_ago_to_now":
                        if start_at_midnight:
                            minstamp, maxstamp = TimeSpan(
                                startOfDay(time_ago), timespan.stop
                            )
                        else:
                            minstamp, maxstamp = TimeSpan(time_ago, timespan.stop)
                    elif time_length == "timespan_specific":
                        minstamp = line_options.get("timespan_start", None)
                        maxstamp = line_options.get("timespan_stop", None)
                        if minstamp is None or maxstamp is None:
                            raise Warning(
                                "Error trying to create timespan_specific graph. "
                                "You are missing either timespan_start or timespan_stop options."
                            )
                    elif time_length == "all":
                        minstamp = start_ts
                        maxstamp = stop_ts
                    else:
                        # Rolling timespans using seconds

                        # Convert to int() for minstamp math and for
                        # point_timestamp conditional later
                        time_length = int(time_length)

                        # Take the generation time and subtract the time_length
                        # to get our start time
                        if start_at_midnight:
                            span_start = plotgen_ts - time_length
                            minstamp = startOfDay(span_start)
                        else:
                            minstamp = plotgen_ts - time_length
                        maxstamp = plotgen_ts

                    if start_at_whole_hour:
                        minstamp -= minstamp % 3600
                    
                    if start_at_beginning_of_month:
                        start_ts, stop_ts = archiveMonthSpan(minstamp)
                        minstamp = start_ts

                    # Find if this chart is using a new database binding.
                    # Default to the binding set in plot_options
                    binding = line_options.get("data_binding", binding)
                    archive = self.db_binder.get_manager(binding)

                    # Find the observation type if specified (e.g. more than 1
                    # of the same on a chart). (e.g. outTemp, rainFall,
                    # windDir, etc.)
                    observation_type = line_options.get("observation_type", line_name)

                    # If we have a weather range, define what the actual
                    # observation type to lookup in the db is, and to use for
                    # yAxis labels
                    weatherRange_obs_lookup = line_options.get("range_type", None)

                    # Get any custom names for this observation
                    name = line_options.get("name", None)
                    if not name:
                        # No explicit name. Look up a generic one. NB:
                        # label_dict is a KeyDict which will substitute the key
                        # if the value is not in the dictionary.
                        if weatherRange_obs_lookup is not None:
                            name = label_dict[weatherRange_obs_lookup]
                        else:
                            name = label_dict[observation_type]

                    # Look for aggregation type:
                    aggregate_type = line_options.get("aggregate_type")
                    if aggregate_type in (None, "", "None", "none"):
                        # No aggregation specified.
                        aggregate_type = aggregate_interval = None
                    else:
                        try:
                            # Aggregation specified. Get the interval.
                            aggregate_interval = weeutil.weeutil.nominal_spans(
                                line_options.get(
                                "aggregate_interval"
                            ))
                        except KeyError:
                            syslog.syslog(
                                syslog.LOG_ERR,
                                "HighchartsJsonGenerator: aggregate interval required for aggregate type %s"
                                % aggregate_type,
                            )
                            syslog.syslog(
                                syslog.LOG_ERR,
                                "HighchartsJsonGenerator: line type %s skipped"
                                % observation_type,
                            )
                            continue
                            
                    # use different target unit
                    special_target_unit = line_options.get("unit",None)

                    # Get the unit label
                    if observation_type == "rainTotal":
                        obs_label = "rain"
                    elif (
                        observation_type == "weatherRange"
                        and weatherRange_obs_lookup is not None
                    ):
                        obs_label = weatherRange_obs_lookup
                    else:
                        obs_label = observation_type
                    unit_label = line_options.get(
                        "yAxis_label_unit",
                        self.formatter.get_label_string(
                            special_target_unit if special_target_unit else self.converter.getTargetUnit(obs_label,aggregate_type)[0]
                        ),
                    )

                    # Set the yAxis label. Place into series for custom
                    # JavaScript. Highcharts will ignore these by default
                    yAxisLabel_config = line_options.get("yAxis_label", None)
                    # Set a default yAxis label if graphs.conf yAxis_label is
                    # none and there's a unit_label - e.g. Temperature (F)
                    if yAxisLabel_config is None and unit_label:
                        yAxis_label = name + " (" + unit_label.strip() + ")"
                    elif yAxisLabel_config and unit_label:
                        yAxis_label = (
                            yAxisLabel_config + " (" + unit_label.strip() + ")"
                        )
                    elif yAxisLabel_config:
                        yAxis_label = yAxisLabel_config
                    else:
                        # Unknown observation, set the default label to ""
                        yAxis_label = ""
                    output[chart_group][plotname]["options"][
                        "yAxis_label"
                    ] = yAxis_label
                    output[chart_group][plotname]["series"][line_name][
                        "yAxis_label"
                    ] = yAxis_label

                    # Check for average type:
                    average_type = line_options.get("average_type")
                    if average_type in (None, "", "None", "none"):
                        # No average type specified so force to none.
                        average_type = None

                    # Mirrored charts
                    mirrored_value = line_options.get("mirrored_value", None)

                    # Custom CSS
                    css_class = line_options.get("css_class", None)
                    output[chart_group][plotname]["options"]["css_class"] = css_class

                    # Setup polar charts
                    polar = line_options.get("polar", None)
                    if polar is not None and to_bool(polar):
                        # Only turn on polar if it's not none and it's true (1 or True)
                        output[chart_group][plotname]["series"][line_name][
                            "polar"
                        ] = "true"
                    else:
                        output[chart_group][plotname]["series"][line_name][
                            "polar"
                        ] = "false"

                    # This for loop is to get any user provided highcharts
                    # series config data. Built-in highcharts variable names
                    # accepted.
                    for highcharts_config, highcharts_value in self.chart_dict[
                        chart_group
                    ][plotname][line_name].items():
                        output[chart_group][plotname]["series"][line_name][
                            highcharts_config
                        ] = highcharts_value

                    # Override any highcharts series configs with standardized
                    # data, then generate the data output
                    output[chart_group][plotname]["series"][line_name]["name"] = name

                    # Set the yAxis min and max if present. Useful for the
                    # rxCheckPercent plots
                    yAxis_min = line_options.get("yAxis_min", None)
                    if yAxis_min:
                        output[chart_group][plotname]["series"][line_name][
                            "yAxis_min"
                        ] = yAxis_min
                    yAxis_max = line_options.get("yAxis_max", None)
                    if yAxis_max:
                        output[chart_group][plotname]["series"][line_name][
                            "yAxis_max"
                        ] = yAxis_max

                    # Add rounding from weewx.conf/skin.conf so Highcharts can use it
                    if observation_type == "rainTotal":
                        rounding_obs_lookup = "rain"
                    elif observation_type == "weatherRange":
                        rounding_obs_lookup = weatherRange_obs_lookup
                    elif observation_type == "haysChart":
                        rounding_obs_lookup = "windSpeed"
                    else:
                        rounding_obs_lookup = observation_type
                    try:
                        obs_group = weewx.units.obs_group_dict[rounding_obs_lookup]
                        obs_unit = self.converter.group_unit_dict[obs_group]
                        obs_round = self.skin_dict["Units"]["StringFormats"].get(
                            obs_unit, "0"
                        )[2]
                        output[chart_group][plotname]["series"][line_name][
                            "rounding"
                        ] = obs_round
                    except:
                        # Not a valid weewx schema name - maybe this is
                        # windRose or something?
                        output[chart_group][plotname]["series"][line_name][
                            "rounding"
                        ] = "-1"

                    # Set default colors, unless the user has specified
                    # otherwise in graphs.conf
                    wind_rose_color = {}
                    wind_rose_color[0] = line_options.get("beauford0", "#7cb5ec")
                    wind_rose_color[1] = line_options.get("beauford1", "#b2df8a")
                    wind_rose_color[2] = line_options.get("beauford2", "#f7a35c")
                    wind_rose_color[3] = line_options.get("beauford3", "#8c6bb1")
                    wind_rose_color[4] = line_options.get("beauford4", "#dd3497")
                    wind_rose_color[5] = line_options.get("beauford5", "#e4d354")
                    wind_rose_color[6] = line_options.get("beauford6", "#268bd2")

                    # Build series data
                    series_data = self.get_observation_data(
                        binding,
                        archive,
                        observation_type,
                        minstamp,
                        maxstamp,
                        aggregate_type,
                        aggregate_interval,
                        average_type,
                        time_length,
                        xAxis_groupby,
                        xAxis_categories,
                        mirrored_value,
                        weatherRange_obs_lookup,
                        wind_rose_color,
                        special_target_unit
                    )

                    # Build the final series data JSON
                    if isinstance(series_data, dict):
                        # If the returned type is a dict, then it's from the
                        # xAxis groupby section containing labels. Need to
                        # repack data, and update xAxis_categories.

                        # Use SQL Labels?
                        if "use_sql_labels" in series_data:
                            if series_data["use_sql_labels"]:
                                output[chart_group][plotname]["options"][
                                    "xAxis_categories"
                                ] = series_data["xAxis_groupby_labels"]
                        elif "weatherRange" in series_data:
                            output[chart_group][plotname]["series"][line_name][
                                "range_unit"
                            ] = series_data["range_unit"]
                            output[chart_group][plotname]["series"][line_name][
                                "range_unit_label"
                            ] = series_data["range_unit_label"]

                        # No matter what, reset data back to just the series
                        # data and not a dict of values
                        output[chart_group][plotname]["series"][line_name][
                            "data"
                        ] = list(series_data["obsdata"])
                    else:
                        # No custom series data overrides, so just add
                        # series_data to the chart series data
                        output[chart_group][plotname]["series"][line_name][
                            "data"
                        ] = list(series_data)

                    # Final pass through
                    # self.highcharts_series_options_to_float() to convert the
                    # remaining options with numeric values to float such that
                    # Highcharts can make use of them.
                    output[chart_group][plotname]["series"][
                        line_name
                    ] = self.highcharts_series_options_to_float(
                        output[chart_group][plotname]["series"][line_name]
                    )

            # Write the output to the JSON file
            with open(json_filename, mode="w") as jf:
                jf.write(json.dumps(output[chart_group], indent=4))

            # Save the graphs.conf to a json file for future debugging
            chart_json_filename = html_dest_dir + "/graphs.json"
            with open(chart_json_filename, mode="w") as cjf:
                cjf.write(json.dumps(self.chart_dict, indent=4))

    def get_observation_data(
        self,
        binding,
        archive,
        observation,
        start_ts,
        end_ts,
        aggregate_type,
        aggregate_interval,
        average_type,
        time_length,
        xAxis_groupby,
        xAxis_categories,
        mirrored_value,
        weatherRange_obs_lookup,
        wind_rose_color,
        special_target_unit
    ):
        """
        Get the SQL vectors for the observation, the aggregate type and the
        interval of time
        """

        if observation == "windRose":
            # Special Belchertown wind rose with Highcharts aggregator Wind
            # speeds are split into the first 7 beaufort groups.
            # https://en.wikipedia.org/wiki/Beaufort_scale

            # Force no aggregate_type
            if aggregate_type:
                aggregate_type = None

            # Force no aggregate_interval
            if aggregate_interval:
                aggregate_interval = None

            # Get windDir observations.
            obs_lookup = "windDir"
            (time_start_vt, time_stop_vt, windDir_vt) = weewx.xtypes.get_series(
                obs_lookup,
                TimeSpan(start_ts, end_ts),
                archive,
                aggregate_type,
                aggregate_interval,
            )
            # windDir_vt = self.converter.convert(windDir_vt)
            # usage_round = int(self.skin_dict['Units']['StringFormats'].get(windDir_vt[2], "0f")[-2])
            usage_round = 0  # Force round to 0 decimal
            windDir_round_vt = [self.round_none(x, usage_round) for x in windDir_vt[0]]
            # windDir_round_vt = [0.0 if v is None else v for v in windDir_round_vt]

            # Get windSpeed observations.
            obs_lookup = "windSpeed"
            (time_start_vt, time_stop_vt, windSpeed_vt) = weewx.xtypes.get_series(
                obs_lookup,
                TimeSpan(start_ts, end_ts),
                archive,
                aggregate_type,
                aggregate_interval,
            )
            windSpeed_vt = self.converter.convert(windSpeed_vt)
            usage_round = int(
                self.skin_dict["Units"]["StringFormats"].get(windSpeed_vt[2], "2f")[-2]
            )
            windSpeed_round_vt = [
                self.round_none(x, usage_round) for x in windSpeed_vt[0]
            ]

            # Exit if the vectors are None
            if windDir_vt[1] is None or windSpeed_vt[1] is None:
                empty_windrose = [{"name": "", "data": []}]
                return empty_windrose

            # Get the unit label from the skin dict for speed.
            windSpeed_unit = windSpeed_vt[1]
            windSpeed_unit_label = self.skin_dict["Units"]["Labels"][windSpeed_unit]

            # Merge the two outputs so we have a consistent data set to filter on
            merged = zip(windDir_round_vt, windSpeed_round_vt)

            # Sort by beaufort wind speeds
            (
                group_0_windDir,
                group_0_windSpeed,
                group_1_windDir,
                group_1_windSpeed,
                group_2_windDir,
                group_2_windSpeed,
                group_3_windDir,
                group_3_windSpeed,
                group_4_windDir,
                group_4_windSpeed,
                group_5_windDir,
                group_5_windSpeed,
                group_6_windDir,
                group_6_windSpeed,
            ) = ([] for i in range(14))
            for windData in merged:
                if windData[0] is not None and windData[1] is not None:
                    if windSpeed_unit in ("mile_per_hour", "mile_per_hour2"):
                        if windData[1] < 1:
                            group_0_windDir.append(windData[0])
                            group_0_windSpeed.append(windData[1])
                        elif 1 <= windData[1] <= 3:
                            group_1_windDir.append(windData[0])
                            group_1_windSpeed.append(windData[1])
                        elif 4 <= windData[1] <= 7:
                            group_2_windDir.append(windData[0])
                            group_2_windSpeed.append(windData[1])
                        elif 8 <= windData[1] <= 12:
                            group_3_windDir.append(windData[0])
                            group_3_windSpeed.append(windData[1])
                        elif 13 <= windData[1] <= 18:
                            group_4_windDir.append(windData[0])
                            group_4_windSpeed.append(windData[1])
                        elif 19 <= windData[1] <= 24:
                            group_5_windDir.append(windData[0])
                            group_5_windSpeed.append(windData[1])
                        elif windData[1] >= 25:
                            group_6_windDir.append(windData[0])
                            group_6_windSpeed.append(windData[1])
                    elif windSpeed_unit in ("km_per_hour", "km_per_hour2"):
                        if windData[1] < 2:
                            group_0_windDir.append(windData[0])
                            group_0_windSpeed.append(windData[1])
                        elif 2 <= windData[1] <= 5:
                            group_1_windDir.append(windData[0])
                            group_1_windSpeed.append(windData[1])
                        elif 6 <= windData[1] <= 11:
                            group_2_windDir.append(windData[0])
                            group_2_windSpeed.append(windData[1])
                        elif 12 <= windData[1] <= 19:
                            group_3_windDir.append(windData[0])
                            group_3_windSpeed.append(windData[1])
                        elif 20 <= windData[1] <= 28:
                            group_4_windDir.append(windData[0])
                            group_4_windSpeed.append(windData[1])
                        elif 29 <= windData[1] <= 38:
                            group_5_windDir.append(windData[0])
                            group_5_windSpeed.append(windData[1])
                        elif windData[1] >= 39:
                            group_6_windDir.append(windData[0])
                            group_6_windSpeed.append(windData[1])
                    elif windSpeed_unit in ("meter_per_second", "meter_per_second2"):
                        if windData[1] < 0.5:
                            group_0_windDir.append(windData[0])
                            group_0_windSpeed.append(windData[1])
                        elif 0.5 <= windData[1] <= 1.5:
                            group_1_windDir.append(windData[0])
                            group_1_windSpeed.append(windData[1])
                        elif 1.6 <= windData[1] <= 3.3:
                            group_2_windDir.append(windData[0])
                            group_2_windSpeed.append(windData[1])
                        elif 3.4 <= windData[1] <= 5.5:
                            group_3_windDir.append(windData[0])
                            group_3_windSpeed.append(windData[1])
                        elif 5.6 <= windData[1] <= 7.9:
                            group_4_windDir.append(windData[0])
                            group_4_windSpeed.append(windData[1])
                        elif 8 <= windData[1] <= 10.7:
                            group_5_windDir.append(windData[0])
                            group_5_windSpeed.append(windData[1])
                        elif windData[1] >= 10.8:
                            group_6_windDir.append(windData[0])
                            group_6_windSpeed.append(windData[1])
                    elif windSpeed_unit in ("knot", "knot2"):
                        if windData[1] < 1:
                            group_0_windDir.append(windData[0])
                            group_0_windSpeed.append(windData[1])
                        elif 1 <= windData[1] <= 3:
                            group_1_windDir.append(windData[0])
                            group_1_windSpeed.append(windData[1])
                        elif 4 <= windData[1] <= 6:
                            group_2_windDir.append(windData[0])
                            group_2_windSpeed.append(windData[1])
                        elif 7 <= windData[1] <= 10:
                            group_3_windDir.append(windData[0])
                            group_3_windSpeed.append(windData[1])
                        elif 11 <= windData[1] <= 16:
                            group_4_windDir.append(windData[0])
                            group_4_windSpeed.append(windData[1])
                        elif 17 <= windData[1] <= 21:
                            group_5_windDir.append(windData[0])
                            group_5_windSpeed.append(windData[1])
                        elif windData[1] >= 22:
                            group_6_windDir.append(windData[0])
                            group_6_windSpeed.append(windData[1])
                    elif windSpeed_unit == "beaufort":
                        if windData[1] <= 1:
                            group_0_windDir.append(windData[0])
                            group_0_windSpeed.append(windData[1])
                        elif windData[1] == 2:
                            group_1_windDir.append(windData[0])
                            group_1_windSpeed.append(windData[1])
                        elif windData[1] == 3:
                            group_2_windDir.append(windData[0])
                            group_2_windSpeed.append(windData[1])
                        elif windData[1] == 4:
                            group_3_windDir.append(windData[0])
                            group_3_windSpeed.append(windData[1])
                        elif windData[1] == 5:
                            group_4_windDir.append(windData[0])
                            group_4_windSpeed.append(windData[1])
                        elif windData[1] == 6:
                            group_5_windDir.append(windData[0])
                            group_5_windSpeed.append(windData[1])
                        elif windData[1] >= 7:
                            group_6_windDir.append(windData[0])
                            group_6_windSpeed.append(windData[1])

            # Get the windRose data
            group_0_series_data = self.create_windrose_data(
                group_0_windDir, group_0_windSpeed
            )
            group_1_series_data = self.create_windrose_data(
                group_1_windDir, group_1_windSpeed
            )
            group_2_series_data = self.create_windrose_data(
                group_2_windDir, group_2_windSpeed
            )
            group_3_series_data = self.create_windrose_data(
                group_3_windDir, group_3_windSpeed
            )
            group_4_series_data = self.create_windrose_data(
                group_4_windDir, group_4_windSpeed
            )
            group_5_series_data = self.create_windrose_data(
                group_5_windDir, group_5_windSpeed
            )
            group_6_series_data = self.create_windrose_data(
                group_6_windDir, group_6_windSpeed
            )

            # Group all together to get wind frequency percentages
            wind_sum = sum(
                group_0_series_data
                + group_1_series_data
                + group_2_series_data
                + group_3_series_data
                + group_4_series_data
                + group_5_series_data
                + group_6_series_data
            )
            if wind_sum > 0:
                y = 0
                while y < len(group_0_series_data):
                    group_0_series_data[y] = round(
                        group_0_series_data[y] / wind_sum * 100
                    )
                    y += 1
                y = 0
                while y < len(group_1_series_data):
                    group_1_series_data[y] = round(
                        group_1_series_data[y] / wind_sum * 100
                    )
                    y += 1
                y = 0
                while y < len(group_2_series_data):
                    group_2_series_data[y] = round(
                        group_2_series_data[y] / wind_sum * 100
                    )
                    y += 1
                y = 0
                while y < len(group_3_series_data):
                    group_3_series_data[y] = round(
                        group_3_series_data[y] / wind_sum * 100
                    )
                    y += 1
                y = 0
                while y < len(group_4_series_data):
                    group_4_series_data[y] = round(
                        group_4_series_data[y] / wind_sum * 100
                    )
                    y += 1
                y = 0
                while y < len(group_5_series_data):
                    group_5_series_data[y] = round(
                        group_5_series_data[y] / wind_sum * 100
                    )
                    y += 1
                y = 0
                while y < len(group_6_series_data):
                    group_6_series_data[y] = round(
                        group_6_series_data[y] / wind_sum * 100
                    )
                    y += 1

            # Setup the labels based on unit
            if windSpeed_unit in ("mile_per_hour", "mile_per_hour2"):
                group_0_speedRange = "< 1"
                group_1_speedRange = "1-3"
                group_2_speedRange = "4-7"
                group_3_speedRange = "8-12"
                group_4_speedRange = "13-18"
                group_5_speedRange = "19-24"
                group_6_speedRange = "25+"
            elif windSpeed_unit in ("km_per_hour", "km_per_hour2"):
                group_0_speedRange = "< 2"
                group_1_speedRange = "2-5"
                group_2_speedRange = "6-11"
                group_3_speedRange = "12-19"
                group_4_speedRange = "20-28"
                group_5_speedRange = "29-38"
                group_6_speedRange = "39+"
            elif windSpeed_unit in ("meter_per_second", "meter_per_second2"):
                group_0_speedRange = "< 0.5"
                group_1_speedRange = "0.5-1.5"
                group_2_speedRange = "1.6-3.3"
                group_3_speedRange = "3.4-5.5"
                group_4_speedRange = "5.5-7.9"
                group_5_speedRange = "8-10.7"
                group_6_speedRange = "10.8+"
            elif windSpeed_unit in ("knot", "knot2"):
                group_0_speedRange = "< 1"
                group_1_speedRange = "1-3"
                group_2_speedRange = "4-6"
                group_3_speedRange = "7-10"
                group_4_speedRange = "11-16"
                group_5_speedRange = "17-21"
                group_6_speedRange = "22+"
            elif windSpeed_unit == "beaufort":
                group_0_speedRange = "0"
                group_1_speedRange = "1"
                group_2_speedRange = "2"
                group_3_speedRange = "3"
                group_4_speedRange = "4"
                group_5_speedRange = "5"
                group_6_speedRange = "6+"

            group_0_name = "%s %s" % (group_0_speedRange, windSpeed_unit_label)
            group_1_name = "%s %s" % (group_1_speedRange, windSpeed_unit_label)
            group_2_name = "%s %s" % (group_2_speedRange, windSpeed_unit_label)
            group_3_name = "%s %s" % (group_3_speedRange, windSpeed_unit_label)
            group_4_name = "%s %s" % (group_4_speedRange, windSpeed_unit_label)
            group_5_name = "%s %s" % (group_5_speedRange, windSpeed_unit_label)
            group_6_name = "%s %s" % (group_6_speedRange, windSpeed_unit_label)

            group_0 = {
                "name": group_0_name,
                "type": "column",
                "color": wind_rose_color[0],
                "zIndex": 106,
                "stacking": "normal",
                "fillOpacity": 0.75,
                "data": group_0_series_data,
            }
            group_1 = {
                "name": group_1_name,
                "type": "column",
                "color": wind_rose_color[1],
                "zIndex": 105,
                "stacking": "normal",
                "fillOpacity": 0.75,
                "data": group_1_series_data,
            }
            group_2 = {
                "name": group_2_name,
                "type": "column",
                "color": wind_rose_color[2],
                "zIndex": 104,
                "stacking": "normal",
                "fillOpacity": 0.75,
                "data": group_2_series_data,
            }
            group_3 = {
                "name": group_3_name,
                "type": "column",
                "color": wind_rose_color[3],
                "zIndex": 103,
                "stacking": "normal",
                "fillOpacity": 0.75,
                "data": group_3_series_data,
            }
            group_4 = {
                "name": group_4_name,
                "type": "column",
                "color": wind_rose_color[4],
                "zIndex": 102,
                "stacking": "normal",
                "fillOpacity": 0.75,
                "data": group_4_series_data,
            }
            group_5 = {
                "name": group_5_name,
                "type": "column",
                "color": wind_rose_color[5],
                "zIndex": 101,
                "stacking": "normal",
                "fillOpacity": 0.75,
                "data": group_5_series_data,
            }
            group_6 = {
                "name": group_6_name,
                "type": "column",
                "color": wind_rose_color[6],
                "zIndex": 100,
                "stacking": "normal",
                "fillOpacity": 0.75,
                "data": group_6_series_data,
            }

            # Append everything into a list and return right away, do not
            # process rest of function
            series = [group_0, group_1, group_2, group_3, group_4, group_5, group_6]
            return series

        # Special Belchertown Weather Range (radial)
        # https://www.highcharts.com/blog/tutorials/209-the-art-of-the-chart-weather-radials/
        if observation == "weatherRange":

            # Define what we are looking up
            if weatherRange_obs_lookup is not None:
                obs_lookup = weatherRange_obs_lookup
            else:
                raise Warning(
                    "Error trying to create the weather range graph. "
                    "You are missing the range_type configuration item."
                )

            # Force 1 day if aggregate_interval. These charts are meant to show
            # a column range for high, low and average for a full day.
            if not aggregate_interval:
                aggregate_interval = 86400

            # Get min values
            aggregate_type = "min"
            try:
                (time_start_vt, time_stop_vt, obs_vt) = weewx.xtypes.get_series(
                    obs_lookup,
                    TimeSpan(start_ts, end_ts),
                    archive,
                    aggregate_type,
                    aggregate_interval,
                )
            except Exception as e:
                raise Warning(
                    "Error trying to use database binding %s to graph observation %s. "
                    "Error was: %s." % (binding, obs_lookup, e)
                )

            self.insert_null_value_timestamps_to_end_ts(time_start_vt, time_stop_vt, obs_vt, start_ts, end_ts, aggregate_interval)

            min_obs_vt = self.converter.convert(obs_vt)

            # Get max values
            aggregate_type = "max"
            try:
                (time_start_vt, time_stop_vt, obs_vt) = weewx.xtypes.get_series(
                    obs_lookup,
                    TimeSpan(start_ts, end_ts),
                    archive,
                    aggregate_type,
                    aggregate_interval,
                )
            except Exception as e:
                raise Warning(
                    "Error trying to use database binding %s to graph observation %s. "
                    "Error was: %s." % (binding, obs_lookup, e)
                )

            self.insert_null_value_timestamps_to_end_ts(time_start_vt, time_stop_vt, obs_vt, start_ts, end_ts, aggregate_interval)

            max_obs_vt = self.converter.convert(obs_vt)

            # Get avg values
            aggregate_type = "avg"
            try:
                (time_start_vt, time_stop_vt, obs_vt) = weewx.xtypes.get_series(
                    obs_lookup,
                    TimeSpan(start_ts, end_ts),
                    archive,
                    aggregate_type,
                    aggregate_interval,
                )
            except Exception as e:
                raise Warning(
                    "Error trying to use database binding %s to graph observation %s. "
                    "Error was: %s." % (binding, obs_lookup, e)
                )

            self.insert_null_value_timestamps_to_end_ts(time_start_vt, time_stop_vt, obs_vt, start_ts, end_ts, aggregate_interval)

            avg_obs_vt = self.converter.convert(obs_vt)

            obs_unit = avg_obs_vt[1]
            obs_unit_label = self.skin_dict["Units"]["Labels"].get(obs_unit, "")

            # Convert to millis and zip all together
            time_ms = [float(x) * 1000 for x in time_start_vt[0]]
            output_data = zip(time_ms, min_obs_vt[0], max_obs_vt[0], avg_obs_vt[0])

            data = {
                "weatherRange": True,
                "obsdata": output_data,
                "range_unit": obs_unit,
                "range_unit_label": obs_unit_label,
            }

            return data

        if observation == "aqiChart":
            data = {"aqiChart": True, "obsdata": [{"y": aqi, "category": aqi_category}]}
            return data

        # Hays chart
        if observation == "haysChart":

            start_ts = int(start_ts)
            end_ts = int(end_ts)

            # Set aggregate interval based on timespan and make sure it is
            # between 5 minutes and 1 day
            logging.debug("Start time is %s and end time is %s" % (start_ts, end_ts))
            aggregate_interval = (end_ts - start_ts) / 360
            if aggregate_interval < 300:
                aggregate_interval = 300
            elif aggregate_interval > 86400:
                aggregate_interval = 86400
            logging.debug("Interval is: %s" % aggregate_interval)

            aggregate_type = "max"
            # Get min values
            obs_lookup = "windSpeed"
            try:
                (time_start_vt, time_stop_vt, obs_vt) = weewx.xtypes.get_series(
                    obs_lookup,
                    TimeSpan(start_ts, end_ts),
                    archive,
                    aggregate_type,
                    aggregate_interval,
                )
            except Exception as e:
                raise Warning(
                    "Error trying to use database binding %s to graph observation %s. "
                    "Error was: %s." % (binding, obs_lookup, e)
                )

            self.insert_null_value_timestamps_to_end_ts(time_start_vt, time_stop_vt, obs_vt, start_ts, end_ts, aggregate_interval)
            
            min_obs_vt = self.converter.convert(obs_vt)

            # Get max values
            obs_lookup = "windGust"
            try:
                (time_start_vt, time_stop_vt, obs_vt) = weewx.xtypes.get_series(
                    obs_lookup,
                    TimeSpan(start_ts, end_ts),
                    archive,
                    aggregate_type,
                    aggregate_interval,
                )
            except Exception as e:
                raise Warning(
                    "Error trying to use database binding %s to graph observation %s. "
                    "Error was: %s." % (binding, obs_lookup, e)
                )

            self.insert_null_value_timestamps_to_end_ts(time_start_vt, time_stop_vt, obs_vt, start_ts, end_ts, aggregate_interval)
            
            max_obs_vt = self.converter.convert(obs_vt)

            obs_unit = max_obs_vt[1]
            obs_unit_label = self.skin_dict["Units"]["Labels"].get(obs_unit, "")

            # Convert to millis and zip all together
            time_ms = [float(x) * 1000 for x in time_start_vt[0]]
            output_data = zip(time_ms, min_obs_vt[0], max_obs_vt[0])

            data = {
                "haysChart": True,
                "obsdata": output_data,
                "range_unit": obs_unit,
                "range_unit_label": obs_unit_label,
            }

            return data

        # Special Belchertown Skin rain counter
        if observation == "rainTotal":
            obs_lookup = "rain"
            # Force sum on this observation
            if aggregate_interval:
                aggregate_type = "sum"
        elif observation == "rainRate":
            obs_lookup = "rainRate"
            # Force max on this observation
            if aggregate_interval:
                aggregate_type = "max"
        else:
            obs_lookup = observation
            
        #   Special aggregation_subtype measures to enable average rainfall, max and min temperatures to be calculated
        
        if aggregate_type == "avg" and observation == "avgRainfall" and aggregate_interval == 86400:
            obs_lookup = "rain"
            obs_label = "Rainfall"

        if xAxis_groupby or len(xAxis_categories) >= 1:
            # Setup the converter - for some reason self.converter doesn't work
            # for the group_unit_dict in this section Get the target unit
            # nickname (something like 'US' or 'METRIC'):
            target_unit_nickname = self.config_dict["StdConvert"]["target_unit"]
            # Get the target unit: weewx.US, weewx.METRIC, weewx.METRICWX
            target_unit = weewx.units.unit_constants[target_unit_nickname.upper()]
            # Bind to the appropriate standard converter units
            converter = weewx.units.StdUnitConverters[target_unit]

            # Find what kind of database we're working with and specify the
            # correctly tailored SQL Query for each type of database
            data_binding = self.config_dict["StdArchive"]["data_binding"]
            database = self.config_dict["DataBindings"][data_binding]["database"]
            database_type = self.config_dict["Databases"][database]["database_type"]
            driver = self.config_dict["DatabaseTypes"][database_type]["driver"]
            xAxis_labels = []
            obsvalues = []

            # Define the xAxis group by for the sql query. Default to month
            if xAxis_groupby == "hour":
                strformat = "%H"
            elif xAxis_groupby == "day":
                strformat = "%d"
            elif xAxis_groupby == "month":
                strformat = "%m"
            elif xAxis_groupby == "year":
                strformat = "%Y"
            elif xAxis_groupby == "":
                strformat = "%m"
            else:
                strformat = "%m"

            # Default catch all in case the aggregate_type isn't defined, default to sum
            if aggregate_type is None:
                aggregate_type = "sum"

            if isinstance(time_length, int):
                order_sql = ' ORDER BY dateTime ASC'
            else:
                order_sql = ''

            # Special case for time_length = all, force to use complete days only
            if time_length == "all":
                start_ts = startOfDay(archive.firstGoodStamp()) + 86400
                end_ts = startOfDay(archive.lastGoodStamp())

            # Set up subquery groupby clause
            if xAxis_groupby == "year": subqry_groupby = '"%Y"'
            elif xAxis_groupby == "month": subqry_groupby = '"%Y%m"'
            elif xAxis_groupby == "day": subqry_groupby = '"%Y%m%d"'
            elif xAxis_groupby == "hour": subqry_groupby = '"%Y%m%d%H"'
            else: subqry_groupby = ''
                            
            if driver == "weedb.sqlite":
                # Use daily summaries where possible - MUST BE FOR WHOLE DAYS determined by start and stop times otherwise use archive
                if xAxis_groupby != "hour" and isStartOfDay(start_ts) and isStartOfDay(end_ts) and end_ts - start_ts > 0 :  # 1 or more exact days
                    # Avg is a special case
                    if aggregate_type == "avg":
                        # Avg(sum) requires a subquery with the correct group by clause
                        if average_type is not None and average_type == "sum":
                            sql_lookup = 'SELECT dt1 AS {0}, ' \
                                         'AVG(obs1) AS obs ' \
                                         'FROM (SELECT strftime("{1}", datetime(dateTime, "unixepoch", "localtime")) AS dt1, sum(sum) AS obs1 ' \
                                                'FROM archive_day_{2} WHERE dateTime >= {3} AND dateTime < {4} '\
                                                'GROUP BY strftime({5}, datetime(dateTime, "unixepoch", "localtime"))) ' \
                                         'GROUP BY {0}{6};'.format(
                                xAxis_groupby,
                                strformat,
                                obs_lookup,
                                start_ts,
                                end_ts,
                                subqry_groupby,
                                order_sql
                            )
                        # avg cases with an average_type
                        elif average_type is not None:
                            sql_lookup = 'SELECT strftime("{0}", datetime(dateTime, "unixepoch", "localtime")) AS {1}, ' \
                                         '{2}({3}) AS obs ' \
                                         'FROM archive_day_{4}  WHERE dateTime >= {5} AND dateTime < {6} ' \
                                         'GROUP BY {1}{7};'.format(
                                strformat,
                                xAxis_groupby,
                                aggregate_type,
                                average_type,
                                obs_lookup,
                                start_ts,
                                end_ts,
                                order_sql
                            )
                        # remaining avg cases without an average_type use weighted average
                        else:
                            sql_lookup = 'SELECT strftime("{0}", datetime(dateTime, "unixepoch", "localtime")) AS {1}, ' \
                                         'SUM(wsum)/SUM(sumtime) AS obs ' \
                                         'FROM archive_day_{2}  WHERE dateTime >= {3} AND dateTime < {4} ' \
                                         'GROUP BY {1}{5};'.format(
                                strformat,
                                xAxis_groupby,
                                obs_lookup,
                                start_ts,
                                end_ts,
                                order_sql
                            )
                    # other aggregate_type cases use direct interrogation of daily summary
                    else:
                        sql_lookup = 'SELECT strftime("{0}", datetime(dateTime, "unixepoch", "localtime")) AS {1}, ' \
                                     '{2}({2}) AS obs ' \
                                     'FROM archive_day_{3}  ' \
                                     'WHERE dateTime >= {4} AND dateTime < {5} GROUP BY {1}{6};'.format(
                            strformat,
                            xAxis_groupby,
                            aggregate_type,
                            obs_lookup,
                            start_ts,
                            end_ts,
                            order_sql
                        )
                else:
                    # archive access with no average_type
                    if average_type is None:
                        sql_lookup = 'SELECT strftime("{0}", datetime(dateTime, "unixepoch", "localtime")) as {1}, ' \
                                     'IFNULL({2}({3}),0) AS obs, dateTime FROM archive ' \
                                     'WHERE dateTime >= {4} AND dateTime < {5} GROUP BY {1}{6};'.format(
                            strformat,
                            xAxis_groupby,
                            aggregate_type,
                            obs_lookup,
                            start_ts,
                            end_ts,
                            order_sql
                        )

                    # average_type requiring a subquery
                    else:
                        sql_lookup = 'SELECT dt1 AS {0}, ' \
                                     '{1}(obs1) AS obs ' \
                                     'FROM (SELECT strftime("{2}", datetime(dateTime, "unixepoch", "localtime")) AS dt1, '\
                                            'IFNULL({3}({4}),0) AS obs1 ' \
                                            'FROM archive WHERE dateTime >= {5} AND dateTime < {6} '\
                                            'GROUP BY strftime({7}, datetime(dateTime, "unixepoch", "localtime"))) ' \
                                     'GROUP BY {0}{8};'.format(
                            xAxis_groupby,
                            aggregate_type,
                            strformat,
                            average_type,
                            obs_lookup,
                            start_ts,
                            end_ts,
                            subqry_groupby,
                            order_sql
                        )

            elif driver == "weedb.mysql":
                # Use daily summaries where possible - MUST BE FOR WHOLE DAYS determined by start and stop times otherwise use archive
                if xAxis_groupby != "hour" and isStartOfDay(start_ts) and isStartOfDay(end_ts) and end_ts - start_ts > 0 :  # 1 or more exact days
                    # Avg is a special case
                    if aggregate_type == "avg":
                        # Avg(sum) requires a subquery with the correct group by clause
                        if average_type is not None and average_type == "sum":
                            sql_lookup = 'SELECT dt1 AS {0}, ' \
                                         'AVG(obs1) AS obs ' \
                                         'FROM (SELECT FROM_UNIXTIME( dateTime, "%{1}" ) AS dt1, sum(sum) AS obs1 ' \
                                                'FROM archive_day_{2} WHERE dateTime >= {3} AND dateTime < {4} '\
                                                'GROUP BY strftime({5}, datetime(dateTime, "unixepoch", "localtime"))) ' \
                                         'GROUP BY {0}{6};'.format(
                                xAxis_groupby,
                                strformat,
                                obs_lookup,
                                start_ts,
                                end_ts,
                                subqry_groupby,
                                order_sql
                            )
                        # avg cases with an average_type
                        elif average_type is not None:
                            sql_lookup = 'SELECT FROM_UNIXTIME( dateTime, "%{0}" ) AS {1}, ' \
                                         '{2}({3}) AS obs ' \
                                         'FROM archive_day_{4}  WHERE dateTime >= {5} AND dateTime < {6} ' \
                                         'GROUP BY {1}{7};'.format(
                                strformat,
                                xAxis_groupby,
                                aggregate_type,
                                average_type,
                                obs_lookup,
                                start_ts,
                                end_ts,
                                order_sql
                            )
                        # remaining avg cases without an average_type use weighted average
                        else:
                            sql_lookup = 'SELECT FROM_UNIXTIME( dateTime, "%{0}" ) AS {1}, ' \
                                         'SUM(wsum)/SUM(sumtime) AS obs ' \
                                         'FROM archive_day_{2}  WHERE dateTime >= {3} AND dateTime < {4} ' \
                                         'GROUP BY {1}{5};'.format(
                                strformat,
                                xAxis_groupby,
                                obs_lookup,
                                start_ts,
                                end_ts,
                                order_sql
                            )
                    # other aggregate_type cases use direct interrogation of daily summary
                    else:
                        sql_lookup = 'SELECT FROM_UNIXTIME( dateTime, "%{0}" ) AS {1}, ' \
                                     '{2}({2}) AS obs ' \
                                     'FROM archive_day_{3}  ' \
                                     'WHERE dateTime >= {4} AND dateTime < {5} GROUP BY {1}{6};'.format(
                            strformat,
                            xAxis_groupby,
                            aggregate_type,
                            obs_lookup,
                            start_ts,
                            end_ts,
                            order_sql
                        )
                else:
                    # archive access with no average_type
                    if average_type is None:
                        sql_lookup = 'SELECT FROM_UNIXTIME( dateTime, "%{0}" ) as {1}, ' \
                                     'IFNULL({2}({3}),0) AS obs, dateTime FROM archive ' \
                                     'WHERE dateTime >= {4} AND dateTime < {5} GROUP BY {1}{6};'.format(
                            strformat,
                            xAxis_groupby,
                            aggregate_type,
                            obs_lookup,
                            start_ts,
                            end_ts,
                            order_sql
                        )

                    # average_type requiring a subquery
                    else:
                        sql_lookup = 'SELECT dt1 AS {0}, ' \
                                     '{1}(obs1) AS obs ' \
                                     'FROM (SELECT FROM_UNIXTIME( dateTime, "%{2}" ) AS dt1, '\
                                            'IFNULL({3}({4}),0) AS obs1 ' \
                                            'FROM archive WHERE dateTime >= {5} AND dateTime < {6} '\
                                            'GROUP BY strftime({7}, datetime(dateTime, "unixepoch", "localtime"))) ' \
                                     'GROUP BY {0}{8};'.format(
                            xAxis_groupby,
                            aggregate_type,
                            strformat,
                            average_type,
                            obs_lookup,
                            start_ts,
                            end_ts,
                            subqry_groupby,
                            order_sql
                        )

            # Setup values for the converter
            try:
                obs_group = weewx.units.obs_group_dict[obs_lookup]
                obs_unit_from_target_unit = converter.group_unit_dict[obs_group]
            except:
                # This observation doesn't exist within weewx schema so nothing
                # to convert, so set None type
                obs_group = None
                obs_unit_from_target_unit = None

            # introduce test to catch any sql errors; a try / except sequence 
            
            try:
                query = archive.genSql(sql_lookup)
            except:
                raise Warning(
                    "SQL error in"
                    "sql_lookup"
                    "The error is: %s"
                        % (error)                    
                )
                
            for row in query:
                xAxis_labels.append(row[0])
                row_tuple = (row[1], obs_unit_from_target_unit, obs_group)
                if special_target_unit:
                    row_converted = weewx.units.convert(row_tuple, special_target_unit)
                else:
                    row_converted = self.converter.convert(row_tuple)
                obsvalues.append(row_converted[0])

            # If the values are to be mirrored, we need to make them negative
            if mirrored_value:
                for i in obsvalues:
                    if i is not None:
                        i = -i

            # Return a dict which has the value for if we need to add labels
            # from sql or not.
            if len(xAxis_categories) == 0:
                data = {
                    "use_sql_labels": True,
                    "xAxis_groupby_labels": xAxis_labels,
                    "obsdata": obsvalues,
                }
            else:
                data = {
                    "use_sql_labels": False,
                    "xAxis_groupby_labels": "",
                    "obsdata": obsvalues,
                }
            return data

        # Begin standard observation lookups
        try:
            (time_start_vt, time_stop_vt, obs_vt) = weewx.xtypes.get_series(
                obs_lookup,
                TimeSpan(start_ts, end_ts),
                archive,
                aggregate_type,
                aggregate_interval,
            )
        except Exception as e:
            raise Warning(
                "Error trying to use database binding %s to graph observation %s. Error was: %s."
                % (binding, obs_lookup, e)
            )

        self.insert_null_value_timestamps_to_end_ts(time_start_vt, time_stop_vt, obs_vt, start_ts, end_ts, aggregate_interval)
        
        if special_target_unit:
            logdbg("unit_group=%s source_unit=%s special_target_unit=%s" % (obs_vt[2],obs_vt[1],special_target_unit))
            obs_vt = weewx.units.Converter({obs_vt[2]:special_target_unit}).convert(obs_vt)
        else:
            obs_vt = self.converter.convert(obs_vt)

        # Special handling for the rain.
        if observation == "rainTotal":
            # The weewx "rain" observation is really "bucket tips". This
            # special counter increments the bucket tips over timespan to
            # return rain total.
            rain_count = 0
            obs_round_vt = []
            for rain in obs_vt[0]:
                # If the rain value is None or "", add it as 0.0
                if rain is None or rain == "":
                    # rain = 0.0
                    # Do not keep adding None or empty results, so that
                    # full-length charts (like weewx v4 archiveYearSpan) don't
                    # have a line that continues past the last actual plot
                    obs_round_vt.append(rain)
                    continue
                rain_count = rain_count + rain
                obs_round_vt.append(round(rain_count, 2))
        else:
            # Send all other observations through the usual process, except
            # Barometer for finer detail
            if observation == "barometer":
                usage_round = int(
                    self.skin_dict["Units"]["StringFormats"].get(obs_vt[1], "1f")[-2]
                )
                obs_round_vt = [
                    round(x, usage_round) if x is not None else None for x in obs_vt[0]
                ]
            else:
                try:
                   usage_round = int(
                       self.skin_dict["Units"]["StringFormats"].get(obs_vt[1], "2f")[-2]
                   )
                except ValueError:
                   loginf (
                      "Observation %s is using unit %s that returns %s for StringFormat, rather than float point decimal format value - using 0 as rounding"
                      % (observation, obs_vt[1], self.skin_dict["Units"]["StringFormats"].get(obs_vt[1]))
                   )
                   usage_round = 0

                obs_round_vt = [self.round_none(x, usage_round) for x in obs_vt[0]]

        # "Today" charts, "timespan_specific" charts and floating timespan
        # charts have the point timestamp on the stop time so we don't see the
        # previous minute in the tooltip. (e.g. 4:59 instead of 5:00)
        # Everything else has it on the start time so we don't see the next day
        # in the tooltip (e.g. Jan 2 instead of Jan 1)
        try:
            if not aggregate_type:
                point_timestamp = time_stop_vt
            elif aggregate_interval and (
                      aggregate_interval == 3600 or aggregate_interval==2629800):
                point_timestamp = time_start_vt
            else:
                point_timestamp = ([(x+y)/2.0 for x,y in zip(time_start_vt[0],time_stop_vt[0])],time_start_vt[1],time_start_vt[2])
        except Exception:
            point_timestamp = time_stop_vt

        # If the values are to be mirrored, we need to make them negative
        if mirrored_value:
            for i in range(len(obs_round_vt)):
                if obs_round_vt[i] is not None:
                    obs_round_vt[i] = -obs_round_vt[i]

        time_ms = [float(x) * 1000 for x in point_timestamp[0]]
        data = zip(time_ms, obs_round_vt)

        return data

    def insert_null_value_timestamps_to_end_ts(self, time_start_vt, time_stop_vt, obs_vt, start_ts, end_ts, interval):
        """
        In weewx 4.5.1 xtypes.py was modified to not return any data points which didn't exist in the archive database.
        This function adds the 'future' data points from the last timestamp in the list up until end_ts with None entries.
        This means that graphs still have the option of showing a full day or month or year on the x axis depending on the time_length specfied.       
        """
        count = 0

        if interval is not None:
            try:
                ts = time_start_vt[0][-1] + interval
            except:
                ts = start_ts

            while ts < end_ts:
                time_start_vt[0].append(ts)
                time_stop_vt[0].append(ts)
                ts = ts + interval
                count = count + 1

        for i in range(count):
           obs_vt[0].append(None)

    def round_none(self, value, places):
        """Round value to 'places' places but also permit a value of None"""
        if value is not None:
            try:
                value = round(value, places)
            except:
                value = None
        return value

    def timespan_year_to_now(self, time_ts, grace=1, years_ago=0):
        """
        In weewx 4 the get_series() for archiveYearSpan returns the full 365
        day chart.  if users do not want a full year (with empty data) and
        would rather a Jan 1 to "now", then they can use this custom timespan

        This is taken right from weewx, but adapted to end at the current
        timestamp, and not the following Jan 1.
        """
        if time_ts is None:
            return None
        time_ts -= grace
        _day_date = datetime.date.fromtimestamp(time_ts)
        return TimeSpan(
            int(time.mktime((_day_date.year - years_ago, 1, 1, 0, 0, 0, 0, 0, -1))),
            int(float(time_ts)),
        )

    def create_windrose_data(self, windDir_list, windSpeed_list):
        # List comprehension borrowed from weewx-wd extension
        # Create windrose_list container and initialise to all 0s
        windrose_list = [0.0 for x in range(16)]

        # Step through each windDir and add corresponding windSpeed to windrose_list
        x = 0
        while x < len(windDir_list):
            # Only want to add windSpeed if both windSpeed and windDir have a value
            if windSpeed_list[x] is not None and windDir_list[x] is not None:
                # Add the windSpeed value to the corresponding element of our
                # windrose list
                windrose_list[
                    int((windDir_list[x] + 11.25) / 22.5) % 16
                ] += windSpeed_list[x]
            x += 1

        # Step through our windrose list and round all elements to 1 decimal place
        y = 0
        while y < len(windrose_list):
            windrose_list[y] = round(windrose_list[y], 1)
            y += 1
        # Need to return a string of the list elements comma separated, no
        # spaces and bounded by [ and ]
        # windroseData = '[' + ','.join(str(z) for z in windrose_list) + ']'
        return windrose_list

    def get_cardinal_direction(self, degree):
        if 0 <= degree <= 11.25:
            return "N"
        if 11.26 <= degree <= 33.75:
            return "NNE"
        if 33.76 <= degree <= 56.25:
            return "NE"
        if 56.26 <= degree <= 78.75:
            return "ENE"
        if 78.76 <= degree <= 101.25:
            return "E"
        if 101.26 <= degree <= 123.75:
            return "ESE"
        if 123.76 <= degree <= 146.25:
            return "SE"
        if 146.26 <= degree <= 168.75:
            return "SSE"
        if 168.76 <= degree <= 191.25:
            return "S"
        if 191.26 <= degree <= 213.75:
            return "SSW"
        if 213.76 <= degree <= 236.25:
            return "SW"
        if 236.26 <= degree <= 258.75:
            return "WSW"
        if 258.76 <= degree <= 281.25:
            return "W"
        if 281.26 <= degree <= 303.75:
            return "WNW"
        if 303.76 <= degree <= 326.25:
            return "NW"
        if 326.26 <= degree <= 348.75:
            return "NNW"
        if 348.76 <= degree <= 360:
            return "N"

    def highcharts_series_options_to_float(self, d):
        """
        Recurse through all the series options and set any strings that
        should be numbers to float.
        https://stackoverflow.com/a/54565277/1177153
        """

        try:
            for k, v in d.items():
                if isinstance(v, dict):
                    # Check nested dicts
                    self.highcharts_series_options_to_float(v)
                else:
                    try:
                        v = to_float(v)
                        d.update({k: v})
                    except:
                        pass
            return d
        except:
            # This item isn't a dict, so return it back
            return d
