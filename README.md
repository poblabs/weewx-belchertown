# Belchertown weewx skin

[![Latest Stable Version](https://img.shields.io/github/v/release/poblabs/weewx-belchertown.svg?style=flat-square)](https://github.com/poblabs/weewx-belchertown/releases) [![Docs](https://img.shields.io/badge/docs-poblabs.github.io-blue.svg?style=flat-square)](https://poblabs.github.io/weewx-belchertown/) [![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=flat-square&amp;logo=paypal&amp;colorA=aaaaaa)](https://paypal.me/pobhq)

A skin (website theme) for the [weewx weather software](https://weewx.com), modeled after my website [BelchertownWeather.com](https://belchertownweather.com).

**📖 Documentation: [poblabs.github.io/weewx-belchertown](https://poblabs.github.io/weewx-belchertown/)**

* **A chart builder**: make a chart by pointing and clicking, watch it draw from your own data, and copy the text it gives you. No chart settings to write by hand ([see below](#chart-builder)).
* **Charts you design**: lines, columns, wind roses, Hays charts, temperature radials and gauges, with a [gallery](https://poblabs.github.io/weewx-belchertown/charts/gallery/) of every chart type to copy from.
* **Highcharts or Apache ECharts**: ECharts is free for any website, including businesses, clubs and non-profits ([compare them](https://poblabs.github.io/weewx-belchertown/charts/#highcharts-or-echarts)).
* **Live updates** on the home page without reloading, with MQTT.
* **Forecasts, air quality and (in the US) weather alerts** with no setup, from Open-Meteo and the National Weather Service; Xweather optional.
* **Records**, "On this day" and your nearest recent earthquake.
* **Light and dark mode** and a **°F/°C button**, on phones, tablets and wall displays.

![The home page in light and dark mode](assets/light_dark_modes.jpg)

## Chart builder

Every Belchertown site has a chart builder at `chart-builder/`. Pick what to plot, how much time it covers and how much detail, and the chart draws itself from your station's data as you go. When it looks right, press Copy and paste the text into `graphs.conf`; the chart appears after the next report. It only reads your data, so it needs no password, and it works with both Highcharts and ECharts.

![The chart builder: settings on the left, the chart drawn from the station's data on the right](docs/assets/chart-builder/builder-echarts.webp)

**[Try it on BelchertownWeather.com](https://belchertownweather.com/chart-builder/)** · [Step-by-step guide](https://poblabs.github.io/weewx-belchertown/charts/chart-builder/)

> [!IMPORTANT]
> **Belchertown 3 requires weewx 5.0 or newer.** On weewx 3 or 4, use [Belchertown 1.3.1](https://github.com/poblabs/weewx-belchertown/releases/tag/weewx-belchertown-1.3.1). Coming from 1.3.1? See [Upgrading from 1.x](https://poblabs.github.io/weewx-belchertown/upgrading/).

## Quick start

1. Install it (leave out `sudo` on a pip install, and answer `y`):

    ```
    sudo weectl extension install https://github.com/poblabs/weewx-belchertown/releases/download/weewx-belchertown-3.2.2/weewx-belchertown-3.2.2.tar.gz
    ```

2. In `weewx.conf`, set `HTML_ROOT` in the `[[Belchertown]]` section to a folder your web server shows, for example `/var/www/html/weewx/belchertown`, and check that `[Station]` has your `latitude` and `longitude`.
3. Restart weewx (`sudo systemctl restart weewx`) and open your site after the next report.
4. Make your first chart: open `chart-builder/` on your new site.

New to this? The [install guide](https://poblabs.github.io/weewx-belchertown/install/) goes one step at a time, and [Before you start](https://poblabs.github.io/weewx-belchertown/before-you-start/) explains the terminal and `weewx.conf`. Already running Belchertown? See [Upgrade](https://poblabs.github.io/weewx-belchertown/upgrade/).

## Help

* [How do I...?](https://poblabs.github.io/weewx-belchertown/how-do-i/) and [Troubleshooting and FAQ](https://poblabs.github.io/weewx-belchertown/troubleshooting/)
* Questions: [GitHub Discussions](https://github.com/poblabs/weewx-belchertown/discussions)
* Found a bug? [Open an issue](https://github.com/poblabs/weewx-belchertown/issues/new/choose)

## Development version

To try the newest changes before they're released, download the [`next` branch](https://github.com/poblabs/weewx-belchertown/archive/next.zip) and install it with `weectl extension install next.zip`, then restart weewx. Expect rough edges.

The documentation lives in the `docs` folder of this repository and is published to the site above whenever `master` changes. Corrections are welcome as pull requests.

## Donate

This project took a lot of coffee to create. If you enjoy this skin and find some value from it, [click here to buy me another cup of coffee](https://paypal.me/pobhq) :)

## Credits

See [Credits and thanks](https://poblabs.github.io/weewx-belchertown/about/). Belchertown is free software under the GNU GPL v3.
