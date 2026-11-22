# Upgrading from 1.x

This page is for anyone running Belchertown 1.3.1, or an older 1.x version, who wants to move to Belchertown 3.0. It covers what to back up, how to install, what looks different afterwards, and what to check.

Why 3.0 and not 2.0? The 2.x numbers belong to [New Belchertown](https://github.com/uajqq/weewx-belchertown-new), a separate fork by uajqq. This skin goes from 1.3.1 straight to 3.0 to keep the two apart. If you are on New Belchertown, this page is not for you.

## Who should upgrade

**Belchertown 3 needs weewx 5.0 or newer.** To see which weewx you have, run:

```
weectl --version
```

If that command isn't found, you are on weewx 3 or 4. In that case, stay on [Belchertown 1.3.1](https://github.com/poblabs/weewx-belchertown/releases/tag/weewx-belchertown-1.3.1), which keeps working but is no longer updated. The 3.0 installer refuses to run on weewx 3 or 4, so it can't break an older system by accident. If you want 3.0, upgrade weewx to version 5 first, following the upgrade guide in the [weewx documentation](https://weewx.com/docs/), and check that your site still works on 1.3.1 before going further.

## Before you start: back up

The installer replaces the skin's own files. Files you created yourself are not touched, but make a copy of everything first so you can go back.

Your Belchertown files are in this folder, depending on how weewx was installed:

| How weewx was installed | Belchertown files | weewx.conf |
| --- | --- | --- |
| Package (`apt`, `yum`, `dnf`) | `/etc/weewx/skins/Belchertown` | `/etc/weewx/weewx.conf` |
| `pip` or git | `~/weewx-data/skins/Belchertown` | `~/weewx-data/weewx.conf` |

1. Copy the whole `skins/Belchertown` folder somewhere safe, for example your home folder. For a package install:

   ```
   sudo cp -a /etc/weewx/skins/Belchertown ~/Belchertown-1.3.1-backup
   ```

   For a pip or git install:

   ```
   cp -a ~/weewx-data/skins/Belchertown ~/Belchertown-1.3.1-backup
   ```

2. Make a copy of `weewx.conf` too, in the same way. Your Belchertown settings live in its `[[Belchertown]]` section.

These are the files in the skin folder that are yours, if you have them. Note which ones you have, because they are the ones to check after the upgrade:

* `graphs.conf` (your charts)
* `about.inc` and `records.inc` (your About and Records page text)
* `header.inc` (extra lines for the top of every page)
* `index_radar.inc` (your own radar or webcam)
* `index_hook_after_station_info.inc`, `index_hook_after_forecast.inc`, `index_hook_after_snapshot.inc`, `index_hook_after_charts.inc` (your own content on the home page)
* any `home_<name>.inc` file
* `records-table.inc`, if you made one

* `custom.css` (your own styles), if you keep it in the skin folder. It can also be in your website folder (the `HTML_ROOT` of `[[Belchertown]]`). Upgrades touch neither, but copy it anyway.

## Install 3

You install 3 over the top of 1.3.1. There is no need to uninstall first, and you shouldn't: uninstalling removes your `[[Belchertown]]` settings from `weewx.conf`. Installing keeps them.

1. Download the newest `weewx-belchertown-3.x.x.tar.gz` (3.2.1 at the time of writing) from the [releases page](https://github.com/poblabs/weewx-belchertown/releases).
2. Install it. The command depends on how weewx was installed:

   **Package install:**

   ```
   sudo weectl extension install weewx-belchertown-3.2.1.tar.gz
   ```

   **pip install:** first turn on the Python environment weewx runs in (usually `~/weewx-venv`), then install:

   ```
   source ~/weewx-venv/bin/activate
   weectl extension install weewx-belchertown-3.2.1.tar.gz
   ```

   **git install:** run weectl from your weewx source folder (usually `~/weewx`):

   ```
   python3 ~/weewx/src/weectl.py extension install weewx-belchertown-3.2.1.tar.gz
   ```

   Answer `y` when it asks whether to install.
3. Restart weewx:

   ```
   sudo systemctl restart weewx
   ```

4. Wait for the next archive period (usually 5 minutes), or build the site right away with `weectl report run`. Then open your site and reload it.

[Install](install.md) has the same steps for a new install.

## What you will notice

* **The forecast is on.** `forecast_enabled` now defaults to 1, and `forecast_provider = auto` uses [Open-Meteo](https://open-meteo.com), which is free and needs no account. If you set `forecast_api_id` for Xweather (the new name for AerisWeather), it keeps using Xweather as before. In the US, weather alerts come from the National Weather Service with no setup. To keep the forecast off, set `forecast_enabled = 0`. See [Forecasts](forecasts.md).
* **The kiosk page is now a view of the home page.** `kiosk.html` and the Raspberry Pi page (`/pi`) are gone. Add `?view=kiosk` to your home page address instead, for example `http://your-server/weewx/belchertown/?view=kiosk`. If a wall display or Raspberry Pi opens the old address, change it. See [Wall display (kiosk view)](kiosk.md).
* **A layout button** (four squares) in the header lets visitors put the forecast, radar or charts first. Storm mode switches to the radar layout by itself during rain or a storm alert. See [Home page layouts](customize.md#home-page-layouts).
* **A units button** in the header switches the whole site between °F and °C (and the other US and metric units) for that visitor. Your station keeps its own units. To hide it, set `unit_toggle_enabled = 0`. See [Units button](customize.md#units-button-f-or-c).
* **A chart builder** at `chart-builder/` on your own site, for example `http://your-server/weewx/belchertown/chart-builder/`. It isn't in the menu. Pick what to plot, see the chart drawn from your data, and copy the text into `graphs.conf`. See [Chart builder](charts/chart-builder.md).
* A new home page block, "On this day", and a new Records page.
* The header stays at the top of the screen while you scroll. To turn that off, set `sticky_header = 0`.

## What to check afterwards

Go through this list once the new site has been built.

1. **Custom files that use jQuery keep working.** 3.0 no longer loads jQuery or Bootstrap for its own pages. When one of your `.inc` files uses jQuery, the skin loads it for that file and says so in the weewx log, for example `index_radar.inc uses jQuery, so jQuery is loaded for it.` The same goes for Bootstrap classes the skin doesn't style. Nothing needs to change. If you want the page a little lighter, see [how to update those files](customize.md#your-own-scripts-jquery-and-bootstrap). To read the weewx log, use `sudo journalctl -u weewx -n 300` or look in `/var/log/syslog`.
2. **Change `moment()` to `dayjs()` in your own files.** moment.js is gone; Day.js replaces it and uses the same date format codes. If any of your `.inc` files call `moment(`, change it to `dayjs(`. Date format labels you set in `weewx.conf`, such as `time_last_updated = "LL, LTS"`, keep working as they are.
3. **Anything else that reads `json/forecast.json` needs updating.** The file has a new format, the same for every forecast provider. If a script, Home Assistant or another website reads it, update that program. The format is described at the top of `bin/user/belchertown_forecast.py`.
4. **Removed options are ignored.** You can leave them in `weewx.conf` or delete them; they do nothing now:
   * `twitter_enabled`, and the labels `twitter_text`, `twitter_owner` and `twitter_hashtags` (the Twitter button is gone)
   * `aeris_map` (the static Xweather map is gone; the radar is the Windy map or your own `radar_html`)
   * `radar_html_kiosk`, `radar_width_kiosk`, `radar_height_kiosk`, `forecast_interval_hours_kiosk` and `aqi_enabled_kiosk`
   * `pi_theme` and `pi_kiosk_bold`
   * the labels `mqtt_websockets_connected_pi` and `mqtt_websockets_waiting_pi`

   The `mqtt_websockets_host_kiosk`, `mqtt_websockets_port_kiosk` and `mqtt_websockets_ssl_kiosk` options still work, for the new kiosk view. Indoor temperature and humidity are no longer written to `weewx_data.json`.
5. **Gauge sizes in `graphs.conf`.** Charts now use Highcharts 13. If your `graphs.conf` gives a gauge `radius` or `innerRadius` as a plain number, Highcharts now reads it as pixels instead of a percentage. Put it in quotes with a percent sign to keep the old size, for example `radius = 70` becomes `radius = "70%"`.
6. **Links to `belchertown-dark.min.css`.** That stylesheet is gone; the skin's dark mode is now part of `style.css`. If your `custom.css`, `header.inc` or another file of yours links to `belchertown-dark.min.css`, remove that line. Rules in `custom.css` that start with `.dark` still apply in dark mode.
7. **Your own changes to `js/belchertown.js.tmpl`.** That file is gone. `js/belchertown.js` is now a plain file, and your settings reach it through `js/belchertown-config.js`. If you had edited `belchertown.js.tmpl`, make the same changes in `belchertown.js` (and keep a copy, because upgrades replace it).
8. **Old files in your website folder.** `kiosk.html` and the `pi` folder from 1.3.1 are no longer updated. Delete them once nothing opens them.
9. **The site is slow to build.** If your database was created before weewx 4, see [The skin is slow after upgrading to weewx 5](troubleshooting.md#the-skin-is-slow-after-upgrading-to-weewx-5).

If something doesn't look right, turn on [debug mode](troubleshooting.md#debug-mode) and check the weewx log.

## Going back to 1.3.1

If 3.0 doesn't work for you, you can put 1.3.1 back.

1. Download the 1.3.1 file from its [release page](https://github.com/poblabs/weewx-belchertown/releases/tag/weewx-belchertown-1.3.1).
2. Install it over 3.0 with the same `weectl extension install` command you used above, using the 1.3.1 file name.
3. Compare your files with the backup you made, and copy back any of yours that changed (`graphs.conf`, `.inc` files, `custom.css`).
4. If you removed any old options from `weewx.conf`, copy them back from your backup of `weewx.conf`.
5. Restart weewx and wait for the next archive period.

If you went back because of a problem, please [open an issue](https://github.com/poblabs/weewx-belchertown/issues/new/choose) so it can be fixed.
