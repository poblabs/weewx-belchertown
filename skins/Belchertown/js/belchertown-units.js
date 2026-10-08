// Visitor's unit switch: shows the page in the other unit system (°F <-> °C, mph <-> km/h, ...).
// The station's own units come from belchertown_config.units; every conversion happens here.

var units_config = belchertown_config.units;

var UNIT_ALT = {
    degree_F: "degree_C", degree_C: "degree_F",
    mile_per_hour: "km_per_hour", km_per_hour: "mile_per_hour", meter_per_second: "km_per_hour",
    mile_per_hour2: "km_per_hour2", km_per_hour2: "mile_per_hour2", meter_per_second2: "km_per_hour2",
    inHg: "hPa", hPa: "inHg", mbar: "inHg", kPa: "inHg", mmHg: "hPa",
    inch: "mm", mm: "inch", cm: "inch",
    inch_per_hour: "mm_per_hour", mm_per_hour: "inch_per_hour", cm_per_hour: "inch_per_hour",
    mile: "km", km: "mile",
    foot: "meter", meter: "foot",
    degree_F_day: "degree_C_day", degree_C_day: "degree_F_day"
};

// Factor to a common base per dimension (m/s, hPa, mm, mm/h, km, m); temperatures are special-cased
var UNIT_FACTOR = {
    mile_per_hour: 0.44704, km_per_hour: 1 / 3.6, meter_per_second: 1, knot: 0.514444,
    mile_per_hour2: 0.44704, km_per_hour2: 1 / 3.6, meter_per_second2: 1,
    inHg: 33.8638866667, hPa: 1, mbar: 1, kPa: 10, mmHg: 1.33322368,
    inch: 25.4, mm: 1, cm: 10,
    inch_per_hour: 25.4, mm_per_hour: 1, cm_per_hour: 10,
    mile: 1.609344, km: 1,
    foot: 0.3048, meter: 1,
    degree_F_day: 5 / 9, degree_C_day: 1
};

function units_alt_on() {
    try { return localStorage.getItem("belchertown_units") === "alt"; } catch (e) { return false; }
}

function alt_unit(unit) {
    var alt = UNIT_ALT[unit];
    return alt && units_config.labels[alt] !== undefined ? alt : null;
}

// delta: a temperature difference (a daily range), which converts without the 32° offset
function convert_unit(value, from, to, delta) {
    if (value === null || value === undefined || isNaN(value) || from === to) return value;
    if (from === "degree_F" && to === "degree_C") return delta ? value * 5 / 9 : (value - 32) * 5 / 9;
    if (from === "degree_C" && to === "degree_F") return delta ? value * 9 / 5 : value * 9 / 5 + 32;
    return value * UNIT_FACTOR[from] / UNIT_FACTOR[to];
}

function unit_decimals(unit) {
    var m = /%\.(\d+)f/.exec(units_config.formats[unit] || "");
    return m ? parseInt(m[1]) : 0;
}

function format_unit_value(value, unit) {
    var d = unit_decimals(unit);
    return Number(value).toLocaleString(config.system_locale_js, {minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: false});
}

// The unit a group is shown in right now
function display_unit(group) {
    var unit = units_config.groups[group];
    return (units_alt_on() && alt_unit(unit)) || unit;
}

function display_label(group, fallback) {
    var unit = display_unit(group);
    return units_config.labels[unit] !== undefined ? units_config.labels[unit] : fallback;
}

// Label for an observation such as "outTemp" or "barometer", for code that labels by observation name
function display_label_for_obs(obs, fallback) {
    var group = units_config.obs[obs];
    return group && units_alt_on() ? display_label(group, fallback) : fallback;
}

// --- Text on the page: "58.0 °F" becomes "14.4 °C" ---

var unit_text_regex = null, unit_by_label = {};

function build_unit_text_regex() {
    var labels = [];
    Object.keys(units_config.groups).forEach(function(group) {
        var unit = units_config.groups[group];
        var label = (units_config.labels[unit] || "").trim();
        if (label && alt_unit(unit) && !(label in unit_by_label)) {
            unit_by_label[label] = unit;
            labels.push(label);
        }
    });
    if (!labels.length) return null;
    labels.sort(function(a, b) { return b.length - a.length; });
    var escaped = labels.map(function(l) { return l.replace(/[.*+?^${}()|[\]\\\/]/g, "\\$&"); });
    return new RegExp("(-?\\d+(?:[.,]\\d+)*)(\\s*)(" + escaped.join("|") + ")(?![A-Za-z0-9/])", "g");
}

function parse_number(text) {
    var dec = (1.5).toLocaleString(config.system_locale_js).charAt(1);
    if (dec === ",") text = text.replace(/\./g, "").replace(",", ".");
    else text = text.replace(/,/g, "");
    return parseFloat(text);
}

function ensure_unit_regex() {
    if (!unit_text_regex) unit_text_regex = build_unit_text_regex();
    return unit_text_regex;
}
if (units_alt_on()) ensure_unit_regex();

function convert_unit_text(text, delta) {
    if (!ensure_unit_regex()) return text;
    return text.replace(unit_text_regex, function(match, number, space, label, offset, whole) {
        if (/^[a-z]+$/.test(label) && /^\s+[a-z]/.test(whole.slice(offset + match.length))) return match;
        var from = unit_by_label[label], to = alt_unit(from);
        var value = convert_unit(parse_number(number), from, to, delta);
        return format_unit_value(value, to) + space + units_config.labels[to].trim();
    });
}

// What each converted text node or bare number said in station units, and what we last wrote into it.
// Text that differs from what we wrote is new (from MQTT or a refresh) and becomes the new original.
var unit_orig = new WeakMap();
var unit_done = new WeakMap();
var UNIT_SKIP = "script, style, textarea, input, .highcharts-container, [data-units-skip]";

function convert_unit_node(node) {
    if (node.nodeType === Node.TEXT_NODE) {
        var parent = node.parentElement;
        if (!parent || parent.closest(UNIT_SKIP)) return;
        if (parent.closest("[data-unit-group]")) {
            convert_bare_number(parent.closest("[data-unit-group]"));
            return;
        }
        if (unit_done.get(node) === node.nodeValue) return;
        unit_orig.set(node, node.nodeValue);
        var converted = convert_unit_text(node.nodeValue, !!parent.closest("[data-unit-delta]"));
        if (converted !== node.nodeValue) node.nodeValue = converted;
        unit_done.set(node, node.nodeValue);
        return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE || node.closest(UNIT_SKIP)) return;
    var bare = node.closest("[data-unit-group]");
    if (bare) {
        convert_bare_number(bare);
        return;
    }
    node.querySelectorAll("[data-unit-group]").forEach(convert_bare_number);
    update_unit_labels(node);
    var walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    var texts = [];
    while (walker.nextNode()) texts.push(walker.currentNode);
    texts.forEach(convert_unit_node);
}

function update_unit_labels(node) {
    node.querySelectorAll("[data-unit-label]").forEach(function(el) {
        el.textContent = units_config.labels[display_unit(el.dataset.unitLabel)];
    });
}

// Back to the station's units: every node we converted gets its original text again
function restore_unit_nodes(node) {
    var walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
        var t = walker.currentNode;
        if (unit_orig.has(t) && unit_done.get(t) === t.nodeValue) t.nodeValue = unit_orig.get(t);
        unit_orig.delete(t);
        unit_done.delete(t);
    }
    node.querySelectorAll("[data-unit-group]").forEach(function(el) {
        if (unit_orig.has(el) && unit_done.get(el) === el.textContent.trim()) el.textContent = unit_orig.get(el);
        unit_orig.delete(el);
        unit_done.delete(el);
    });
    update_unit_labels(node);
}

// An element holding just a number whose unit is shown elsewhere, such as the big temperature
function convert_bare_number(el) {
    var text = el.textContent.trim();
    if (unit_done.get(el) === text) return;
    unit_orig.set(el, el.textContent);
    var from = units_config.groups[el.dataset.unitGroup], to = alt_unit(from), value = parse_number(text);
    if (to && !isNaN(value)) el.textContent = format_unit_value(convert_unit(value, from, to), to);
    unit_done.set(el, el.textContent.trim());
}

// --- Data the scripts draw from ---

var FORECAST_UNITS = {F: "degree_F", C: "degree_C", mph: "mile_per_hour", "km/h": "km_per_hour", "m/s": "meter_per_second", "in": "inch", cm: "cm"};

function convert_forecast_units(data) {
    var u = data.units || {}, temp = FORECAST_UNITS[u.temp], wind = FORECAST_UNITS[u.wind], snow = FORECAST_UNITS[u.snow];
    var temp_to = display_unit("group_temperature"), wind_to = display_unit("group_speed");
    var snow_to = display_unit("group_rain") === "inch" ? "inch" : "cm";
    if (snow_to === snow) snow = null;
    if (temp_to === temp) temp_to = null;
    if (wind_to === wind || ["knot", "beaufort"].indexOf(units_config.groups.group_speed) >= 0) wind_to = null;
    ["daily", "three_hourly", "hourly"].forEach(function(key) {
        (data[key] || []).forEach(function(p) {
            if (temp_to) ["temp_avg", "temp_min", "temp_max", "dewpoint"].forEach(function(f) { p[f] = convert_unit(p[f], temp, temp_to); });
            if (wind_to) ["wind", "gust"].forEach(function(f) { p[f] = convert_unit(p[f], wind, wind_to); });
            if (snow && p.snow) p.snow = convert_unit(p.snow, snow, snow_to);
        });
    });
    if (snow) u.snow = snow_to === "cm" ? "cm" : "in";
    return data;
}

// Chart group JSON: each series says which unit its data is in
function convert_chart_units(data) {
    Object.keys(data).forEach(function(plotname) {
        var plot = data[plotname];
        if (!plot || !plot.series) return;
        Object.keys(plot.series).forEach(function(name) {
            var s = plot.series[name], from = s.range_unit || s.unit || series_station_unit(s), to = from && alt_unit(from);
            if (s.obsType === "windRose") {
                (s.data || []).forEach(function(bin) { if (bin && bin.name) bin.name = convert_unit_range_text(bin.name); });
                return;
            }
            if (!to) return;
            var from_label = (units_config.labels[from] || "").trim(), to_label = units_config.labels[to].trim();
            s.data = (s.data || []).map(function(point) {
                if (Array.isArray(point)) {
                    return point.map(function(v, i) { return i === 0 || v === null ? v : convert_unit(v, from, to); });
                }
                return typeof point === "number" ? convert_unit(point, from, to) : point;
            });
            if (s.yAxis_label) s.yAxis_label = swap_axis_unit(s.yAxis_label, from_label, to_label);
            if (plot.options && plot.options.yAxis_label) plot.options.yAxis_label = swap_axis_unit(plot.options.yAxis_label, from_label, to_label);
            if (s.rounding !== undefined && s.rounding >= 0) s.rounding = unit_decimals(to);
            if (s.range_unit) {
                s.range_unit = to;
                s.range_unit_label = units_config.labels[to];
            }
            if (s.unit) s.unit = to;
            ["yAxis_min", "yAxis_max", "yAxis_softMin", "yAxis_softMax"].forEach(function(key) {
                if (s[key] !== undefined && s[key] !== null && s[key] !== "" && s[key] !== "undefined") s[key] = convert_unit(parseFloat(s[key]), from, to);
            });
            if (s.yAxis_tickInterval) s.yAxis_tickInterval = convert_unit(parseFloat(s.yAxis_tickInterval), from, to, true);
        });
    });
    return data;
}

// Chart files written before series carried their unit: go by the observation
function series_station_unit(s) {
    var obs = s.observation_type || s.obsType;
    if (obs === "rainTotal") obs = "rain";
    if (obs === "haysChart") obs = "windSpeed";
    var group = units_config.obs[obs];
    return group ? units_config.groups[group] : null;
}

// "Rain Total (in)" -> "Rain Total (mm)": only the unit in parentheses
function swap_axis_unit(text, from_label, to_label) {
    if (!from_label) return text;
    return text.split("(" + from_label + ")").join("(" + to_label + ")");
}

// "1-3  mph" (windrose speed bins) -> "2-5 km/h"
function convert_unit_range_text(text) {
    return text.replace(/(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)(\s*)(\S+)\s*$/, function(match, a, b, space, label) {
        var from = unit_by_label[label], to = from && alt_unit(from);
        if (!to) return match;
        return Math.round(convert_unit(parseFloat(a), from, to)) + "-" + Math.round(convert_unit(parseFloat(b), from, to)) + " " + units_config.labels[to].trim();
    }).replace(/^([<>]?\s*)(\d+(?:\.\d+)?)(\+?)(\s*)(\S+)\s*$/, function(match, pre, a, plus, space, label) {
        var from = unit_by_label[label], to = from && alt_unit(from);
        if (!to) return match;
        return pre + Math.round(convert_unit(parseFloat(a), from, to)) + plus + " " + units_config.labels[to].trim();
    });
}

// --- The switch ---

// The temperature unit on screen now
function unit_switch_text() {
    return (units_config.labels[display_unit("group_temperature")] || "").trim();
}

// Chart groups drawn on this page, so a switch can draw them again
var charts_shown = [];

var unit_observer = new MutationObserver(function(mutations) {
    if (!units_alt_on()) return;
    mutations.forEach(function(m) {
        if (m.type === "characterData") convert_unit_node(m.target);
        else m.addedNodes.forEach(convert_unit_node);
    });
});

function set_units(alt) {
    try { localStorage.setItem("belchertown_units", alt ? "alt" : "station"); } catch (e) {}
    if (alt) convert_unit_node(document.body);
    else restore_unit_nodes(document.body);
    wx_all("#unitSwitch span").forEach(function(s) { s.textContent = unit_switch_text(); });
    if (window.forecast_last_data) update_forecast_data(forecast_last_data);
    charts_shown.forEach(function(args) { showChart(args[0], args[1]); });
    document.dispatchEvent(new Event("wx-units"));
}

document.addEventListener("DOMContentLoaded", function() {
    var button = document.getElementById("unitSwitch");
    if (button) {
        button.querySelector("span").textContent = unit_switch_text();
        button.addEventListener("click", function() { set_units(!units_alt_on()); });
    }
    if (units_alt_on()) convert_unit_node(document.body);
    unit_observer.observe(document.body, {childList: true, characterData: true, subtree: true});
    document.documentElement.classList.remove("units-pending");
});
