# Public MQTT Brokers

[Live updates](live-updates.md) need an MQTT broker: a program that receives readings from weewx and passes them on to your visitors' browsers. A public broker is one that someone else runs on the internet and lets anyone use, for free and without signing up.

A public broker is a good way to:

- try live updates before setting up a broker of your own, or
- see them working when you don't have a server you can run a broker on.

## Read this first: your data is public

- **Anyone can read it.** Everything sent to a public broker can be read by anyone who knows or guesses your topic, and there are tools that list every topic in use.
- **There is no password.** You can't keep others out, and anyone can also publish to your topic. Someone could put made-up numbers on your home page.
- **No promises.** A public broker can be slow, busy, or down, and its owners can change or close it at any time. When it's down, your live updates stop.

Weather readings aren't usually secret, but don't send anything to a public broker that you wouldn't put on your website. Use them for trying things out, not as your long-term setup.

## Brokers that work

These public brokers accept plain MQTT from weewx and websockets from browsers. Use the **websockets** port in the skin settings.

| Broker | Websockets port (ws) | Secure websockets port (wss) |
| --- | --- | --- |
| `test.mosquitto.org` | 8080 | 8081 |
| `broker.hivemq.com` | 8000 | 8884 |
| `broker.emqx.io` | 8083 | 8084 |

If your site's address starts with `https://`, browsers only allow secure websockets, so use a wss port and `mqtt_websockets_ssl = 1`. The wss ports are in the table. A secure port also works for an `http://` site.

Each broker's own website lists its current ports: [test.mosquitto.org](https://test.mosquitto.org), [HiveMQ](https://www.hivemq.com/mqtt/public-mqtt-broker/), [EMQX](https://www.emqx.com/en/mqtt/public-mqtt5-broker). Check there if one stops working.

## Example: test.mosquitto.org

**1. Pick a topic nobody else will use.** Everyone on the broker shares the same topic names, so `weather` is certainly taken. Make one up with your town and some random digits, for example `belchertown/yourtown-58213`. The examples below use that; replace it with yours everywhere.

**2. Install the weewx-mqtt extension** by following the install steps in [its README](https://github.com/matthewwall/weewx-mqtt).

**3. Point weewx-mqtt at the broker.** Open your `weewx.conf` in a text editor. Where it is depends on how weewx was installed; see the table in [Install](install.md). Find the `[[MQTT]]` section under `[StdRESTful]` that the installer added and make it look like this, with your topic and units:

```
    [[MQTT]]
        server_url = mqtt://test.mosquitto.org:1883/
        topic = belchertown/yourtown-58213
        unit_system = US
        binding = archive, loop
        aggregation = aggregate
```

This is the [sample from Live updates](live-updates.md#in-short) with the broker filled in. There's no username or password in `server_url`, because the broker doesn't use them, and no `[[[tls]]]` part. Port 1883 is the broker's plain MQTT port, which is what weewx uses. Set `unit_system` to the units your site shows: `US`, `METRIC` or `METRICWX`.

**4. Turn on live updates in the skin.** In the same file, find the `[[Belchertown]]` section and add these lines to its `[[[Extras]]]` part (create `[[[Extras]]]` if it isn't there). The topic is the one from step 3 with `/loop` added:

```
        [[[Extras]]]
            mqtt_websockets_enabled = 1
            mqtt_websockets_host = "test.mosquitto.org"
            mqtt_websockets_port = 8081
            mqtt_websockets_ssl = 1
            mqtt_websockets_topic = "belchertown/yourtown-58213/loop"
```

Leave `mqtt_websockets_username` and `mqtt_websockets_password` out.

**5. Restart weewx and rebuild the site:**

```
sudo systemctl restart weewx
weectl report run
```

**6. Open your home page.** Within a few seconds the dot next to "Last Updated" should turn green. If it doesn't, see [how to tell it's working](live-updates.md#how-to-tell-its-working) and [troubleshooting](live-updates.md#troubleshooting) on the live updates page.

## When you're ready: your own broker

Once you know you want live updates, move to a broker of your own with a password. Your data is then only readable by your website, nobody else can publish to your topic, and it stays up as long as your own computer does. [Live Updates with MQTT](live-updates.md) walks through setting up Mosquitto on the same computer as weewx. Moving over only means changing `server_url` and `topic` in `[[MQTT]]` and the `mqtt_websockets_*` settings in `[[[Extras]]]`.


## Run your own

**Run your own.** [These are my instructions for setting up a broker](https://web.archive.org/web/20240412180952/https://obrienlabs.net/how-to-setup-your-own-mqtt-broker). A small DigitalOcean server is a quick and easy place to run one, and signing up with this **referral** link gets you free credit and helps pay for my server:

[![DigitalOcean Referral Badge](https://web-platforms.sfo2.cdn.digitaloceanspaces.com/WWW/Badge%201.svg)](https://www.digitalocean.com/?refcode=f79cac0e591d&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge)
