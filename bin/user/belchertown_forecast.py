"""Forecast providers for the Belchertown skin.

Each provider is downloaded and converted to one format, written to json/forecast.json and
drawn by belchertown-forecast.js. Values are already in the units forecast_units asks for;
wind is also given in knots for stations that show knots or Beaufort.

    {"belchertown_forecast": 3, "provider": "openmeteo", "timestamp": 1791306900,
     "units": {"temp": "F", "wind": "mph", "snow": "in", "visibility": "miles"},
     "current": {"icon": "clear-day", "text": "Clear", "visibility": 10.0, "cloud_cover": 0} or null,
     "aqi": {"value": 34, "category": "good", "place": ""} or null,
     "daily" / "three_hourly" / "hourly": [{"time", "icon", "text", "temp_avg", "temp_min",
         "temp_max", "dewpoint", "humidity", "pop", "wind", "gust", "wind_kts", "gust_kts", "snow"}],
     "alerts": [{"title", "body", "type", "expires"}]}
"""
import json
import os
import time
from urllib.request import Request, urlopen

FORMAT = 3
USER_AGENT = "weewx-belchertown (https://github.com/poblabs/weewx-belchertown)"

# forecast_units -> display units, the same choices the skin has always made
UNITS = {
    "us": {"temp": "F", "wind": "mph", "snow": "in", "visibility": "miles"},
    "uk2": {"temp": "C", "wind": "mph", "snow": "cm", "visibility": "miles"},
    "ca": {"temp": "C", "wind": "km/h", "snow": "cm", "visibility": "km"},
    "si": {"temp": "C", "wind": "m/s", "snow": "cm", "visibility": "km"},
}


def provider_for(extras):
    """aeris/xweather, openmeteo, or auto: Xweather when its keys are set, else Open-Meteo."""
    provider = extras.get("forecast_provider", "auto").lower()
    if provider in ("aeris", "xweather"):
        return "xweather"
    if provider == "auto":
        return "xweather" if extras.get("forecast_api_id") else "openmeteo"
    return provider


def is_stale(path, stale_seconds):
    """Old enough to refresh, or in the first 5 minutes of the hour so the hourly row lines up."""
    if not os.path.isfile(path):
        return True
    try:
        with open(path) as f:
            if json.load(f).get("belchertown_forecast") != FORMAT:
                return True
    except (ValueError, OSError):
        return True
    age = time.time() - os.path.getmtime(path)
    return age > int(stale_seconds) or (time.strftime("%M") < "05" and age > 300)


def get_json(url):
    with urlopen(Request(url, None, {"User-Agent": USER_AGENT}), timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def coded_text(labels, coverage, intensity, weather, with_coverage):
    """Condition text from the forecast_*_code labels, e.g. "" + "L" + "R" -> "Light Rain"."""
    if weather in ("CL", "FW", "SC", "BK", "OV"):
        return labels["forecast_cloud_code_" + weather]
    text = ""
    if coverage and with_coverage:
        text += labels["forecast_coverage_code_" + coverage] + " "
    if intensity:
        text += labels["forecast_intensity_code_" + intensity] + " "
    return text + labels["forecast_weather_code_" + weather]


def aqi_category(value):
    """US EPA category for an AQI value."""
    for limit, category in ((50, "good"), (100, "moderate"), (150, "usg"), (200, "unhealthy"), (300, "very unhealthy")):
        if value <= limit:
            return category
    return "hazardous"


def kts(kph):
    return None if kph is None else kph / 1.852


# ---------------------------------------------------------------------------- Xweather

def xweather_download(extras, lat, lon):
    if "forecast_dev_file" in extras:
        # Hidden option: a pre-downloaded raw Xweather file instead of API calls
        return get_json(extras["forecast_dev_file"])
    base = "https://data.api.xweather.com/"
    auth = "client_id=%s&client_secret=%s" % (extras["forecast_api_id"], extras["forecast_api_secret"])
    metar = "&filter=metar" if extras.get("forecast_aeris_use_metar") == "1" else ""
    raw = {
        "timestamp": int(time.time()),
        "current": [get_json("%sobservations/%s,%s?format=json&filter=allstations%s&limit=1&%s" % (base, lat, lon, metar, auth))],
        "forecast_24hr": [get_json("%sforecasts/%s,%s?format=json&filter=day&limit=7&%s" % (base, lat, lon, auth))],
        "forecast_3hr": [get_json("%sforecasts/%s,%s?format=json&filter=3hr&limit=8&%s" % (base, lat, lon, auth))],
        "forecast_1hr": [get_json("%sforecasts/%s,%s?format=json&filter=1hr&limit=16&%s" % (base, lat, lon, auth))],
        "aqi": [get_json("%sairquality/closest?p=%s,%s&format=json&radius=50mi&limit=1&%s" % (base, lat, lon, auth))],
    }
    if extras.get("forecast_alert_enabled") == "1":
        raw["alerts"] = [get_json("%salerts/%s,%s?format=json&limit=%s&lang=%s&%s" % (
            base, lat, lon, extras.get("forecast_alert_limit") or 1, extras.get("forecast_lang", "en").lower(), auth))]
    return raw


def xweather_convert(raw, extras, labels, icons):
    units = UNITS.get(extras.get("forecast_units", "us").lower(), UNITS["us"])
    metric_temp = units["temp"] == "C"

    def icon(name):
        return icons.get(name.split(".")[0], "unknown")

    def text(code, with_coverage):
        coverage, intensity, weather = code.split(":")
        return coded_text(labels, coverage, intensity, weather, with_coverage)

    def wind(period, key):
        if units["wind"] == "km/h":
            return period[key + "KPH"]
        if units["wind"] == "m/s":
            return None if period[key + "KPH"] is None else period[key + "KPH"] / 3.6
        return period[key + "MPH"]

    def periods(name):
        out = []
        for p in raw[name][0]["response"][0]["periods"]:
            out.append({
                "time": p["timestamp"],
                "icon": icon(p["icon"]),
                "text": text(p["weatherPrimaryCoded"], False),
                "temp_avg": p["avgTempC" if metric_temp else "avgTempF"],
                "temp_min": p["minTempC" if metric_temp else "minTempF"],
                "temp_max": p["maxTempC" if metric_temp else "maxTempF"],
                "dewpoint": p["dewpointC" if metric_temp else "dewpointF"],
                "humidity": p["humidity"],
                "pop": p["pop"] or 0,
                "wind": wind(p, "windSpeed"),
                "gust": wind(p, "windGust"),
                "wind_kts": p["windSpeedKTS"],
                "gust_kts": p["windGustKTS"],
                "snow": p["snowCM" if units["snow"] == "cm" else "snowIN"] or 0,
            })
        return out

    current = None
    try:
        ob = raw["current"][0]["response"]["ob"]
        current = {"icon": "", "text": "", "visibility": None, "cloud_cover": ob.get("sky")}
        if extras.get("forecast_aeris_use_metar") == "1":
            current["icon"] = icon(ob["icon"])
            current["text"] = text(ob["weatherPrimaryCoded"], True)
            current["visibility"] = ob["visibilityKM" if units["visibility"] == "km" else "visibilityMI"]
    except (KeyError, IndexError, TypeError, AttributeError):
        pass

    aqi = None
    try:
        a = raw["aqi"][0]
        if a.get("success") and not a.get("error"):
            period = a["response"][0]["periods"][0]
            aqi = {"value": period["aqi"], "category": period["category"], "place": a["response"][0]["place"]["name"]}
        elif a.get("success") and a["error"]["code"] == "warn_no_data":
            aqi = {"value": "No Data", "category": "", "place": ""}
    except (KeyError, IndexError, TypeError):
        pass

    alerts = []
    for a in (raw.get("alerts") or [{}])[0].get("response") or []:
        alert_type = a["details"]["type"]
        key = "forecast_alert_code_" + ("SPS" if alert_type == "SP.S" else alert_type.replace(".", "_"))
        alerts.append({
            "title": labels[key] if key in labels else a["details"]["name"],
            "body": a["details"]["body"],
            "type": alert_type,
            "expires": a["timestamps"]["expires"],
        })

    return {
        "belchertown_forecast": FORMAT, "provider": "xweather", "timestamp": raw.get("timestamp", int(time.time())),
        "units": units, "current": current, "aqi": aqi,
        "daily": periods("forecast_24hr"), "three_hourly": periods("forecast_3hr"), "hourly": periods("forecast_1hr"),
        "alerts": alerts,
    }


# ---------------------------------------------------------------------------- Open-Meteo

# WMO weather code -> (day icon, night icon, coverage, intensity, Xweather-style weather code).
# The codes reuse the forecast_*_code labels, so existing translations cover Open-Meteo too.
WMO = {
    0: ("clear-day", "clear-night", "", "", "CL"),
    1: ("mostly-clear-day", "mostly-clear-night", "", "", "FW"),
    2: ("partly-cloudy-day", "partly-cloudy-night", "", "", "SC"),
    3: ("cloudy", "cloudy", "", "", "OV"),
    45: ("fog", "fog", "", "", "F"),
    48: ("fog", "fog", "", "", "ZF"),
    51: ("drizzle", "drizzle", "", "L", "L"),
    53: ("drizzle", "drizzle", "", "", "L"),
    55: ("drizzle", "drizzle", "", "H", "L"),
    56: ("sleet", "sleet", "", "L", "ZL"),
    57: ("sleet", "sleet", "", "H", "ZL"),
    61: ("rain", "rain", "", "L", "R"),
    63: ("rain", "rain", "", "", "R"),
    65: ("rain", "rain", "", "H", "R"),
    66: ("sleet", "sleet", "", "L", "ZR"),
    67: ("sleet", "sleet", "", "H", "ZR"),
    71: ("snow", "snow", "", "L", "S"),
    73: ("snow", "snow", "", "", "S"),
    75: ("snow", "snow", "", "H", "S"),
    77: ("snow", "snow", "", "", "S"),
    80: ("rain", "rain", "", "L", "RW"),
    81: ("rain", "rain", "", "", "RW"),
    82: ("rain", "rain", "", "VH", "RW"),
    85: ("snow", "snow", "", "L", "SW"),
    86: ("snow", "snow", "", "H", "SW"),
    95: ("thunderstorm", "thunderstorm", "", "", "T"),
    96: ("thunderstorm", "thunderstorm", "", "", "T"),
    99: ("thunderstorm", "thunderstorm", "", "H", "T"),
}


def openmeteo_download(extras, lat, lon):
    hourly = "temperature_2m,dew_point_2m,relative_humidity_2m,precipitation_probability,weather_code,wind_speed_10m,wind_gusts_10m,snowfall,is_day"
    daily = ("weather_code,temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_probability_max,"
             "wind_speed_10m_max,wind_gusts_10m_max,snowfall_sum,relative_humidity_2m_mean,dew_point_2m_mean")
    raw = {
        "timestamp": int(time.time()),
        "forecast": get_json(
            "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&timezone=auto&timeformat=unixtime"
            "&forecast_days=7&wind_speed_unit=kmh&current=weather_code,is_day,cloud_cover,visibility&hourly=%s&daily=%s"
            % (lat, lon, hourly, daily)),
    }
    if extras.get("aqi_enabled") == "1":
        raw["aqi"] = get_json(
            "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=%s&longitude=%s&current=us_aqi&timeformat=unixtime"
            % (lat, lon))
    return raw


def openmeteo_convert(raw, extras, labels):
    units = UNITS.get(extras.get("forecast_units", "us").lower(), UNITS["us"])
    f = raw["forecast"]

    def temp(c):
        return None if c is None else (c * 9 / 5 + 32 if units["temp"] == "F" else c)

    def wind(kph):
        if kph is None:
            return None
        return {"mph": kph / 1.609344, "km/h": kph, "m/s": kph / 3.6}[units["wind"]]

    def snow(cm):
        return 0 if not cm else (cm if units["snow"] == "cm" else cm / 2.54)

    def look(code, is_day=1):
        day_icon, night_icon, coverage, intensity, weather = WMO.get(code, ("unknown", "unknown", "", "", "CL"))
        return (day_icon if is_day else night_icon), coded_text(labels, coverage, intensity, weather, True)

    h = f["hourly"]
    start = next((i for i, t in enumerate(h["time"]) if t + 3600 > time.time()), 0)

    def hour_period(i, span):
        window = range(i, min(i + span, len(h["time"])))
        icon, text = look(h["weather_code"][i], h["is_day"][i])
        temps = [h["temperature_2m"][j] for j in window if h["temperature_2m"][j] is not None]
        return {
            "time": h["time"][i], "icon": icon, "text": text,
            "temp_avg": temp(h["temperature_2m"][i]),
            "temp_min": temp(min(temps)) if temps else None,
            "temp_max": temp(max(temps)) if temps else None,
            "dewpoint": temp(h["dew_point_2m"][i]),
            "humidity": h["relative_humidity_2m"][i],
            "pop": max((h["precipitation_probability"][j] or 0) for j in window),
            "wind": wind(h["wind_speed_10m"][i]),
            "gust": wind(max((h["wind_gusts_10m"][j] or 0) for j in window)),
            "wind_kts": kts(h["wind_speed_10m"][i]),
            "gust_kts": kts(max((h["wind_gusts_10m"][j] or 0) for j in window)),
            "snow": snow(sum((h["snowfall"][j] or 0) for j in window)),
        }

    d = f["daily"]
    daily = []
    for i in range(len(d["time"])):
        icon, text = look(d["weather_code"][i])
        daily.append({
            "time": d["time"][i], "icon": icon, "text": text,
            "temp_avg": temp(d["temperature_2m_mean"][i]),
            "temp_min": temp(d["temperature_2m_min"][i]),
            "temp_max": temp(d["temperature_2m_max"][i]),
            "dewpoint": temp(d["dew_point_2m_mean"][i]),
            "humidity": d["relative_humidity_2m_mean"][i],
            "pop": d["precipitation_probability_max"][i] or 0,
            "wind": wind(d["wind_speed_10m_max"][i]),
            "gust": wind(d["wind_gusts_10m_max"][i]),
            "wind_kts": kts(d["wind_speed_10m_max"][i]),
            "gust_kts": kts(d["wind_gusts_10m_max"][i]),
            "snow": snow(d["snowfall_sum"][i]),
        })

    c = f.get("current") or {}
    current = None
    if "weather_code" in c:
        icon, text = look(c["weather_code"], c.get("is_day", 1))
        meters = c.get("visibility")
        visibility = None if meters is None else round(meters / 1000 if units["visibility"] == "km" else meters / 1609.344, 1)
        current = {"icon": icon, "text": text, "visibility": visibility, "cloud_cover": c.get("cloud_cover")}

    aqi = None
    value = ((raw.get("aqi") or {}).get("current") or {}).get("us_aqi")
    if value is not None:
        aqi = {"value": value, "category": aqi_category(value), "place": ""}

    return {
        "belchertown_forecast": FORMAT, "provider": "openmeteo", "timestamp": raw["timestamp"],
        "units": units, "current": current, "aqi": aqi,
        "daily": daily,
        "three_hourly": [hour_period(i, 3) for i in range(start, min(start + 24, len(h["time"])), 3)],
        "hourly": [hour_period(i, 1) for i in range(start, min(start + 16, len(h["time"])))],
        "alerts": [],
    }


# ---------------------------------------------------------------------------- entry points

def update(path, extras, lat, lon, labels, icon_list_path):
    """Refresh forecast.json if it's stale; return the forecast either way."""
    provider = provider_for(extras)
    if is_stale(path, extras.get("forecast_stale", 3540)):
        if provider == "xweather":
            with open(icon_list_path) as f:
                icons = json.load(f)
            forecast = xweather_convert(xweather_download(extras, lat, lon), extras, labels, icons)
        elif provider == "openmeteo":
            forecast = openmeteo_convert(openmeteo_download(extras, lat, lon), extras, labels)
        else:
            raise ValueError("Unknown forecast_provider %r" % provider)
        with open(path, "w") as f:
            json.dump(forecast, f)
        return forecast, True
    with open(path) as f:
        return json.load(f), False
