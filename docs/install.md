# Install

These steps get you a working site. Everything else on this site is optional.

**1. Download** the latest `weewx-belchertown-x.x.x.tar.gz` from the [releases page](https://github.com/poblabs/weewx-belchertown/releases).

**2. Install it.** Replace `x.x.x` with the version you downloaded:

```
weectl extension install weewx-belchertown-x.x.x.tar.gz
```

**3. Check your station's location.** Open your `weewx.conf` (see the table below) and make sure the `[Station]` section has your `latitude` and `longitude`. The forecast, earthquakes and sunrise/sunset all use them.

**Where's my weewx.conf?** It depends on how you installed weewx:

| How weewx was installed | weewx.conf | Belchertown files | weewx's website folder |
| --- | --- | --- | --- |
| Package (`apt`, `yum`, `dnf`) | `/etc/weewx/weewx.conf` | `/etc/weewx/skins/Belchertown` | `/var/www/html/weewx` |
| `pip` | `~/weewx-data/weewx.conf` | `~/weewx-data/skins/Belchertown` | `~/weewx-data/public_html` |

**4. Choose where the site goes.** The installer sets `HTML_ROOT = belchertown` in the `[[Belchertown]]` section, which puts the site in a `belchertown` folder next to `weewx.conf`, where your web server probably can't see it. Change it to a folder inside your website, for example:

```
    [[Belchertown]]
        skin = Belchertown
        HTML_ROOT = /var/www/html/weewx/belchertown
```

**5. Restart weewx:**

```
sudo systemctl restart weewx
```

**6. Wait** for the next archive period (how often weewx saves a record, usually every 5 minutes), or build the site right away with:

```
weectl report run
```

**7. Open your website** at the matching address, for example `http://your-server/weewx/belchertown`. To make it your main page, see [Make Belchertown your main website](#make-belchertown-your-main-website).

## Make Belchertown your main website

To make Belchertown the main site and move weewx's standard pages into a `weewx` subfolder:

1. In `weewx.conf`, under `[StdReport]`, change `HTML_ROOT` to `/var/www/html/weewx` (or wherever your website lives, plus `/weewx`).
2. Under `[[Belchertown]]`, set `HTML_ROOT` to your website's main folder:

```
    [[Belchertown]]
        skin = Belchertown
        HTML_ROOT = /var/www/html
```

3. Optional but recommended: empty the website folder so Belchertown starts clean.
4. Restart weewx and wait for the next archive period.


## Uninstall

```
weectl extension uninstall Belchertown
```

## Development version

To try the newest changes before they're released, download the [`next` branch](https://github.com/poblabs/weewx-belchertown/archive/next.zip) and install it with `weectl extension install next.zip`, or copy its files over your `skins/Belchertown` and `bin/user` folders. Then restart weewx. The `next` branch is where the 3.0 rewrite happens, so expect rough edges.
