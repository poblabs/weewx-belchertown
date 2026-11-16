# Live Updates with MQTT

Without live updates, your Belchertown site changes once per archive period (how often weewx saves a record, usually every 5 minutes). With live updates, the current conditions on the home page change every few seconds, as fast as your station reports, without reloading the page.

This page walks through the most common setup: an MQTT broker on the same computer as weewx. If you don't have a server of your own and only want to try it, see [Public MQTT Brokers](brokers.md).

## How it works

Three pieces work together:

1. **A broker.** MQTT is a small messaging system. The broker is the program in the middle: weewx sends readings to it, and it passes them on to anyone listening. [Mosquitto](https://mosquitto.org) is the usual choice.
2. **weewx's MQTT extension** ([weewx-mqtt](https://github.com/matthewwall/weewx-mqtt), written by Matthew Wall). It sends each new reading from weewx to the broker. The Belchertown skin does not send anything itself.
3. **The skin.** Each visitor's web browser connects to the broker and listens. Browsers can't speak plain MQTT, so they connect over **websockets**, a kind of connection that stays open. Your broker needs a websockets port for this, separate from its plain MQTT port.

So there are two ports to keep apart:

| Who connects | Connection type | Usual port on Mosquitto |
| --- | --- | --- |
| weewx (the weewx-mqtt extension) | plain MQTT | 1883 |
| Your visitors' browsers (the skin) | websockets | 9001 |

Mixing these two up is the most common reason live updates don't work.

## In short

It works with **MQTT**, a small messaging system. weewx sends each new reading to an MQTT server (a "broker"), and visitors' browsers listen to the broker over **websockets** (a connection that stays open). You need:

1. **A broker.** Run your own or use a public one; see [MQTT brokers](brokers.md).
2. **The [weewx-mqtt extension](https://github.com/weewx/weewx/wiki/mqtt)**, so weewx sends its data to the broker. A sample configuration for it (change `server_url`, `topic` and `unit_system`; delete the `[[[tls]]]` part if your broker doesn't use SSL):

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

3. **The skin settings**, in `[[[Extras]]]`. The port here is the broker's *websockets* port, not its regular MQTT port:

```
        [[[Extras]]]
            mqtt_websockets_enabled = 1
            mqtt_websockets_host = "mqtt.hostname"
            mqtt_websockets_port = 8080
            mqtt_websockets_ssl = 1
            mqtt_websockets_topic = "the/topic/to/publish/to/loop"
```

When weewx saves a new archive record, the page also reloads its forecast, earthquake and chart data. Questions about the weewx-mqtt extension itself go to the [weewx-user group](https://groups.google.com/forum/#!forum/weewx-user); I didn't write it.

The step-by-step guide below does all of this with your own broker.

## Step by step: Mosquitto on the same computer as weewx

These steps are for Debian, Ubuntu and Raspberry Pi OS. Run the commands in a terminal on the computer that runs weewx.

**1. Install Mosquitto** and its test tools:

```
sudo apt install mosquitto mosquitto-clients
```

**2. Create two accounts on the broker.** One is for weewx, which sends data. The other is for your website. Visitors' browsers receive the website's password, so that account will only be allowed to read. Each command asks you to type a password:

```
sudo mosquitto_passwd -c /etc/mosquitto/passwd weewx
sudo mosquitto_passwd /etc/mosquitto/passwd website
```

The `-c` creates the file, so use it only on the first command. Using it again would erase the first account.

**3. Say what each account may do.** Open a new file `/etc/mosquitto/acl` in a text editor (for example `sudo nano /etc/mosquitto/acl`) and put this in it:

```
user weewx
topic readwrite weather/#

user website
topic read weather/#
```

`weather` is the topic, the name your readings are published under. You can choose another name; use the same one everywhere on this page.

**4. Let Mosquitto read both files:**

```
sudo chown mosquitto:mosquitto /etc/mosquitto/passwd /etc/mosquitto/acl
sudo chmod 600 /etc/mosquitto/passwd /etc/mosquitto/acl
```

**5. Turn on the two ports.** Open a new file `/etc/mosquitto/conf.d/belchertown.conf` in a text editor and put this in it:

```
per_listener_settings false
allow_anonymous false
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/acl

listener 1883
protocol mqtt

listener 9001
protocol websockets
```

`listener 1883` is the plain MQTT port that weewx uses. `listener 9001` with `protocol websockets` is the port for your visitors' browsers. `allow_anonymous false` means nobody can connect without one of the accounts from step 2.

**6. Restart Mosquitto** and check that it started:

```
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
```

The status should say `active (running)`. If it doesn't, `sudo journalctl -u mosquitto` shows why.

**7. Install the weewx-mqtt extension.** Follow the install steps in [its README](https://github.com/matthewwall/weewx-mqtt). It also needs the Python MQTT library, which its README covers.

**8. Point weewx-mqtt at your broker.** The installer adds an `[[MQTT]]` section under `[StdRESTful]` in your `weewx.conf`. Make it match the [sample above](#in-short), with these values:

- `server_url = mqtt://weewx:yourpassword@localhost:1883/`, using the `weewx` account's password from step 2. Note the port is 1883, the plain MQTT port.
- `topic = weather`
- `unit_system` set to the units your site shows: `US`, `METRIC` or `METRICWX`.
- Delete the `[[[tls]]]` part. weewx and the broker are on the same computer, so the connection never leaves it.

Keep `binding = archive, loop` and `aggregation = aggregate` as the sample shows them. With these, weewx-mqtt publishes every reading to the topic `weather/loop`, and that is what the skin listens to.

**9. Turn on live updates in the skin.** Open `weewx.conf` in a text editor, find the `[[Belchertown]]` section, and add these lines to its `[[[Extras]]]` part (create `[[[Extras]]]` if it isn't there). Replace `weather.example.com` with your site's address and `websitepassword` with the `website` account's password:

```
    [[Belchertown]]
        skin = Belchertown
        HTML_ROOT = /var/www/html/weewx/belchertown
        [[[Extras]]]
            mqtt_websockets_enabled = 1
            mqtt_websockets_host = "weather.example.com"
            mqtt_websockets_port = 9001
            mqtt_websockets_ssl = 0
            mqtt_websockets_topic = "weather/loop"
            mqtt_websockets_username = "website"
            mqtt_websockets_password = "websitepassword"
            disconnect_live_website_visitor = 1800000
```

Keep your own `HTML_ROOT` line; the one above is an example. Where `weewx.conf` is depends on how weewx was installed; see the table in [Install](install.md).

`mqtt_websockets_host` is the address your **visitors'** browsers use to reach the broker, so it must be your site's public name or address. `localhost` would only work in a browser on the weewx computer itself.

**10. Open the websockets port.** If the computer has a firewall, allow port 9001 (on Ubuntu with ufw: `sudo ufw allow 9001/tcp`). For visitors outside your home, your router also needs to forward port 9001 to this computer, the same way it forwards your web server's port.

**11. Restart weewx and rebuild the site:**

```
sudo systemctl restart weewx
weectl report run
```

**12. Open your home page.** Within a few seconds the status line near the top should change to "Connected to weather station live. Data received" with the time.

### Your site uses https

A page loaded over `https://` is only allowed to open secure websockets (`wss://`). Visitors' browsers will refuse a plain websockets connection and live updates will never connect. To fix it:

1. Give the 9001 listener your site's certificate. Add `certfile` and `keyfile` lines under `listener 9001` in `/etc/mosquitto/conf.d/belchertown.conf`, pointing at the same certificate files your web server uses. The [mosquitto.conf documentation](https://mosquitto.org/man/mosquitto-conf-5.html) explains these settings. The `mosquitto` user must be able to read those files.
2. Set `mqtt_websockets_ssl = 1` in `[[[Extras]]]`.
3. Make `mqtt_websockets_host` the same name that's on the certificate, for example `weather.example.com`, not an IP address.
4. Restart Mosquitto and weewx.

## How to tell it's working

**The dot.** Next to the "Last Updated" line at the top of the home page is a small colored dot:

- **Yellow**: connecting, or connected and waiting for the first reading.
- **Green**: connected, and readings are arriving.
- **Red**: the browser could not connect, or lost the connection.

The text next to it says the same thing in words.

**The browser console.** For more detail, turn on debug mode: set `belchertown_debug = 1` in `[[[Extras]]]` and restart weewx (turn it off again afterwards; it's noisy). Then open your browser's developer console (press F12 in most browsers, then pick the Console tab). [Debug mode](troubleshooting.md#debug-mode) has more on this. When everything works you'll see, in order:

```
MQTT: Connecting to MQTT Websockets: weather.example.com 9001 (SSL Disabled)
MQTT: MQTT Connected. Subscribing.
MQTT: {"dateTime": "...", "outTemp_F": "...", ...}
```

The last line repeats each time a reading arrives. Check the host, port and SSL setting in the first line against what you meant to set.

**From the weewx computer.** To see whether weewx is publishing at all, leaving the skin out of it, run this and wait a few seconds:

```
mosquitto_sub -h localhost -p 1883 -u website -P websitepassword -t 'weather/#' -v
```

Each reading prints as a line starting with `weather/loop`. Press Ctrl+C to stop. If nothing prints, the problem is between weewx and the broker, not in the skin.

## Visitors are disconnected after 30 minutes

That's on purpose. So that browser tabs left open don't stay connected forever, live updates stop after `disconnect_live_website_visitor` milliseconds (the default, 1800000, is 30 minutes). The page then says "Live updates have stopped" and shows a **Continue live updates** button that reconnects.

- Set `disconnect_live_website_visitor = 0` to never disconnect.
- Add `?stayconnected=true` to the end of the address to keep one browser connected, for example on a screen in your kitchen.
- The wall display (`?view=kiosk`) never disconnects. See [Wall display (kiosk view)](kiosk.md).

## A wall display on your home network

A display in your house can connect to the broker directly over your home network instead of going out to the internet and back. In the kiosk view (`?view=kiosk`) the skin uses these settings, if `mqtt_websockets_host_kiosk` is filled in:

```
        [[[Extras]]]
            mqtt_websockets_host_kiosk = "192.168.1.10"
            mqtt_websockets_port_kiosk = 9001
            mqtt_websockets_ssl_kiosk = 0
```

Use the weewx computer's address on your home network. If you leave the port or SSL setting empty, the kiosk view uses `mqtt_websockets_port` or `mqtt_websockets_ssl`. If `mqtt_websockets_host_kiosk` is empty, it uses all the normal settings. The topic, username and password are always the normal ones.

## Troubleshooting

**The dot turns red right away, and the console says "Cannot connect to MQTT broker".**

- **Wrong port.** `mqtt_websockets_port` must be the broker's websockets port (9001 in this guide), not 1883. The skin's default is 1883, so if you didn't set the port, that's the problem.
- **http and https mismatch.** If your site's address starts with `https://`, you need `mqtt_websockets_ssl = 1` and a broker listener with a certificate. See [Your site uses https](#your-site-uses-https). The console usually also shows a "mixed content" or "insecure WebSocket" error.
- **Firewall or router.** Port 9001 isn't open on the weewx computer, or isn't forwarded by your router. A test: it works from a browser at home using the local address, but not from a phone on cellular data.
- **Host.** `mqtt_websockets_host` is `localhost`, a home-network address like `192.168.1.10`, or a misspelled name. Visitors' browsers need an address they can reach from wherever they are.
- **Account.** The username or password is wrong, or `allow_anonymous false` is set and the skin has no username. `sudo journalctl -u mosquitto` shows refused logins.

**The dot stays yellow and the text says "Connected. Waiting for data."**

The browser reached the broker, but nothing arrives on the topic it's listening to.

- **Topic mismatch.** `mqtt_websockets_topic` must be the weewx-mqtt `topic` with `/loop` added: `topic = weather` in weewx-mqtt means `mqtt_websockets_topic = "weather/loop"` in the skin. Capital letters count.
- **weewx isn't publishing.** Run the `mosquitto_sub` test above. If nothing prints, check the weewx log (`sudo journalctl -u weewx`, or `/var/log/syslog`) for lines from weewx-mqtt, such as a refused login or wrong port in `server_url`.
- **The website account can't read the topic.** Check the `acl` file from step 3 uses the same topic name.

**The dot is green but some numbers are wrong or don't change.**

- **`unit_system` in the weewx-mqtt section doesn't match your site.** weewx-mqtt names each value with its unit, for example `outTemp_F` or `outTemp_C`, and the skin expects the units your site is set to. If your site shows metric and weewx-mqtt publishes `US`, temperatures arrive in Fahrenheit under a °C label. Set `unit_system` in `[[MQTT]]` to the same units as your site and restart weewx.
- **An observation isn't in the live data.** The list next to the radar (`station_observations`) only updates live for values your station sends with each reading. Anything else updates when the page reloads.

**Live updates work, but the charts and forecast never refresh.**

The skin refreshes charts, forecast and daily highs and lows when weewx saves an archive record. That needs `binding = archive, loop` in the weewx-mqtt section, as the [sample](#in-short) shows. With only `loop`, the page never hears about archive records.

**Still stuck?** Ask in the skin's [Questions and help](https://github.com/poblabs/weewx-belchertown/discussions/categories/q-a) discussions. Include the lines starting with `MQTT:` from the browser console and your `[[MQTT]]` and `[[[Extras]]]` settings, with passwords removed.
