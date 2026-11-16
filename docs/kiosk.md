# Wall display (kiosk view)

To show your weather on a TV, tablet or a spare monitor, open your home page with `?view=kiosk` added to the end of the address:

```
http://your-server/weewx/belchertown/?view=kiosk
```

That shows only the current conditions, sun and moon, radar and forecast, with no menu, records or charts, sized to fit a 1280 × 800 screen without scrolling. Live updates never time out in this view and reconnect on their own. Nothing needs to be turned on; it uses your normal settings.

You can force a theme too, which helps on a screen that's always on:

```
http://your-server/weewx/belchertown/?view=kiosk&theme=dark
```

??? note "Start the display automatically on a Raspberry Pi"

    On Raspberry Pi OS with the LXDE desktop, put this in `/home/pi/.config/lxsession/LXDE-pi/autostart` (change the address to yours):

    ```
    @sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' /home/pi/.config/chromium/Default/Preferences
    @sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' /home/pi/.config/chromium/Default/Preferences
    @chromium-browser --start-fullscreen --kiosk --disable-site-isolation-trials --enable-low-end-device-mode --renderer-process-limit=2 --app=http://your-server/weewx/belchertown/?view=kiosk
    @unclutter -idle 0.1
    ```

??? note "Use a different MQTT broker for the display"

    If the display sits on the same network as your MQTT broker, it can connect to it directly instead of through the internet. Add these to `[[[Extras]]]`. Anything left empty uses the normal [live update](live-updates.md) setting.

    | Name | Default | Description
    | ---- | ------- | -----------
    | mqtt_websockets_host_kiosk | "" | The broker for the display, for example `localhost` or `192.168.1.10`.
    | mqtt_websockets_port_kiosk | "" | Its websockets port.
    | mqtt_websockets_ssl_kiosk | "" | 1 if it uses SSL, 0 if not.
