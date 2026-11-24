# Upgrade

New versions of Belchertown fix problems and add features. Upgrading takes about 5 minutes: back up, install the new version over the old one, restart weewx. Your settings and your own files stay.

This page is for upgrading Belchertown 3 to a newer 3.x. Coming from Belchertown 1.x? Follow [Upgrading from 1.x](upgrading.md) instead; it covers the bigger changes.

!!! tip "Hear about new versions"
    On the [Belchertown GitHub page](https://github.com/poblabs/weewx-belchertown), click **Watch**, then **Custom**, tick **Releases** and **Apply**. GitHub emails you when a new version comes out. (You need a free GitHub account.) The [releases page](https://github.com/poblabs/weewx-belchertown/releases) lists every version with what changed.

## Which version do I have?

```
sudo weectl extension list
```

(Leave out `sudo` on a pip install.) The Belchertown line shows the version. It's also in your site's page source: in the browser, right-click the page, choose **View page source**, and search for `Skin Version`.

## What an upgrade keeps and replaces

Installing a new version copies the skin's own files over the old ones. Anything the skin doesn't ship is left alone. We tested this by upgrading a station from 3.0.1 to 3.1.0:

| | After an upgrade |
| --- | --- |
| Your settings in `weewx.conf` (the `[[Belchertown]]` section: logo, theme, forecast, MQTT and the rest) | **Kept.** weewx also saves a dated copy of `weewx.conf` before it changes anything. |
| `graphs.conf` (your charts) | **Kept.** |
| `about.inc`, `records.inc`, `custom.css`, `header.inc`, `index_radar.inc`, `home_*.inc`, `index_hook_*.inc` (your own files) | **Kept.** |
| Your weather data and the website folder | **Not touched.** The site is rebuilt at the next report. |
| `skin.conf` | **Replaced.** Changes you made in it are lost, which is why settings belong in `weewx.conf` ([how](customize.md)). |
| Any other file the skin ships (`graphs.conf.example`, `style.css`, the `js` files, the language files, the page templates) | **Replaced.** Changes you made in them are lost. |

So the rule is: **never change the skin's own files.** Put settings in `weewx.conf`, styles in `custom.css`, charts in `graphs.conf`, and your own text in the `.inc` files. Then upgrades are painless.

## 1. Back up

One command saves your Belchertown folder and `weewx.conf` in a single dated file in your home folder.

=== "Package install"

    ```
    sudo tar czf ~/belchertown-backup-$(date +%Y%m%d).tar.gz /etc/weewx/skins/Belchertown /etc/weewx/weewx.conf
    ```

=== "pip install"

    ```
    tar czf ~/belchertown-backup-$(date +%Y%m%d).tar.gz ~/weewx-data/skins/Belchertown ~/weewx-data/weewx.conf
    ```

**You should see** a message like `Removing leading '/' from member names`; that's normal. `ls ~` lists the new backup file.

If you keep `custom.css` in your website folder rather than the skin folder, copy it too, for example `cp /var/www/html/weewx/belchertown/custom.css ~/`.

## 2. Install the new version

The same command as a [new install](install.md#2-install-the-skin), with the new version number in both places. For 3.2.3:

=== "Package install"

    ```
    sudo weectl extension install https://github.com/poblabs/weewx-belchertown/releases/download/weewx-belchertown-3.2.3/weewx-belchertown-3.2.3.tar.gz
    ```

=== "pip install"

    ```
    weectl extension install https://github.com/poblabs/weewx-belchertown/releases/download/weewx-belchertown-3.2.3/weewx-belchertown-3.2.3.tar.gz
    ```

Type `y` when it asks. **You should see** `Finished installing extension Belchertown`. There's no need to uninstall the old version first, and you shouldn't: uninstalling removes your `[[Belchertown]]` settings from `weewx.conf`.

## 3. Restart weewx and check

```
sudo systemctl restart weewx
```

Wait for the next report (5 to 10 minutes), then reload your site. Your browser may keep old copies of some files for a while: if something looks half old, half new, reload with Ctrl + Shift + R (Command + Shift + R on a Mac).

## 4. Read what's new

The [changelog](https://github.com/poblabs/weewx-belchertown/blob/master/changelog) lists what changed in each version, including any setting you might want to turn on. New features are usually off until you turn them on, so the site looks the same after an upgrade.

## Going back to an older version

If a new version gives you trouble, install the old one again the same way as step 2, with its version number (every version is on the [releases page](https://github.com/poblabs/weewx-belchertown/releases)). For example, to go back to 3.2.2:

```
sudo weectl extension install https://github.com/poblabs/weewx-belchertown/releases/download/weewx-belchertown-3.2.2/weewx-belchertown-3.2.2.tar.gz
```

Restart weewx. Then please [tell us what went wrong](https://github.com/poblabs/weewx-belchertown/issues/new/choose), so it can be fixed.

## Restoring from your backup

To put back a file from the backup, for example `graphs.conf`, first list what's in it:

```
tar tzf ~/belchertown-backup-20261116.tar.gz
```

(Use your backup's date.) Then unpack it into a folder of its own and copy what you need from there:

```
mkdir ~/restore && tar xzf ~/belchertown-backup-20261116.tar.gz -C ~/restore
```

The files are in `~/restore`, under the same folder names as before (for example `~/restore/etc/weewx/skins/Belchertown/graphs.conf`). Copy one back with `sudo cp`, then restart weewx.

## Upgrading weewx itself

Belchertown 3 works with every weewx 5 version. Upgrading weewx (for example from 5.0 to 5.1) doesn't remove the skin: follow the [weewx upgrade guide](https://weewx.com/docs/), then check that `weectl extension list` still shows Belchertown and that your site updates.

## Uninstall

To remove Belchertown completely:

```
sudo weectl extension uninstall Belchertown
```

(Leave out `sudo` on a pip install.) This removes the skin's own files and its `[[Belchertown]]` section from `weewx.conf`. Your own files (`graphs.conf`, `about.inc`, `custom.css` and the like) stay in the skin folder. Restart weewx afterwards. The pages it already built stay in your website folder until you delete them, and your weather data isn't touched. Make a [backup](#1-back-up) first if you might come back.
