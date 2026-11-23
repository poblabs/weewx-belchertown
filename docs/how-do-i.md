# How do I...?

Short answers to the things people most often want to change, with a link to the details. Most of them are one line in `weewx.conf`.

!!! note "Where settings go"
    Unless it says otherwise, a setting goes in `weewx.conf` under `[[Belchertown]]`, in its `[[[Extras]]]` part, like this:

    ```
    [StdReport]
        [[Belchertown]]
            skin = Belchertown
            HTML_ROOT = /var/www/html/weewx/belchertown
            [[[Extras]]]
                theme = auto
                logo_image = "https://example.com/my-logo.png"
    ```

    If there's no `[[[Extras]]]` line yet, add it. After saving, restart weewx (`sudo systemctl restart weewx`) and wait for the next report. [Before you start](before-you-start.md#changing-a-settings-file) shows how to edit the file.

## The basics

### Change my site's name

Without a logo, the site shows `site_title` in the top left:

```
            site_title = "Hilltop Weather"
```

The heading on the home page and the text in the footer are "labels". They go in a `[[[Labels]]]` part next to `[[[Extras]]]`:

```
        [[[Labels]]]
            [[[[Generic]]]]
                home_page_header = "Hilltop Weather Conditions"
                footer_copyright_text = "Hilltop Weather"
```

More: [Change the site title and other text](customize.md#change-the-site-title-and-other-text).

### Add my logo

Put the logo picture on the web somewhere (your own site is fine) and give its **full** address. About 330 by 80 pixels fits best:

```
            logo_image = "https://example.com/my-logo.png"
            logo_image_dark = "https://example.com/my-logo-white.png"
```

`logo_image_dark` is optional, for a version that shows up on the dark background.

### Show metric units

That's a weewx setting, not a Belchertown one: see [Use metric units](customize.md#use-metric-units). Visitors can also switch between °F and °C themselves with the units button in the header.

### Use dark mode, or switch at sunset

```
            theme = auto
```

`light` or `dark` keeps it fixed; `auto` switches to dark at sunset and back at sunrise. Visitors can flip it with the moon/sun button.

### Show the site in my language

`lang` goes in the `[[Belchertown]]` section itself, not in `[[[Extras]]]`:

```
    [[Belchertown]]
        skin = Belchertown
        lang = de
```

German (`de`), French (`fr`), Italian (`it`), Catalan (`ca`) and Swedish (`sv`) are complete. See [Translations](translations.md).

### Change the About page

Copy `about.inc.example` to `about.inc` in the Belchertown skin folder and edit it. Plain text works, and HTML if you know it. Package install:

```
cd /etc/weewx/skins/Belchertown
sudo cp about.inc.example about.inc
sudo nano about.inc
```

The page updates at the next report; there's no need to restart weewx for this one. More: [About and Records pages](customize.md#about-and-records-pages).

## The home page

### Change what's on the home page, or the order

```
            home_sections = conditions, forecast, charts
```

The blocks are `conditions`, `forecast`, `onthisday`, `snapshot` and `charts`. List them in the order you want; leave one out to hide it. See [Choose what's on the home page](customize.md#choose-whats-on-the-home-page-and-in-what-order).

### Show my webcam picture

Add your own block. Make up a name, here `webcam`, put it in `home_sections`, and create a file called `home_webcam.inc` in the Belchertown skin folder:

```
            home_sections = conditions, webcam, forecast, snapshot, charts
```

`home_webcam.inc`:

```html
<div style="text-align: center;">
    <img src="https://example.com/webcam/latest.jpg" style="max-width: 100%;" alt="Webcam">
</div>
```

### Change or remove the radar

The radar is a Windy.com map. To zoom it in or out, or show something else on it:

```
            radar_zoom = 9
            radar_overlay = wind
```

To use your own map or picture instead, set `radar_html` to any HTML. All the radar options are in [All skin options](options.md).

### Turn off the forecast, alerts or earthquakes

```
            forecast_enabled = 0
            forecast_alert_enabled = 0
            earthquake_enabled = 0
```

Use whichever you need. Earthquakes are off unless you turn them on with `earthquake_enabled = 1`.

### Show the forecast in °C

```
            forecast_units = si
```

`si` is metric with wind in meters per second, `ca` is metric with wind in km/h, `uk2` is metric with wind in mph. See [Forecast units](forecasts.md#forecast-units).

### Hide the °F/°C button

```
            unit_toggle_enabled = 0
```

### Add a page or a menu link

Put links in an optional `menu.inc` file, and add whole pages with one setting in `weewx.conf`. See [Your own pages and charts](charts/custom-pages.md).

## Charts

### Add a chart

The easiest way is the [chart builder](charts/chart-builder.md) on your own site: open `chart-builder/` at the end of your site's address, pick what to plot, and copy the text it gives you into `graphs.conf`. Or copy one from the [chart gallery](charts/gallery.md).

`graphs.conf` is in the Belchertown skin folder. If it isn't there yet, make it from the example first:

```
cd /etc/weewx/skins/Belchertown
sudo cp graphs.conf.example graphs.conf
```

Chart changes show up at the next report. No restart needed.

### Remove a chart, or change the home page charts

Open `graphs.conf` and delete the chart's section: the line with its name in double brackets (`[[chart3]]`) and everything indented under it. The home page shows the charts in the `[homepage]` group; to show the Today charts there instead, set `highcharts_homepage_graphgroup = day`.

### Use the free chart library (ECharts)

```
            chart_library = echarts
```

Highcharts is free for personal sites only. ECharts is free for any site. See [Highcharts or ECharts](charts/index.md#highcharts-or-echarts).

## More

### Make the home page update every few seconds

That's [live updates](live-updates.md), with MQTT. It takes a little more setup: the page walks you through it.

### Show the weather on a TV or spare screen

Add `?view=kiosk` to your home page's address. See [Wall display](kiosk.md).

### Build the site right away, without waiting

Waiting for the next report (5 minutes or so) always works. To build it now on a pip install, run `weectl report run`. On a package install, run it as the user weewx runs as, so the files keep the right owner:

```
sudo -u $(systemctl show weewx -p User --value) weectl report run
```

If that answers `unknown user` or similar, your weewx runs as the administrator: use `sudo weectl report run`.

### Find out why something isn't working

Turn on [debug mode](troubleshooting.md#debug-mode) and look at the weewx log. [Troubleshooting and FAQ](troubleshooting.md) has the common problems.

### Back up, upgrade or uninstall

See [Upgrade](upgrade.md): it covers all three.
