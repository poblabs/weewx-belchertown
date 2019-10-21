This is the Belchertown skin for the weewx weather system.
Copyright 2018 Pat O'Brien

Please view the README.md on GitHub for full configuration instructions. https://github.com/poblabs/weewx-belchertown

Installation instructions:

1) Run the installer:

sudo wee_extension --install weewx-belchertown.tgz

2) Restart weewx:

sudo /etc/init.d/weewx stop
sudo /etc/init.d/weewx start

3) Wait for an archive period, or run wee_reports

4) Look at the result in the 'belchertown' subdirectory.

public_html/belchertown


Configuration options:

While optional, you should first setup the DarkSky API so you can enable the forecasts option. 
Weather icons, the 8 day forecast and visibility all come from DarkSky's API. 

There are a number of options all set as a default within the skin.conf file. 
It is recommended that any option you want to override to add it to the weewx.conf
file. This way your changes do not get erased on skin or weewx upgrades. 

For example, to add a logo to your site, you would want to open your weewx.conf and
find the Belchertown skin section. Add an [[[Extras]]] stanza and then the logo_image variable
and the location of the logo. 

Example:

[StdReport]
    [[Belchertown]]
        [[[Extras]]]
            logo_image = "https://belchertownweather.com/images/content/btownwx-logo-slim.png"
    
For a list of Extra variables that can be changed, you can look in the skin.conf, or look on the 
GitHub repository for the variables and their descriptions.

Credits:

Highcharts graph extension from Gary Roderick at https://github.com/gjr80/weewx-highcharts
Weather icon set from Brian at http://weather34.com
Forecast data from http://darksky.net
