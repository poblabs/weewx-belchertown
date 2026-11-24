# Install

Six steps, about 15 minutes. Each step says what you should see, so you know it worked before moving on. New to typing commands or editing `weewx.conf`? Read [Before you start](before-you-start.md) first; it explains both.

!!! info "Belchertown 3 needs weewx 5.0 or newer"
    Check with `weectl --version`. On weewx 3 or 4, use [Belchertown 1.3.1](https://github.com/poblabs/weewx-belchertown/releases/tag/weewx-belchertown-1.3.1) instead. Already running Belchertown? See [Upgrade](upgrade.md).

## 1. Check that weewx is running

```
sudo systemctl status weewx
```

**You should see** `active (running)`. Press `q` to leave. If weewx isn't running, get it working first with the [weewx documentation](https://weewx.com/docs/); Belchertown needs it.

## 2. Install the skin

This downloads Belchertown 3.1.0 and installs it in one go. Pick your kind of weewx ([which one do I have?](before-you-start.md#which-kind-of-weewx-you-have)):

=== "Package install"

    ```
    sudo weectl extension install https://github.com/poblabs/weewx-belchertown/releases/download/weewx-belchertown-3.2.3/weewx-belchertown-3.2.3.tar.gz
    ```

=== "pip install"

    ```
    weectl extension install https://github.com/poblabs/weewx-belchertown/releases/download/weewx-belchertown-3.2.3/weewx-belchertown-3.2.3.tar.gz
    ```

    (Turn on weewx's Python first with `source ~/weewx-venv/bin/activate`, as in [Before you start](before-you-start.md#which-kind-of-weewx-you-have).)

When it asks `Install extension ... (y/n)?`, type `y` and press Enter.

**You should see** `Finished installing extension Belchertown` at the end. It also says `Saved copy of configuration as ...`: weewx keeps a dated copy of your `weewx.conf` before changing it, so you can always go back.

??? note "No internet on the weewx computer, or want a different version?"
    Download the `.tar.gz` file from the [releases page](https://github.com/poblabs/weewx-belchertown/releases) on any computer, copy it to the weewx computer, and install it by its file name instead of the web address, for example `sudo weectl extension install weewx-belchertown-3.2.3.tar.gz`.

## 3. Tell it where to put the website

The installer added a `[[Belchertown]]` section to `weewx.conf`. Its `HTML_ROOT` line says where the web pages go, and it starts out pointing at a folder your web server can't show. Change it so the site sits next to weewx's standard pages.

Open `weewx.conf` ([how](before-you-start.md#changing-a-settings-file)), find `[[Belchertown]]` (Ctrl + W in nano), and change the `HTML_ROOT` line under it:

=== "Package install"

    ```
        [[Belchertown]]
            skin = Belchertown
            HTML_ROOT = /var/www/html/weewx/belchertown
    ```

=== "pip install"

    ```
        [[Belchertown]]
            skin = Belchertown
            HTML_ROOT = public_html/belchertown
    ```

    (This puts it inside `~/weewx-data/public_html`, next to the standard pages, wherever your web server already shows those.)

Leave the other lines in the section as they are.

**While you're in the file**, find the `[Station]` section near the top and check that `latitude` and `longitude` are your station's. The forecast, sunrise and sunset, and earthquakes all use them. Numbers south of the equator and west of Greenwich are negative: Belchertown, Massachusetts is `latitude = 42.28` and `longitude = -72.40`.

Save (Ctrl + O, Enter) and leave (Ctrl + X).

## 4. Restart weewx

```
sudo systemctl restart weewx
```

Then check it came back:

```
sudo systemctl status weewx
```

**You should see** `active (running)` again. If it says `failed`, there's most likely a typo in what you just changed: open `weewx.conf` again and compare it with the example above. Spaces at the start of the lines matter.

## 5. Wait for the first report

weewx builds the website after it saves each record, usually every 5 minutes. **Wait 5 to 10 minutes.** The first build takes longer than the rest, because the charts read your whole database once (up to a few minutes on a Raspberry Pi with years of data).

To check on it, watch the weewx log:

```
sudo journalctl -u weewx -f
```

**You should see** a line like `Generated 18 files for report Belchertown`. Press Ctrl + C to stop watching. (On some systems the log is in `/var/log/syslog` instead: `sudo tail -f /var/log/syslog`.)

## 6. Open your new website

Open the same address as weewx's standard pages, with `/belchertown/` added. On a package install, that's usually:

```
http://raspberrypi.local/weewx/belchertown/
```

Use your weewx computer's own name or address in place of `raspberrypi.local`. **You should see** your current conditions, the forecast and charts.

**It worked? Congratulations.** Bookmark it, then:

* [How do I...?](how-do-i.md): the everyday changes, such as your site's name, your logo, metric units and dark mode.
* [Make it yours](customize.md): everything you can change about the site.
* [Chart builder](charts/chart-builder.md): open `chart-builder/` on your new site and make your first chart by pointing and clicking.
* [Charts](charts/index.md): pick your own charts, and choose between Highcharts and the free ECharts.

## If it didn't work

**The browser says "Not Found" (404).**
The web pages aren't where your web server looks. Check that `HTML_ROOT` in step 3 matches your kind of install, that you restarted weewx, and that 10 minutes have passed. Then see whether the files exist (package install): `ls /var/www/html/weewx/belchertown`. An `index.html` in the list means the site was built and the address is the problem; try the address of the standard Seasons pages and add `belchertown/`.

**The page shows, but with no numbers, "NaN" or empty charts.**
weewx hasn't collected enough data yet, or the first build is still running. Give it a few archive periods.

**weewx won't start after the change.**
Undo the change: open `weewx.conf` again and compare with step 3, or copy back the dated copy the installer saved (`ls /etc/weewx/` shows it, with the date in its name). Then restart weewx.

**Something else.**
See [Troubleshooting and FAQ](troubleshooting.md), or ask in [GitHub Discussions](https://github.com/poblabs/weewx-belchertown/discussions) with the lines from the weewx log that mention `belchertown`.

## Make Belchertown your main website

So that visitors see Belchertown at your site's plain address (`http://raspberrypi.local/` instead of `.../weewx/belchertown/`), swap the two folders (package install shown):

1. In `weewx.conf`, find `HTML_ROOT` directly under `[StdReport]` (not the one under `[[Belchertown]]`) and set it to `/var/www/html/weewx`. That's where weewx's standard pages go; it's often already set to this.
2. Under `[[Belchertown]]`, set `HTML_ROOT` to the web server's main folder:

    ```
        [[Belchertown]]
            skin = Belchertown
            HTML_ROOT = /var/www/html
    ```

3. Optional but recommended: move anything else out of `/var/www/html` (such as the web server's own welcome page, `index.nginx-debian.html`) so Belchertown starts clean. Keep the `weewx` folder.
4. Restart weewx and wait for the next report.

If the log then says `Permission denied` for `/var/www/html`, weewx isn't allowed to write there. Give the folder to the user weewx runs as:

```
sudo chown $(systemctl show weewx -p User --value) /var/www/html
```

## Try the development version

To try the newest changes before they're released, install the `next` branch instead. It's where new features are tested, so expect rough edges:

```
sudo weectl extension install https://github.com/poblabs/weewx-belchertown/archive/next.zip
```

(Leave out `sudo` on a pip install.) Then restart weewx. To go back to the released version, install it again the same way as in step 2.
