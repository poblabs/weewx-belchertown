# Forecasts

**The forecast works out of the box.** With no setup at all, the current conditions, the 7-day, 3-hour and 1-hour forecasts and the air quality come from [Open-Meteo](https://open-meteo.com), which is free, needs no account and covers the whole world.

**Weather alerts** (watches and warnings) also work with no setup **in the US**: they come from the National Weather Service. Outside the US there are no alerts unless you use Xweather.

**Other forecast sources** are optional:

* **National Weather Service** (US only, free, no key): set `forecast_provider = nws` to use the NWS forecast itself, the one on weather.gov.
* **[Xweather](https://www.xweather.com)** (formerly AerisWeather): needs a free key, and brings its own alerts, including outside the US where Xweather covers them. There are two ways to get a key:
  * **Xweather's free tier** (US and Canada): the first 15,000 calls each month are free, with no credit card. The skin uses roughly 7,000 a month with everything turned on. [Sign up here](https://www.xweather.com/pricing/weather-api-pay-as-you-go).
  * **The PWSweather contributor plan** (anywhere): free if you send your station's data to [PWSweather](https://www.pwsweather.com/register), which weewx can do for you with the `[[PWSweather]]` section under `[StdRESTful]` in `weewx.conf`. [Sign up here](https://signup.xweather.com/pws-contributor) with your PWSweather login.

  Then copy your client ID and secret from your Xweather account into `[[[Extras]]]`. As soon as a key is there, the skin uses Xweather instead of Open-Meteo:

```
        [[[Extras]]]
            forecast_api_id = "your_id"
            forecast_api_secret = "your_secret_key"
```

The skin downloads a new forecast about once an hour. `forecast_provider` chooses the source: `auto` (the default: Xweather when a key is set, otherwise Open-Meteo), `openmeteo`, `nws` or `aeris` (Xweather). `forecast_alert_provider` does the same for alerts: `auto` (Xweather's alerts with Xweather, otherwise the National Weather Service), `nws`, `aeris` or `none`. Air quality comes from Xweather with Xweather, and from Open-Meteo otherwise. To turn the forecast off, set `forecast_enabled = 0`; to turn only the alerts off, set `forecast_alert_enabled = 0`. More settings are under "Forecast options" in [All skin options](options.md).

??? note "For developers: the forecast.json file"

    The skin writes the forecast to `json/forecast.json` in the same format whatever the source, so other programs can read it. Values are already in the units `forecast_units` asks for (listed under `units`); wind is also given in knots. The format is described at the top of `bin/user/belchertown_forecast.py`, and `belchertown_forecast` is its version number (3).

## Forecast units

The forecast's units are set separately with `forecast_units`:

* `us`: US units (the default)
* `si`: metric. Temperature in °C, wind in meters per second, visibility in kilometers
* `ca`: same as `si`, but wind in kilometers per hour
* `uk2`: same as `si`, but wind in miles per hour and visibility in miles

## Forecast in your language

The forecast arrives as weather codes, and each code has a label, so the forecast can be translated like any other text. Look for the `forecast_` labels in `skin.conf` and copy the ones you want to change into `weewx.conf` ([how](customize.md#change-the-site-title-and-other-text)).
