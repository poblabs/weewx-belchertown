# Installer for Belchertown weewx skin
# Pat O'Brien, 2018

import configobj
from setup import ExtensionInstaller

try:
    # Python 2
    from StringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO

#-------- extension info -----------

VERSION      = "1.3.1"
NAME         = 'Belchertown'
DESCRIPTION  = 'A clean modern skin with real time streaming updates and interactive charts. Modeled after BelchertownWeather.com'
AUTHOR       = "Pat OBrien"
AUTHOR_EMAIL = "https://github.com/poblabs/weewx-belchertown"

#-------- main loader -----------

def loader():
    return BelchertownInstaller()

class BelchertownInstaller(ExtensionInstaller):
    def __init__(self):
        super(BelchertownInstaller, self).__init__(
            version=VERSION,
            name=NAME,
            description=DESCRIPTION,
            author=AUTHOR,
            author_email=AUTHOR_EMAIL,
            config=config_dict,
            files=files_dict
        )

#----------------------------------
#         config stanza
#----------------------------------

extension_config = """
[StdReport]

    [[Belchertown]]
        skin = Belchertown
        HTML_ROOT = belchertown
        enable = true 

        [[[Extras]]]

           # For help refer to the docs at https://github.com/poblabs/weewx-belchertown
           # and consult skin.conf for the configurable elements and their hierarchy

           #--- General Options ---
           # belchertown_debug = 0
           # belchertown_locale = "auto"
           # theme = light
           # theme_toggle_enabled = 1
           # logo_image = ""
           # logo_image_dark = ""
           # site_title = "My Weather Website"
           # station_observations = "barometer","dewpoint","outHumidity","rainWithRainRate"
           # beaufort_category = 0
           # manifest_name = "My Weather Website"
           # manifest_short_name = "MWW"
           # aeris_map = 0
           # radar_html = ''   #  (default seems to center on your lat/lon)
           # radar_html_dark = None
           # radar_zoom = 8
           # radar_marker = 0
           # almanac_extras = 1
           # highcharts_enabled = 1
           # graph_page_show_all_button = 1
           # graph_page_default_graphgroup = "day"
           # highcharts_homepage_graphgroup = "day"
           # highcharts_decimal = "auto"
           # highcharts_thousands = "auto"
           # googleAnalyticsId = ""
           # pi_kiosk_bold = "false"
           # pi_theme = "auto"
           # webpage_autorefresh = 0
           # reload_hook_images = 0
           # reload_images_radar = 300
           # reload_images_hook_asi = -1
           # reload_images_hook_af = -1
           # reload_images_hook_as = -1
           # reload_images_hook_ac = -1
           # show_last_updated_alert = 0
           # last_updated_alert_threshold = 1800

           #--- MQTT Websockets (for Real Time Streaming) Options ---
           # mqtt_websockets_enabled = 0
           # mqtt_websockets_host = ""
           # mqtt_websockets_port = 8080
           # mqtt_websockets_ssl	= 0
           # mqtt_websockets_topic = ""
           # disconnect_live_website_visitor = 1800000

           #--- Forecast Options ---
           # forecast_enabled = 0
           # forecast_provider = "aeris"
           # forecast_api_id = ""
           # forecast_api_secret = ""
           # forecast_units = "us"
           # forecast_lang = "en"
           # forecast_stale = 3540
           # forecast_aeris_use_metar = 1
           # forecast_interval_hours = 24
           # forecast_alert_enabled = 0
           # forecast_alert_limit = 1
           # forecast_show_daily_forecast_link = 0
           # forecast_daily_forecast_link = ""
           # aqi_enabled = 0
           # aqi_location_enabled = 0

           #--- Earthquake Options ---
           # earthquake_enabled = 0
           # earthquake_maxradiuskm = 1000
           # earthquake_stale = 10740
           # earthquake_server = USGS
           # geonet_mmi = 4

           #--- Social Options ---
           # facebook_enabled = 0
           # twitter_enabled = 0
           # twitter_hashtags = "weewx #weather"
           # social_share_html = ""
           
           #--- Kiosk Options ---
           # radar_html_kiosk = ""
           # radar_width_kiosk = 490
           # radar_height_kiosk = 362
           # mqtt_websockets_host_kiosk = ""
           # mqtt_websockets_port_kiosk = ""
           # mqtt_websockets_ssl_kiosk = ""
           # forecast_interval_hours_kiosk = 24
           # aqi_enabled_kiosk = 0

           #-------------------------------------------------------------
           #---
           #--- python's ConfigObj has a limitation in how it processes
           #--- comments, so we need to define an 'unused' variable below
           #--- to ensure that this whole stanza makes it into weewx.conf
           #--- 
           #--- please ignore the following 'unused' variable
           #---
           #-------------------------------------------------------------
           work_around_ConfigObj_limitations = true

           # [[[[Generic]]]]
                #-- Footer information --
                # footer_copyright_text = "My Weather Website"
                # footer_disclaimer_text = "Never make important decisions based on info from this website."

                #-- Default page headers --
                # home_page_header = "My Station Weather Conditions"
                # graphs_page_header = "Weather Observation Graphs"
                # reports_page_header = "Weather Observation Reports"
                # records_page_header = "Weather Observation Records"
                # about_page_header = "About This Site"
                # powered_by = 'Observations are powered by a <a href="/about" target="_blank">Personal Weather Station</a>'

                #-- Twitter Social Share --
                # twitter_text = "Check out my website: My Weather Website Weather Conditions"
                # twitter_owner = "YourTwitterUsernameHere"
                # twitter_hashtags = "weewx #weather"

"""
config_dict = configobj.ConfigObj(StringIO(extension_config))

#----------------------------------
#        files stanza
#----------------------------------

files=[('bin/user', ['bin/user/belchertown.py'
                    ]
        ),
       ('skins/Belchertown', ['skins/Belchertown/favicon.ico',
                              'skins/Belchertown/footer.html.tmpl',
                              'skins/Belchertown/header.html.tmpl',
                              'skins/Belchertown/index.html.tmpl',
                              'skins/Belchertown/about.inc.example',
                              'skins/Belchertown/kiosk.html.tmpl',
                              'skins/Belchertown/kiosk.css',
                              'skins/Belchertown/celestial.inc',
                              'skins/Belchertown/graphs.conf.example',
                              'skins/Belchertown/page-header.inc',
                              'skins/Belchertown/manifest.json.tmpl',
                              'skins/Belchertown/records.inc.example',
                              'skins/Belchertown/records-table.inc.example',
                              'skins/Belchertown/robots.txt',
                              'skins/Belchertown/skin.conf',
                              'skins/Belchertown/belchertown-dark.min.css',
                              'skins/Belchertown/style.css'
                             ]
        ),
       ('skins/Belchertown/about', ['skins/Belchertown/about/index.html.tmpl']),
       ('skins/Belchertown/graphs', ['skins/Belchertown/graphs/index.html.tmpl']),
       ('skins/Belchertown/NOAA', ['skins/Belchertown/NOAA/NOAA-YYYY-MM.txt.tmpl',
                                   'skins/Belchertown/NOAA/NOAA-YYYY.txt.tmpl'
                                  ]
        ),
       ('skins/Belchertown/pi', ['skins/Belchertown/pi/index.html.tmpl']),
       ('skins/Belchertown/records', ['skins/Belchertown/records/index.html.tmpl']),
       ('skins/Belchertown/reports', ['skins/Belchertown/reports/index.html.tmpl']),
       ('skins/Belchertown/js', ['skins/Belchertown/js/belchertown.js.tmpl',
                                 'skins/Belchertown/js/index.html',
                                 'skins/Belchertown/js/responsive-menu.js'
                                ]
        ),
       ('skins/Belchertown/json', ['skins/Belchertown/json/index.html',
                                   'skins/Belchertown/json/weewx_data.json.tmpl'
                                  ]
        ),
       ('skins/Belchertown/images', ['skins/Belchertown/images/clear-day.png',
                                     'skins/Belchertown/images/clear-night.png',
                                     'skins/Belchertown/images/cloudy.png',
                                     'skins/Belchertown/images/drizzle.png',
                                     'skins/Belchertown/images/fog.png',
                                     'skins/Belchertown/images/hail.png',
                                     'skins/Belchertown/images/mostly-clear-day.png',
                                     'skins/Belchertown/images/mostly-clear-night.png',
                                     'skins/Belchertown/images/mostly-cloudy-day.png',
                                     'skins/Belchertown/images/mostly-cloudy-night.png',
                                     'skins/Belchertown/images/partly-cloudy-day.png',
                                     'skins/Belchertown/images/partly-cloudy-night.png',
                                     'skins/Belchertown/images/rain.png',
                                     'skins/Belchertown/images/sleet.png',
                                     'skins/Belchertown/images/snow.png',
                                     'skins/Belchertown/images/snowflake-icon-15px.png',
                                     'skins/Belchertown/images/station.png',
                                     'skins/Belchertown/images/station48.png',
                                     'skins/Belchertown/images/station72.png',
                                     'skins/Belchertown/images/station96.png',
                                     'skins/Belchertown/images/station144.png',
                                     'skins/Belchertown/images/station168.png',
                                     'skins/Belchertown/images/station192.png',
                                     'skins/Belchertown/images/sunrise.png',
                                     'skins/Belchertown/images/sunset.png',
                                     'skins/Belchertown/images/thunderstorm.png',
                                     'skins/Belchertown/images/tornado.png',
                                     'skins/Belchertown/images/unknown.png',
                                     'skins/Belchertown/images/wind.png',
                                     'skins/Belchertown/images/windy.png',
                                     'skins/Belchertown/images/index.html',
                                     'skins/Belchertown/images/aeris-icon-list.json'                                    
                                    ]
        )
]
files_dict = files

#---------------------------------
#          done
#---------------------------------
