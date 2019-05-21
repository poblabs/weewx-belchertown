# Installer for Belchertown weewx skin
# Pat O'Brien, 2018

from setup import ExtensionInstaller

def loader():
    return ExfoliationInstaller()

class ExfoliationInstaller(ExtensionInstaller):
    def __init__(self):
        super(ExfoliationInstaller, self).__init__(
            version="1.0rc9.2",
            name='Belchertown',
            description='A clean modern skin with real time streaming updates and interactive charts. Modeled after BelchertownWeather.com',
            author="Pat OBrien",
            author_email="pat@obrienlabs.net",
            config={
                'StdReport': {
                    'Belchertown': {
                        'skin':'Belchertown',
                        'HTML_ROOT':'belchertown'
                    }
                }
            },
            files=[('bin/user', ['bin/user/belchertown.py'
                                ]
                    ),
                   ('skins/Belchertown', ['skins/Belchertown/favicon.ico',
                                          'skins/Belchertown/footer.html.tmpl',
                                          'skins/Belchertown/header.html.tmpl',
                                          'skins/Belchertown/index.html.tmpl',
                                          'skins/Belchertown/about.inc.example',
                                          'skins/Belchertown/celestial.inc',
                                          'skins/Belchertown/graphs.conf.example',
                                          'skins/Belchertown/page-header.inc',
                                          'skins/Belchertown/manifest.json.tmpl',
                                          'skins/Belchertown/records.inc.example',
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
                   ('skins/Belchertown/pi', ['skins/Belchertown/pi/index.html.tmpl',
                                               'skins/Belchertown/pi/pi-header.html.tmpl'
                                              ]
                    ),                    
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
                                                 'skins/Belchertown/images/fog.png',
                                                 'skins/Belchertown/images/hail.png',
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
                                                 'skins/Belchertown/images/wind.png',
                                                 'skins/Belchertown/images/index.html'
                                                ]
                    )
                   ]
        )
