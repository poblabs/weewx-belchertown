"""Forecast providers for the Belchertown skin.

Each provider is downloaded and converted to one format, written to json/forecast.json and
drawn by belchertown-forecast.js. Values are already in the units forecast_units asks for;
wind is also given in knots for stations that show knots or Beaufort.

    {"belchertown_forecast": 3, "provider": "openmeteo", "timestamp": 1791306900,
     "timezone": "America/New_York", "utc_offset": -14400,
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
    if provider in ("aeris", "xweather") or "forecast_dev_file" in extras:
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
    with urlopen(Request(url, None, {"User-Agent": USER_AGENT}), timeout=15) as response:
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
    for name in ("current", "forecast_24hr", "forecast_3hr", "forecast_1hr"):
        reply = (raw.get(name) or [{}])[0]
        if reply.get("success") is False or not reply.get("response"):
            error = reply.get("error") or {}
            raise RuntimeError("Xweather %s: %s %s" % (name, error.get("code", "no data"), error.get("description", "")))
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
        "timezone": ((raw["forecast_24hr"][0].get("response") or [{}])[0].get("profile") or {}).get("tz"),
        "units": units, "current": current, "aqi": aqi,
        "daily": periods("forecast_24hr"), "three_hourly": periods("forecast_3hr"), "hourly": periods("forecast_1hr"),
        "alerts": alerts,
    }


# ---------------------------------------------------------------------------- Open-Meteo weather codes

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


# ---------------------------------------------------------------------------- metric providers
# Open-Meteo and NWS both give hourly metric data; these turn it into display periods.

class Display:
    """Metric values (C, km/h, cm, m) in the forecast_units display units."""

    def __init__(self, units):
        self.units = units

    def temp(self, c):
        return None if c is None else (c * 9 / 5 + 32 if self.units["temp"] == "F" else c)

    def wind(self, kph):
        if kph is None:
            return None
        return {"mph": kph / 1.609344, "km/h": kph, "m/s": kph / 3.6}[self.units["wind"]]

    def snow(self, cm):
        return 0 if not cm else (cm if self.units["snow"] == "cm" else cm / 2.54)

    def visibility(self, meters):
        if meters is None:
            return None
        return round(meters / 1000 if self.units["visibility"] == "km" else meters / 1609.344, 1)


def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def period(show, when, icon, text, temps, dewpoints, humidities, pops, winds, gusts, snows, avg=None):
    """One forecast period from lists of hourly metric values (or single daily values)."""
    temps = [t for t in temps if t is not None]
    return {
        "time": when, "icon": icon, "text": text,
        "temp_avg": show.temp(avg if avg is not None else (temps[0] if temps else None)),
        "temp_min": show.temp(min(temps)) if temps else None,
        "temp_max": show.temp(max(temps)) if temps else None,
        "dewpoint": show.temp(dewpoints[0] if dewpoints else None),
        "humidity": humidities[0] if humidities else None,
        "pop": max([p or 0 for p in pops] or [0]),
        "wind": show.wind(winds[0] if winds else None),
        "gust": show.wind(max([g or 0 for g in gusts] or [0])),
        "wind_kts": kts(winds[0] if winds else None),
        "gust_kts": kts(max([g or 0 for g in gusts] or [0])),
        "snow": show.snow(sum(s or 0 for s in snows)),
    }


def hour_periods(show, h, start, span, count):
    """Periods of `span` hours from an hourly series: dict of equal-length lists."""
    out = []
    for i in range(start, min(start + span * count, len(h["time"])), span):
        w = slice(i, min(i + span, len(h["time"])))
        out.append(period(show, h["time"][i], h["icon"][i], h["text"][i], h["temp"][w], h["dewpoint"][i:i + 1],
                          h["humidity"][i:i + 1], h["pop"][w], h["wind"][i:i + 1], h["gust"][w], h["snow"][w]))
    return out


def first_hour(times):
    now = time.time()
    return next((i for i, t in enumerate(times) if t + 3600 > now), 0)


def openmeteo_aqi(lat, lon):
    data = get_json("https://air-quality-api.open-meteo.com/v1/air-quality?latitude=%s&longitude=%s&current=us_aqi&timeformat=unixtime"
                    % (lat, lon))
    value = (data.get("current") or {}).get("us_aqi")
    return None if value is None else {"value": value, "category": aqi_category(value), "place": ""}


# ---------------------------------------------------------------------------- Open-Meteo

def openmeteo_download(extras, lat, lon):
    hourly = "temperature_2m,dew_point_2m,relative_humidity_2m,precipitation_probability,weather_code,wind_speed_10m,wind_gusts_10m,snowfall,is_day"
    daily = ("weather_code,temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_probability_max,"
             "wind_speed_10m_max,wind_gusts_10m_max,snowfall_sum,relative_humidity_2m_mean,dew_point_2m_mean")
    return {
        "timestamp": int(time.time()),
        "forecast": get_json(
            "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&timezone=auto&timeformat=unixtime"
            "&forecast_days=7&wind_speed_unit=kmh&current=weather_code,is_day,cloud_cover,visibility&hourly=%s&daily=%s"
            % (lat, lon, hourly, daily)),
    }


def openmeteo_convert(raw, extras, labels):
    units = UNITS.get(extras.get("forecast_units", "us").lower(), UNITS["us"])
    show = Display(units)
    f = raw["forecast"]

    def look(code, is_day=1):
        day_icon, night_icon, coverage, intensity, weather = WMO.get(code, ("unknown", "unknown", "", "", "CL"))
        return (day_icon if is_day else night_icon), coded_text(labels, coverage, intensity, weather, True)

    h = f["hourly"]
    looks = [look(c, d) for c, d in zip(h["weather_code"], h["is_day"])]
    series = {
        "time": h["time"], "icon": [l[0] for l in looks], "text": [l[1] for l in looks],
        "temp": h["temperature_2m"], "dewpoint": h["dew_point_2m"], "humidity": h["relative_humidity_2m"],
        "pop": h["precipitation_probability"], "wind": h["wind_speed_10m"], "gust": h["wind_gusts_10m"], "snow": h["snowfall"],
    }
    start = first_hour(h["time"])

    d = f["daily"]
    daily = []
    for i in range(len(d["time"])):
        icon, text = look(d["weather_code"][i])
        daily.append(period(show, d["time"][i], icon, text,
                            [d["temperature_2m_min"][i], d["temperature_2m_max"][i]], [d["dew_point_2m_mean"][i]],
                            [d["relative_humidity_2m_mean"][i]], [d["precipitation_probability_max"][i]],
                            [d["wind_speed_10m_max"][i]], [d["wind_gusts_10m_max"][i]], [d["snowfall_sum"][i]],
                            avg=d["temperature_2m_mean"][i]))

    c = f.get("current") or {}
    current = None
    if "weather_code" in c:
        icon, text = look(c["weather_code"], c.get("is_day", 1))
        current = {"icon": icon, "text": text, "visibility": show.visibility(c.get("visibility")), "cloud_cover": c.get("cloud_cover")}

    return {
        "belchertown_forecast": FORMAT, "provider": "openmeteo", "timestamp": raw["timestamp"], "timezone": f.get("timezone"),
        "units": units, "current": current, "aqi": None,
        "daily": daily,
        "three_hourly": hour_periods(show, series, start, 3, 8),
        "hourly": hour_periods(show, series, start, 1, 16),
        "alerts": [],
    }


# ---------------------------------------------------------------------------- NWS (US only, no key)

# NWS icon codes (https://api.weather.gov/icons) -> skin icon; "day"/"night" picks the variant
NWS_ICONS = {
    "skc": "clear", "few": "mostly-clear", "sct": "partly-cloudy", "bkn": "mostly-cloudy", "ovc": "cloudy",
    "wind_skc": "wind", "wind_few": "wind", "wind_sct": "wind", "wind_bkn": "wind", "wind_ovc": "wind",
    "snow": "snow", "blizzard": "snow", "rain_snow": "sleet", "rain_sleet": "sleet", "snow_sleet": "sleet",
    "sleet": "sleet", "fzra": "sleet", "rain_fzra": "sleet", "snow_fzra": "sleet",
    "rain": "rain", "rain_showers": "rain", "rain_showers_hi": "rain",
    "tsra": "thunderstorm", "tsra_sct": "thunderstorm", "tsra_hi": "thunderstorm",
    "tornado": "thunderstorm", "hurricane": "thunderstorm", "tropical_storm": "thunderstorm",
    "dust": "fog", "smoke": "fog", "haze": "fog", "fog": "fog", "hot": "clear", "cold": "clear",
}
DAY_NIGHT = ("clear", "mostly-clear", "partly-cloudy", "mostly-cloudy")
NWS_CLOUDS = {"SKC": 0, "CLR": 0, "FEW": 25, "SCT": 50, "BKN": 75, "OVC": 100, "VV": 100}


def nws_icon(url):
    """https://api.weather.gov/icons/land/night/rain,40/tsra?size=small -> "rain"."""
    try:
        parts = url.split("?")[0].split("/")
        when, code = parts[-2], parts[-1]
        if when not in ("day", "night"):
            when, code = parts[-3], parts[-2]
        icon = NWS_ICONS.get(code.split(",")[0], "unknown")
        return icon + "-" + when if icon in DAY_NIGHT else icon
    except (AttributeError, IndexError):
        return "unknown"


def iso_epoch(text):
    from datetime import datetime
    return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp())


def nws_windows(layer):
    """Gridpoint values as (start epoch, hours, value)."""
    import re
    out = []
    for v in layer.get("values", []):
        start, _, duration = v["validTime"].partition("/")
        m = re.match(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?)?", duration)
        out.append((iso_epoch(start), max(1, int(m.group(1) or 0) * 24 + int(m.group(2) or 0)), v["value"]))
    return out


def nws_series(layer):
    """Gridpoint values like {"validTime": "2026-10-06T12:00:00+00:00/PT6H", "value": 3} -> {hour epoch: value}.
    Rates are repeated over their hours; amounts (mm) go on the first hour."""
    out = {}
    amount = layer.get("uom", "").endswith(":mm")
    for start, hours, value in nws_windows(layer):
        for k in range(1 if amount else hours):
            out[start + 3600 * k] = value
    return out


def nws_download(extras, lat, lon):
    point = get_json("https://api.weather.gov/points/%s,%s" % (lat, lon))["properties"]
    raw = {
        "timestamp": int(time.time()),
        "forecast": get_json(point["forecast"]),
        "hourly": get_json(point["forecastHourly"]),
        "grid": get_json(point["forecastGridData"]),
        "timezone": point.get("timeZone"),
    }
    # Some stations don't report a weather description; use the nearest one that does
    raw["observation"] = None
    try:
        for station in get_json(point["observationStations"])["features"][:3]:
            observation = get_json(station["id"] + "/observations/latest")
            if (observation.get("properties") or {}).get("textDescription"):
                raw["observation"] = observation
                break
    except Exception:
        pass
    return raw


def nws_convert(raw, extras, labels):
    units = UNITS.get(extras.get("forecast_units", "us").lower(), UNITS["us"])
    show = Display(units)
    grid = raw["grid"]["properties"]
    layers = {name: nws_series(grid.get(name, {})) for name in (
        "temperature", "dewpoint", "relativeHumidity", "probabilityOfPrecipitation", "windSpeed", "windGust",
        "snowfallAmount")}

    hourly_periods = raw["hourly"]["properties"]["periods"]
    times = [iso_epoch(p["startTime"]) for p in hourly_periods]
    series = {
        "time": times,
        "icon": [nws_icon(p["icon"]) for p in hourly_periods],
        "text": [p["shortForecast"] for p in hourly_periods],
        "temp": [layers["temperature"].get(t) for t in times],
        "dewpoint": [layers["dewpoint"].get(t) for t in times],
        "humidity": [layers["relativeHumidity"].get(t) for t in times],
        "pop": [layers["probabilityOfPrecipitation"].get(t) for t in times],
        "wind": [layers["windSpeed"].get(t) for t in times],
        "gust": [layers["windGust"].get(t) for t in times],
        "snow": [(layers["snowfallAmount"].get(t) or 0) / 10 for t in times],
    }
    start = first_hour(times)

    # Days, highs and lows follow NWS's own 12-hour forecast ("Wednesday 64 / Wednesday Night 49", in F),
    # so the page matches weather.gov; the rest comes from the hourly grid for that date
    tz = None
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(raw.get("timezone") or "UTC")
    except Exception:
        pass
    from datetime import datetime

    def day_of(epoch):
        return datetime.fromtimestamp(epoch, tz).date()

    days = {}
    for p in raw["forecast"]["properties"]["periods"]:
        day = day_of(iso_epoch(p["startTime"]))
        entry = days.setdefault(day, {"look": None, "pops": [], "high": None, "low": None})
        if p["isDaytime"] or entry["look"] is None:
            entry["look"] = (nws_icon(p["icon"]), p["shortForecast"])
        entry["pops"].append((p.get("probabilityOfPrecipitation") or {}).get("value"))
        celsius = (p["temperature"] - 32) * 5 / 9 if p.get("temperatureUnit") == "F" else p["temperature"]
        entry["high" if p["isDaytime"] else "low"] = celsius
    daily = []
    for day in sorted(days)[:7]:
        hours = [t for t in times if day_of(t) == day]
        hourly_temps = [layers["temperature"].get(t) for t in hours if layers["temperature"].get(t) is not None]
        midnight = int(datetime(day.year, day.month, day.day, tzinfo=tz).timestamp())
        icon, text = days[day]["look"]
        high = days[day]["high"] if days[day]["high"] is not None else (max(hourly_temps) if hourly_temps else None)
        low = days[day]["low"] if days[day]["low"] is not None else (min(hourly_temps) if hourly_temps else None)
        temps = [low, high]
        daily.append(period(show, midnight, icon, text, temps,
                            [mean(layers["dewpoint"].get(t) for t in hours)],
                            [mean(layers["relativeHumidity"].get(t) for t in hours)],
                            days[day]["pops"],
                            [max([layers["windSpeed"].get(t) or 0 for t in hours] or [0])],
                            [layers["windGust"].get(t) for t in hours],
                            [(layers["snowfallAmount"].get(t) or 0) / 10 for t in hours],
                            avg=mean(layers["temperature"].get(t) for t in hours)))

    current = None
    ob = ((raw.get("observation") or {}).get("properties")) or {}
    if ob.get("textDescription"):
        clouds = [NWS_CLOUDS.get(layer.get("amount"), 0) for layer in ob.get("cloudLayers") or []]
        current = {
            "icon": nws_icon(ob.get("icon") or ""),
            "text": ob["textDescription"],
            "visibility": show.visibility((ob.get("visibility") or {}).get("value")),
            "cloud_cover": max(clouds) if clouds else None,
        }

    return {
        "belchertown_forecast": FORMAT, "provider": "nws", "timestamp": raw["timestamp"], "timezone": raw.get("timezone"),
        "units": units, "current": current, "aqi": None,
        "daily": daily,
        "three_hourly": hour_periods(show, series, start, 3, 8),
        "hourly": hour_periods(show, series, start, 1, 16),
        "alerts": [],
    }


def in_us(lat, lon):
    """Roughly the US, its territories included, where NWS alerts apply."""
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return True
    return (17 <= lat <= 72 and -180 <= lon <= -64) or (12 <= lat <= 21 and 143 <= lon <= 147) or (-15 <= lat <= -10 and -172 <= lon <= -168)


def nws_alerts(lat, lon):
    """Active NWS alerts for the station; an empty list outside the US."""
    try:
        features = get_json("https://api.weather.gov/alerts/active?point=%s,%s" % (lat, lon))["features"]
    except Exception:
        return []
    alerts = []
    for f in features:
        p = f["properties"]
        alerts.append({
            "title": p["event"],
            "body": "\n\n".join(x for x in (p.get("description"), p.get("instruction")) if x),
            "type": p["event"],
            "expires": iso_epoch(p.get("ends") or p["expires"]),
        })
    return alerts


# ---------------------------------------------------------------------------- entry points

def alert_provider_for(extras, provider):
    """auto: the forecast provider's own alerts (Xweather), else NWS (empty outside the US)."""
    choice = extras.get("forecast_alert_provider", "auto").lower()
    if choice == "auto":
        return "xweather" if provider == "xweather" else "nws"
    return "xweather" if choice == "aeris" else choice


RETRY_HOLD = 600
_last_failure = [0]


def update(path, extras, lat, lon, labels, icon_list_path):
    """Refresh forecast.json if it's stale; return the forecast either way.
    After a failed download the next try waits RETRY_HOLD seconds, so a dead network doesn't stall every report."""
    provider = provider_for(extras)
    cached = None
    if os.path.isfile(path):
        try:
            with open(path) as f:
                cached = json.load(f)
        except (ValueError, OSError):
            cached = None
    if not is_stale(path, extras.get("forecast_stale", 3540)):
        return cached, False
    if time.time() - _last_failure[0] < RETRY_HOLD:
        return cached, False
    try:
        return download(path, extras, lat, lon, labels, icon_list_path, provider)
    except Exception:
        _last_failure[0] = time.time()
        raise


def download(path, extras, lat, lon, labels, icon_list_path, provider):
    if provider == "xweather":
        with open(icon_list_path) as f:
            icons = json.load(f)
        forecast = xweather_convert(xweather_download(extras, lat, lon), extras, labels, icons)
    elif provider == "openmeteo":
        forecast = openmeteo_convert(openmeteo_download(extras, lat, lon), extras, labels)
    elif provider == "nws":
        forecast = nws_convert(nws_download(extras, lat, lon), extras, labels)
    else:
        raise ValueError("Unknown forecast_provider %r" % provider)

    # Fill what the provider doesn't have: air quality from Open-Meteo, alerts from NWS
    if extras.get("aqi_enabled") == "1" and forecast["aqi"] is None and provider != "xweather":
        try:
            forecast["aqi"] = openmeteo_aqi(lat, lon)
        except Exception:
            pass
    alert_provider = alert_provider_for(extras, provider)
    if extras.get("forecast_alert_enabled") != "1" or alert_provider == "none":
        forecast["alerts"] = []
    elif alert_provider == "nws" and (in_us(lat, lon) or extras.get("forecast_alert_provider", "auto").lower() == "nws"):
        forecast["alerts"] = nws_alerts(lat, lon)[:int(extras.get("forecast_alert_limit") or 10)]
        forecast["alert_provider"] = "nws"

    forecast["utc_offset"] = utc_offset(forecast.get("timezone"))
    with open(path, "w") as f:
        json.dump(forecast, f)
    _last_failure[0] = 0
    return forecast, True


def utc_offset(timezone):
    """The location's current UTC offset in seconds (the server's own if the provider gave no zone)."""
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        return int(datetime.now(ZoneInfo(timezone)).utcoffset().total_seconds())
    except Exception:
        return int(datetime.now().astimezone().utcoffset().total_seconds())

