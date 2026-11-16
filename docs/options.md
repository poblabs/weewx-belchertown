# All skin options

These go in `weewx.conf` under `[[Belchertown]]` → `[[[Extras]]]` ([example](customize.md)). Click a group to open it.

??? note "General options"

    | Name | Default | Description
    | ---- | ------- | ----------
    | belchertown_debug | 0 | 1 turns on debug messages in the browser console. See [Debug mode](troubleshooting.md#debug-mode).
    | belchertown_locale | "auto" | The language and number format, like `"en_US.UTF-8"` or `"de_DE.UTF-8"`. `"auto"` uses `lang` if the report has one, otherwise your server's setting. The browser formats dates and live values in any locale; numbers built on the server need the locale installed there.
    | theme | light | `light`, `dark` or `auto` (light at sunrise, dark at sunset).
    | theme_toggle_enabled | 1 | Shows a moon/sun button so visitors can flip between light and dark.
    | jquery | auto | Loads jQuery only when one of your own `.inc` files uses it. 1 always loads it, 0 never does. See [Your own scripts, jQuery and Bootstrap](customize.md#your-own-scripts-jquery-and-bootstrap).
    | bootstrap | auto | Loads Bootstrap's stylesheet only when one of your own `.inc` files uses Bootstrap classes the skin doesn't style. 1 always loads it, 0 never does.
    | chart_builder_enabled | 1 | Writes the data for the [chart builder](charts/chart-builder.md) page once an hour. 0 turns it off.
    | back_to_top_button_enabled | 0 | 1 shows a "back to top" button once the page is scrolled.
    | back_to_top_button_position | 0 | 0 puts the button on the right, 1 on the left.
    | back_to_top_button_opacity | 0.8 | How solid the button is, from 0.1 (faint) to 1.0.
    | sticky_header | 1 | Keeps the header (logo, menu and buttons) at the top of the screen while scrolling; it slims down once you scroll. 0 lets it scroll away with the page.
    | unit_toggle_enabled | 1 | Shows a units button (°F or °C) so visitors can see the site in the other unit system. See [Units button](customize.md#units-button-f-or-c).
    | logo_image | "" | The **full** web address of your logo. About 330 × 80 pixels fits best.
    | logo_image_dark | "" | The **full** web address of a logo for dark mode.
    | site_title | "My Weather Website" | Shown instead of a logo when `logo_image` is empty.
    | station_observations | "barometer", "dewpoint", "outHumidity", "rainWithRainRate" | Which observations are listed next to the radar, in order. Use weewx database names, plus `aqi`, `visibility` and `cloud_cover` (from the forecast provider) and `rainWithRainRate` (rain total and rate on one line). To read from another database, add the binding, for example `leafTemp2(data_binding=sdr_binding)`; if that observation isn't in the live MQTT data it only updates when the page reloads.
    | beaufort_category | 0 | Shows the Beaufort category ("calm", "gale", ...) under wind speed. For live updates, add `beaufort = prefer_hardware` under `[StdWXCalculate]` → `[[Calculations]]` in `weewx.conf`.
    | manifest_name | "My Weather Website" | Your site's name when someone adds it to their phone's home screen.
    | manifest_short_name | "MWW" | The name under its home screen icon.
    | radar_html | "" (a windy.com map) | The radar for light mode (and dark mode, if `radar_html_dark` isn't set). Any HTML, about 650 × 360 pixels. To make your own from windy.com, open Weather Radar there and choose "embed widget on page".
    | radar_html_dark | "" | The radar for dark mode. Any HTML.
    | radar_width | 650 | Width of the windy.com radar, in pixels. Your own `radar_html` sets its own size.
    | radar_height | 360 | Height of the windy.com radar, in pixels.
    | radar_zoom | 8 | How far the radar starts zoomed in, from 1 (far) to 11 (close).
    | radar_marker | 0 | 1 puts a marker at your station on the windy.com radar.
    | radar_overlay | radar | What the windy.com map shows: `radar`, `wind`, `gust`, `rain`, `temp`, `clouds`, `satellite`, `pressure`, `rh`, `snowcover`, `thunder` and the other layer names windy.com offers.
    | almanac_extras | 1 | Shows extra sun and moon details. Requires the `ephem` Python package on your server.
    | highcharts_enabled | 1 | 0 hides the charts.
    | chart_library | highcharts | `echarts` draws the charts with Apache ECharts, which is free for any site. See [Highcharts or ECharts](charts/index.md#highcharts-or-echarts).
    | home_sections | conditions, forecast, onthisday, snapshot, charts | The blocks on the home page, in order. Leave one out to hide it, or add your own. See [Choose what's on the home page](customize.md#choose-whats-on-the-home-page-and-in-what-order).
    | home_view | dashboard | The home page layout visitors see first: `dashboard`, `forecast`, `radar` or `charts`. See [Home page layouts](customize.md#home-page-layouts).
    | storm_view | 1 | Storm mode: shows the radar first while it's raining or a storm alert is in effect. 0 turns it off. See [Home page layouts](customize.md#home-page-layouts).
    | graph_page_show_all_button | 1 | Adds an "All" button on the Graphs page that shows every chart, two per row.
    | graph_page_default_graphgroup | "day" | Which chart group the Graphs page opens with. `"all"` shows them all.
    | highcharts_homepage_graphgroup | "homepage" | Which chart group the home page shows. See the [chart wiki](charts/graphs-conf.md).
    | highcharts_decimal | "auto" | The decimal point in charts. `"auto"` uses your locale's.
    | highcharts_thousands | "auto" | The thousands separator in charts. `"auto"` uses your locale's.
    | googleAnalyticsId | "" | Your Google Analytics ID, if you use it.
    | webpage_autorefresh | 0 | Without live updates, reload the page this often, in milliseconds (300000 = 5 minutes). 0 turns it off.
    | reload_hook_images | 0 | 1 reloads images in your [home page content](customize.md#add-your-own-content-to-the-home-page) on the timers below.
    | reload_images_radar | 300 | Seconds between radar reloads. -1 turns it off.
    | reload_images_hook_asi | -1 | Seconds between reloads of images in `index_hook_after_station_info.inc`. -1 turns it off.
    | reload_images_hook_af | -1 | Seconds between reloads of images in `index_hook_after_forecast.inc`. -1 turns it off.
    | reload_images_hook_as | -1 | Seconds between reloads of images in `index_hook_after_snapshot.inc`. -1 turns it off.
    | reload_images_hook_ac | -1 | Seconds between reloads of images in `index_hook_after_charts.inc`. -1 turns it off.
    | show_last_updated_alert | 0 | Without live updates, shows a warning banner when the data is older than the next setting.
    | last_updated_alert_threshold | 1800 | Seconds before the data counts as old for that banner.

??? note "Live update (MQTT) options"

    | Name | Default | Description
    | ---- | ------- | -----------
    | mqtt_websockets_enabled | 0 | 1 turns on [live updates](live-updates.md).
    | mqtt_websockets_host | "" | Your broker's hostname or IP address.
    | mqtt_websockets_port | 1883 | Your broker's **websockets** port. (1883 is the usual plain MQTT port; websockets is often 9001 or 8080. Check your broker.)
    | mqtt_websockets_username | "" | Username for the broker, if it needs one.
    | mqtt_websockets_password | "" | Password for the broker, if it needs one. Visitors' browsers receive it, so use a read-only account.
    | mqtt_websockets_ssl | 0 | 1 if your broker uses SSL.
    | mqtt_websockets_topic | "" | The topic to listen to, usually ending in `/loop` (for example `weather/loop`), to match your weewx-mqtt settings.
    | disconnect_live_website_visitor | 1800000 | Stop a visitor's live updates after this many milliseconds, so idle tabs don't stay connected forever. 1800000 = 30 minutes. 0 never disconnects.

??? note "Forecast options"

    | Name | Default | Description
    | ---- | ------- | -----------
    | forecast_enabled | 1 | 1 shows the [forecast](forecasts.md). 0 turns it off.
    | forecast_provider | "auto" | Where the forecast comes from: `openmeteo` (free, no key, worldwide), `nws` (National Weather Service, US only, no key), `aeris` (Xweather, needs a key), or `auto` (Xweather when `forecast_api_id` is set, otherwise Open-Meteo).
    | forecast_api_id | "" | Your Xweather client ID.
    | forecast_api_secret | "" | Your Xweather client secret.
    | forecast_units | "us" | `us`, `si`, `ca` or `uk2`. See [Forecast units](forecasts.md#forecast-units).
    | forecast_stale | 3540 | Seconds before a new forecast is downloaded (3540 = 59 minutes). Each download costs about 10 Xweather calls (air quality counts 5), so going much below an hour can use up the free tier.
    | forecast_aeris_use_metar | 1 | Xweather only: 1 takes current conditions from airports and official stations; 0 from nearby personal weather stations.
    | forecast_interval_hours | 24 | Which forecast shows when someone opens the site: 1, 3 or 24 hours apart, or 0 to hide the forecast.
    | forecast_alert_enabled | 1 | 1 shows weather alerts (watches and warnings). They refresh with the forecast. 0 turns them off.
    | forecast_alert_provider | "auto" | Where alerts come from: `nws` (National Weather Service, US only, no key), `aeris` (Xweather), `none`, or `auto` (Xweather's alerts when the forecast is from Xweather, otherwise the National Weather Service).
    | forecast_alert_limit | 1 | How many alerts to show.
    | forecast_lang | "en" | The language of Xweather alert text (an Xweather language code). The forecast itself uses the skin's labels.
    | forecast_show_daily_forecast_link | 0 | 1 adds a link under each forecast day to the website in the next option.
    | forecast_daily_forecast_link | "" | The address for those links. `YYYY`, `MM` and `DD` are replaced with the day's date, for example `https://live.xweather.com/local/us/ma/belchertown/forecast/YYYY/MM/DD`.
    | forecast_show_humidity_dewpoint | 0 | Show humidity (1) or dew point (2) in the forecast. 0 shows neither.
    | aqi_enabled | 0 | 1 shows the Air Quality Index: from the nearest station within 50 miles with Xweather, otherwise modeled for your location by Open-Meteo.
    | aqi_location_enabled | 0 | Xweather only: 1 shows where that AQI reading comes from, which may be far away.

??? note "Earthquake options"

    | Name | Default | Description
    | ---- | ------- | -----------
    | earthquake_enabled | 0 | 1 shows your nearest recent earthquake on the home page.
    | earthquake_maxradiuskm | 1000 | How far from your station to look, in kilometers.
    | earthquake_stale | 10740 | Seconds before downloading new earthquake data (10740 = just under 3 hours). Please keep it around 3 hours to be kind to the servers.
    | earthquake_server | USGS | `USGS` (best for North America), `GeoNet` (New Zealand) or `ReNaSS` (Europe).
    | geonet_mmi | 4 | GeoNet only: the smallest intensity to show (MMI, -1 to 8). 4 shows light quakes and stronger.

??? note "Social sharing options"

    | Name | Default | Description
    | ---- | ------- | -----------
    | facebook_enabled | 0 | 1 shows a Facebook share button at the top of each page.
    | social_share_html | "http://yourwebsite" | The address people share, usually your home page. Set it, or the buttons share a dead link.
