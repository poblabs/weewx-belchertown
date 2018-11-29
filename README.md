# Belchertown weewx skin

This skin (or theme, or template) is for the [weewx weather software](http://weewx.com) and is modeled after my website [BelchertownWeather.com](https://belchertownweather.com). I developed that website with custom features but used weewx as the backend archive. It was a good fit to port the site to a weewx skin.

Features include:
* Real-time streaming updates on the front page of the webpage without neededing to reload the website. (weewx-mqtt extension required)
* Forecast data updated every hour without needing to reload the website. (a free DarkSky API key required)
* Information on your closest Earthquake updated automatically every 3 hours
* Observation graphs without needing to reload the website.
* Weather records for the current year, and for all time. 
* Responsive design. Mobile and iPad landscape ready! Use your mobile phone or iPad in landscape mode as an additional live console display.

## Requirements 

### weewx.conf
These settings need to be enabled in order for the skin to work. Within `weewx.conf`, under `[Station]` make sure you have: 
* `latitude` - used for forecasting and earthquake data
* `longitude` - used for forecasting and earthquake data
* `station_url` - The full URL to your website without a trailing slash. Even if your website is on your LAN only, this needs to be enabled. Example: `http://yourwebsite.com` or `http://192.168.1.100`

### DarkSky API (optional)
DarkSky API is where the forecast data comes from. The skin will work without DarkSky's integration, however it is used to show current weather observations and icons. 

**You must sign up to use their service.** This skin does not provide any forecast data. You need to join their website and get a free developer key. Their free tier allows for 1,000 requests a day. The skin will download and cache every hour - 24 requests a day - well below the free 1,000.

* Sign up at https://darksky.net/dev
* Once you are logged in, take note of the Secret Key on the DarkSky console. 
* Use this key as the `darksky_secret_key` option. See below options table after you have installed the skin.
* Make sure you place the "Powered by DarkSky" somewhere on your website. Like the About page (see below after install for customizing the About page). 

### MQTT (optional)
MQTT is a publish / subscribe system. Mostly used for IoT devices, but it works great for a live website. 

You will to use an [MQTT broker](https://github.com/poblabs/weewx-belchertown#mqtt-brokers) (aka server) to publish your data to. You can [install your own broker pretty easily](https://obrienlabs.net/how-to-setup-your-own-mqtt-broker/), or use a public one (some free, some paid). Your weewx server will **publish** it's weather data to a broker and visitors to your website will **subscribe** to those updates using MQTT Websockets. When data is published the subscribers get that data immediatly. 

With the [`weewx-mqtt` extension](https://github.com/weewx/weewx/wiki/mqtt) installed, everytime weewx generates a LOOP it'll automatically publish that data to MQTT which will update your website in real time. Once ARCHIVE is published, your website will reload the forecast data, earthquake data and graphs automatically.

A sample MQTT extension config is below. Update the `server_url`, `topic`, and `unit_system` to suite your needs. Keep `binding` as archive and loop. Remove the tls section if your broker is not using SSL/TLS.

```
    [[MQTT]]
        server_url = mqtt://username:password@mqtt.hostname:port/
        topic = the/topic/to/publish/to
        unit_system = US
        binding = archive, loop
        aggregation = aggregate
        [[[tls]]]
            tls_version = tlsv1
            ca_certs = /etc/ssl/certs/ca-certificates.crt
```

**I did not write the MQTT extension, so please direct any questions or problems about it to the [user forums](https://groups.google.com/forum/#!forum/weewx-user).**

### MQTT Websockets (optional, but required if you want real-time updates)

Your MQTT broker (server) will need to support MQTT websockets in order for the website skin to connect to the MQTT topics. Please make sure your broker has websockets support. 

### MQTT Brokers

#### Install your own MQTT Broker
If you want to run your own MQTT broker, you can [follow these instructions that I've put together](https://obrienlabs.net/how-to-setup-your-own-mqtt-broker/). 

#### Use a Public Broker
These public brokers have been tested as working. If you have others to add the to the list, let me know.

* [test.mosquitto.org](http://test.mosquitto.org)

## Install weewx-belchertown

1) Download the tar gz file.

2) Run the installer. Replace `x.x` with the version number of the skin you've downloaded.

```
sudo wee_extension --install weewx-belchertown-x.x.tar.gz
```

3) Restart weewx:

```
sudo /etc/init.d/weewx stop
sudo /etc/init.d/weewx start
```

4) Wait for an archive period, or run `sudo wee_reports` to force an update

5) Browse to your website to see the skin. It may be in the belchertown subdirectory.

## Belchertown Skin as Default Skin

To make Belchertown the default skin for your site, make the configuration changes as below. This is an example config and may need a little fine-tuning site-per-site.

1. In `weewx.conf` look for the `[StdReport]` section. Within that section is `[[StandardReport]]` and under that change `skin = Standard` to `skin = Belchertown`. 

2. Take note of the `HTML_ROOT` setting in the `[StdReport]` section since you will need it for the next section. 

3. Then modify the Belchertown skin options with these minimal updates:

```
    [[Belchertown]]
        HTML_ROOT = <<the HTML_ROOT location as above. E.g. public_html>>
        skin = Belchertown
        [[[Extras]]]
           belchertown_root_url = "http://your_full_website_url"
           
   [[Highcharts_Belchertown]]
        HTML_ROOT = <<the HTML_ROOT location as above. E.g. public_html>>
        skin = Highcharts_Belchertown
```

4. This is optional, but advised: Delete all contents of the `HTML_ROOT` folder and let Belchertown create an entire new site. This prevents stale duplicate data.

5. Restart weewx and let it generate the files upon the next archive interval.

## Creating About Page and Records Page

The About Page and Records Page offer some areas for custom HTML to be run. To create or edit these pages, go to the `skins/Belchertown` folder. These files should not be overwritten during skin upgrdades, but it's always best to have a backup just in case!

* Create (or edit) the `skins/Belchertown/about.inc` and `skins/Belchertown/records.inc` files with your text editor, such as Notepad or Nano.
    * These files take full HTML, so you can get fancy if you want. 
    * You can view, and use the sample file [`about.inc.example`](https://github.com/poblabs/weewx-belchertown/blob/master/skins/Belchertown/about.inc.example) and [`records.inc.example`](https://github.com/poblabs/weewx-belchertown/blob/master/skins/Belchertown/records.inc.example). Just rename to remove the `.example`, edit and you should be good to go. 
* Then restart weewx for the changes to take effect, and wait for an archive interval for the pages to be generated.

## Using Metric

If your weewx and your weather station are configured for metric, you can display the metric values in the skin. Just like with the [Standard weewx skin](http://weewx.com/docs/customizing.htm#[Units]), to change the site to metric you would need to add `[[[Units]]]` and `[[[[Groups]]]]` to the Belchertown skin options in `weewx.conf`, with the appropriate group values. Restart weewx when you have made the changes. For example:

```
[StdReport]
    [[Belchertown]]
        skin = Belchertown
        HTML_ROOT = belchertown
        [[[Units]]]
            [[[[Groups]]]]
                group_altitude = meter
                group_degree_day = degree_C_day
                group_pressure = mbar
                group_rain = mm
                group_rainrate = mm_per_hour
                group_speed = meter_per_second
                group_speed2 = meter_per_second2
                group_temperature = degree_C
    [[Highcharts_Belchertown]]
        skin = Highcharts_Belchertown
        HTML_ROOT = belchertown
        [[[Units]]]
            [[[[Groups]]]]
                group_altitude = meter
                group_degree_day = degree_C_day
                group_pressure = mbar
                group_rain = mm
                group_rainrate = mm_per_hour
                group_speed = meter_per_second
                group_speed2 = meter_per_second2
                group_temperature = degree_C                
```

## Belchertown Skin Options

The Belchertown skin will work as a very basic skin once installed using the default values in the table below.

To override a default setting add the setting name and value to the Extras section for the skin by opening `weewx.conf` and look for `[StdReport]`. Under will be `[[Belchertown]]`. Add `[[[Extras]]]` (with 3 brackets) and then add your values. For example:

```
[StdReport]
    [[Belchertown]]
        skin = Belchertown
        HTML_ROOT = belchertown
        [[[Extras]]]
            logo_image = "https://belchertownweather.com/images/content/btownwx-logo-slim.png"
            footer_copyright_text = "BelchertownWeather.com"
            forecast_enabled = 1
            darksky_secret_key = "your_key"
            earthquake_enabled = 1
            twitter_enabled = 1
            twitter_owner = PatOBrienPhoto
```

The benefit to adding these values to `weewx.conf` is that they persist after skin upgrades, whereas `skin.conf` could get replaced on skin upgrades. Always have a backup of `weewx.conf` and `skin.conf` just in case! 

Restart weewx once you add your custom options and wait for an archive period to see the results.

For ease of readability I have broken them out into separate tables. However you just add the overrides to the config just like the example above. 

## General Options

| Name | Default | Description
| ---- | ------- | ----------
| logo_image | "" | The URL to your logo image. 330 pixels wide by 80 pixels high works best. Anything outside of this would need custom CSS
| site_title | "My Weather Website" | If `logo_image` is not defined, then the `site_title` will be used. Define and change this to what you want your site title to be.
| footer_copyright_text | "My Weather Website" | This is the text to show after the year in the copyright. 
| graphs_page_header | "Weather Observation Graphs" | The header text to show on the Graphs page
| reports_page_header | "Weather Observation Reports" | The header text to show on the Reports page
| records_page_header | "Weather Observation Records" | The header text to show on the Records page
| about_page_header | "About This Site" | The header text to show on the About page
| radar_html | A windy.com iFrame | Full HTML Allowed. Recommended size 650 pixels wide by 360 pixels high. This URL will be used as the radar iFrame or image hyperlink. If you are using windy.com for live radar, they have instructions on how to embed their maps. Go to windy.com, click on Weather Radar on the right, then click on embed widget on page. Make sure you use the sizes recommended earier in this description.
| highcharts_enabled | 1 | Show the charts on the website. 1 = enable, 0 = disable.
| show_apptemp | 0 | If you have [enabled Apparent Temperature](http://weewx.com/docs/customizing.htm#add_archive_type) (appTemp) in your database, you can show it on the site by enabling this. 
| show_windrun | 0 | If you have [enabled Wind Run](http://weewx.com/docs/customizing.htm#add_archive_type) (windRun) in your database, you can show it on the site by enabling this.
| googleAnalyticsId | "" | Enter your Google Analytics ID if you are using one

## MQTT (for Real Time Streaming) Options

| Name | Default | Description
| ---- | ------- | -----------
| mqtt_enabled | 0 | Set to 1 to enable the real-time streaming website updates from your MQTT broker (server)
| mqtt_host | "" | The MQTT broker hostname or IP
| mqtt_port | 1883 | The MQTT broker's port. Example: 1883 is standard. Brokers using SSL may be on port 9001. Check your broker's documentation.
| mqtt_ssl | 0 | Set to 1 if your broker is using SSL
| mqtt_topic | "" | The topic to subscribe to for your weather data
| disconnect_live_visitor | 1800000 | The number of seconds after a visitor has loaded your page that we disconnect them from the live streaming updates. The idea here is to save your broker from a streaming connection that never ends. Time is in milliseconds. 0 = disabled. 300000 = 5 minutes. 1800000 = 30 minutes

## Forecast Options

| Name | Default | Description
| ---- | ------- | -----------
| forecast_enabled | 0 | 1 = enable, 0 = disable. Enables the forecast data from DarkSky API.
| darksky_secret_key | "" | Your DarkSky secret key
| darksky_units | "auto" | The units to use for the DarkSky forecast. Default of `auto` which automatically selects units based on your geographic location. [Other options](https://darksky.net/dev/docs) are: `us` (imperial), `si` (metric), `ca` (metric except that windSpeed and windGust are in kilometers per hour), `uk2` (metric except that nearestStormDistance and visibility are in miles, and windSpeed and windGust in miles per hour).
| forecast_stale | 3540 | The number of seconds before the skin will download a new forecast update. Default is 59 minutes so that on the next archive interval at 60 minutes it will download a new file (based on 5 minute archive intervals (see weewx.conf, archive_interval)). ***WARNING*** 1 hour is recommended. Setting this too low will result in being billed from DarkSky. Use at your own risk of being billed if you set this too low. 3540 seconds = 59 minutes. 3600 seconds = 1 hour. 1800 seconds = 30 minutes. 

## Earthquake Options

| Name | Default | Description
| ---- | ------- | -----------
| earthquake_enabled | 0 | 1 = enable, 0 = disable. Show the earthquake data on the front page
| earthquake_maxradiuskm | 1000 | The radius in kilometers from your weewx.conf's latitude and longitude to search for the most recent earthquake.
| earthquake_stale | 10740 | The number of seconds after which the skin will download new earthquake data from USGS. Recommended setting is every 3 hours to be kind to the USGS servers. 10800 seconds = 3 hours. 10740 = 2 hours 59 minutes

## Social Options

These are the options for the social media sharing section at the top right of each page. This does not link your site to anything, instead it gives your visitors a way to spread the word about your page on social media. 

| Name | Default | Description
| ---- | ------- | -----------
| facebook_enabled | 0 | Enable the Facebook Share button
| twitter_enabled | 0 | Enable the Twitter Share button
| twitter_owner | "" | Your Twitter handle which will be mentioned when the share button is pressed
| twitter_hashtags | "weewx #weather" | The hashtags to include in the share button's text. 

## Frequently Asked Questions

* Q: How do I make this skin my default website?
* A: [Click here to take a look at this section of the readme file which explains how to set this up](https://github.com/poblabs/weewx-belchertown#belchertown-skin-as-default-skin). 
---
* Q: My NOAA reports are blank.
* A: If this is right after you installed the skin, give weewx an archive interval or populate this data
---
* Q: I see errors like these:
    * `No such file or directory '/home/weewx/skins/Belchertown/about.inc'` 
    * `No such file or directory '/home/weewx/skins/Belchertown/records.inc'`
* A: You probably skipped the step [Creating About Page and Records Page](https://github.com/poblabs/weewx-belchertown#creating-about-page-and-records-page). Please give that a try. 
---
* Q: Do I have to use MQTT?
* A: Nope! If you disable the MQTT option, then weewx will still create a website for you, it just will be done on the archive interval. weewx will still generate these pages for you if you have MQTT enabled, the benefit is that you do not have to reload the website. 
---
* Q: What MQTT broker should I use?
* A: There are a number of free ones out there and they all have different limitations. A popular one is io.adafruit.com, but check that their free tier will suite your needs. If you can't find a good free one, you can always install and configure Mosquitto (the name of an MQTT broker) on your server. Just make sure you set the permissions so that **only you can publish**. You do not want the general public to have the ability to publish data onto your weewx stream. 
* Currently I am not providing support on how to do this, but I do plan to do a write up soon and will link to it when it's ready. In the meantime there's plenty of resources available online to set up your own MQTT broker if desired. 
---
* Q: Do I have to use forecasts?
* A: You do not need to use forecasts, but it is recommended to use forecasts so you take advantage of the theme's design with icons and observations.
---
* Q: Do I have to use earthquake data?
* A: Nope! If you leave it disabled, it won't show on the site nor will any data be downloaded. 
---
* Q: Do I have to use the radar?
* A: Nope! If you leave it disabled you'll just have a big blank box on the website. But [windy.com](https://windy.com) provides a free animated radar, so why not include it? :)
---
* Q: Do I have to use the graphs?
* A: Nope! If you have it disabled we will hide those portions of the site. It comes packaged with this theme already though, so you can leave it enabled. 
---
* Q: Why does the skin take a while to generate sometimes?
* A: This is because of the graph system. That file goes through your archive's day, week, month and year values, and all time values to generate the graphs. Depending on how big your database is this could take a little longer. 
---
* Q: I noticed my graphs don't update right away on an archive period. How come?
* A: Because the highcharts can take a few extra seconds, I've put in a 30 second delay on the graphs automatic update. This way it's loading the newest data.
---
* Q: Do the graphs on the Graphs page update automatically?
* A: No, only the front page is automatically updated. All the other pages are normal pages that need to be refreshed to see new information.
---
* Q: How do I change my about page, or records page?
* A: See above on how to do that. 
---
* Q: How can I tell if the skin downloaded new forecast or earthquake data?
* A: Check your system log file. You should see the skin output something along the lines of "New forecast file downloaded" or "New earthquake file downloaded".
---
* Q: How come I'm seeing `NAN` in some areas?
* A: This is because weewx hasn't gathered enough data from your station yet. Give it a few more archive intervals. 
---
* Q: How do I uninstall this skin?
* A: `sudo wee_extension --uninstall Belchertown`

## Donate
[![Donate](https://img.shields.io/badge/Donate-Support%20by%20Donating%20or%20Buying%20me%20a%20Coffee-blue.svg)](https://obrienlabs.net/donate)

This project took a lot of coffee to create. If you enjoy this skin and find some value from it, [click here to buy me another cup of coffee](https://obrienlabs.net/donate) :)

## Credits
* DarkSky API for the weather forecasts.
* Windy.com for the iFrame embedded weather radar.
* Gary for the [weewx-highcharts](https://github.com/gjr80/weewx-highcharts) extension. A custom forked version has been packaged with this Belchertown theme. 
* Brian at [weather34.com](http://weather34.com) for the weather icons from the simplicty 2015 theme. Used with agreement.
