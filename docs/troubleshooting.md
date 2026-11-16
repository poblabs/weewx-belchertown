# Troubleshooting and FAQ

## Debug mode

Debug mode makes the skin explain what it is doing. It writes messages about live updates (MQTT), the light and dark theme, times and dates, and the charts. It is the first thing to turn on when a page looks wrong or a feature doesn't work.

**To turn it on**, open `weewx.conf` in a text editor, add `belchertown_debug = 1` to the `[[[Extras]]]` part of the `[[Belchertown]]` section, save the file and restart weewx (`sudo systemctl restart weewx`):

```
[StdReport]
    [[Belchertown]]
        [[[Extras]]]
            belchertown_debug = 1
```

**Where the messages appear:**

* **In your browser.** Open your site, press F12 (on a Mac: Option + Command + I) and click the "Console" tab. Reload the page. The debug messages are listed there, and errors show in red.
* **In the weewx log.** This is where weewx writes what happened when it built the site. On most systems you can read it with `sudo journalctl -u weewx -n 300`, or by looking in the file `/var/log/syslog`. For more detail there, set `debug = 1` near the top of `weewx.conf` and restart weewx.

For a quick look without restarting weewx, add `?debug=true` to the end of your site's address instead, for example `http://example.com/?debug=true`. That turns it on for you only, on that page.

Set `belchertown_debug = 0` again when you are done.

**Reporting a bug?** Paste these into the [bug report](https://github.com/poblabs/weewx-belchertown/issues/new/choose):

1. The lines from the weewx log that mention `belchertown`, from around the time of the problem.
2. Any red lines from the browser console.
3. Your weewx version (`weectl --version`) and Belchertown version (`weectl extension list`).
4. The `[[Belchertown]]` section of your `weewx.conf`, with passwords and API keys removed.

## The skin is slow after upgrading to weewx 5

Belchertown expects the `wview-extended` database layout that weewx has used since version 4. A database created before weewx 4 may be missing `appTemp`, and weewx 5 then calculates it on the fly, which is slow. Back up your database, then add the column and fill it in with `weectl database add-column appTemp` and `weectl database calc-missing`. [Issue 924](https://github.com/poblabs/weewx-belchertown/issues/924) has the details.

## Questions

??? note "Do I have to use live updates, forecasts, earthquakes, the radar or the charts?"

    No. Everything beyond the basic install is optional. Leave a feature off and the site still works; it just updates once per archive period instead of live.

??? note "The units are wrong on the live-updated values."

    The live values come from the weewx-mqtt extension, so set the units there. For example, to send today's rain in millimeters:

    ```
    [[MQTT]]
            [[[inputs]]]
                    [[[[dayRain]]]]
                            name = dayRain_mm
                            units = mm
    ```

??? note "My NOAA reports are blank."

    Right after installing, give weewx a few archive periods to fill them in.

??? note "I see NAN in some places."

    weewx hasn't collected enough data yet. Give it a few more archive periods.

??? note "Why does the skin take a while to build?"

    The charts read your whole database, from today back to the first record. A big database or a slow computer (like a Raspberry Pi) takes longer. Turning the charts off or using faster hardware helps.

??? note "The charts don't update right away after an archive period."

    That's on purpose: the home page waits 30 seconds so the new chart data is ready. Only the home page updates live; the other pages show new data when reloaded.

??? note "The forecast's "Last Updated" time changes format when the page loads."

    The page is built with your server's date format, and the browser then reformats it with Day.js. The two formats can differ slightly for some locales.

??? note "How can I tell whether new forecast or earthquake data was downloaded?"

    Check the weewx log for "forecast downloaded". Errors show up there too; earthquake downloads only appear with debug on.

## Charts don't show or look wrong

See [If something goes wrong](charts/graphs-conf.md#if-something-goes-wrong) on the graphs.conf page.
