// Apache ECharts drawing for chart_library = echarts. belchertown-charts.js builds each chart's options the
// Highcharts way from graphs.conf; echarts_draw() turns those options into an ECharts chart.

var echarts_store = {};
var echarts_offsets = {};
var echarts_dark_on = null;

// Chart titles are links, in the page's link color as with Highcharts
function echarts_link_color() {
    var a = document.createElement("a");
    a.href = "#";
    a.style.display = "none";
    document.body.appendChild(a);
    var color = getComputedStyle(a).color;
    a.remove();
    return color;
}

function echarts_theme() {
    var dark = document.body.classList.contains("dark");
    return {
        dark: dark,
        background: dark ? "#2a2a2b" : "#ffffff",
        title: echarts_link_color(),
        text: dark ? "#e0e0e3" : "#666666",
        grid: dark ? "#707073" : "#e6e6e6",
        axis: dark ? "#707073" : "#555555",
        pane: dark ? "#505053" : "#e6e6e6",
        tooltip: dark ? "rgba(48,48,50,0.92)" : "rgba(247,247,247,0.92)",
        tooltip_text: dark ? "#e0e0e3" : "#333333",
        font: getComputedStyle(document.body).fontFamily
    };
}

// ECharts has no time zone setting: times are shifted so its UTC clock reads the station's local time
function echarts_offset(ts) {
    var hour = Math.floor(ts / 3600000);
    if (echarts_offsets[hour] === undefined) echarts_offsets[hour] = tzAdjustedMoment(ts / 1000).utcOffset() * 60000;
    return echarts_offsets[hour];
}

function echarts_local(ts) {
    return ts + echarts_offset(ts);
}

function echarts_plain(html) {
    if (html == null) return "";
    return new DOMParser().parseFromString(String(html), "text/html").body.textContent.trim();
}

function echarts_num(value) {
    if (value === undefined || value === null || value === "" || value === "undefined") return null;
    var n = parseFloat(value);
    return isNaN(n) ? null : n;
}

function echarts_true(value) {
    return value === true || String(value).toLowerCase() === "true";
}

// The same labels Highcharts gave the time axis: the time of day, the date at midnight, the month on the 1st of long spans
function echarts_time_label(span) {
    return function(value) {
        var t = dayjs.utc(value);
        if (t.hour() === 0 && t.minute() === 0) {
            if (span > 62 * 86400000 && t.date() === 1) return t.format("MMM YY");
            return t.format("D MMM");
        }
        return t.format("LT");
    };
}

function echarts_point(point, i) {
    if (Array.isArray(point)) return {x: point[0], y: point[1]};
    if (point !== null && typeof point === "object") return {x: point.x !== undefined ? point.x : i, y: point.y};
    return {x: i, y: point};
}

function echarts_value_text(y, meta) {
    return highcharts_tooltip_factory(y, meta.obsType, true, meta.rounding, meta.mirrored, meta.numberFormat);
}

function echarts_dot(color) {
    return "<span style='color:" + color + "'>●</span> ";
}

function echarts_tooltip_base(theme) {
    return {
        backgroundColor: theme.tooltip,
        borderColor: theme.grid,
        textStyle: {color: theme.tooltip_text, fontSize: 13},
        confine: true
    };
}

function echarts_axis_label(labels, theme) {
    var out = {color: theme.text, fontSize: 12};
    if (!labels) return out;
    if (labels.formatter) {
        var formatter = labels.formatter;
        out.formatter = function(value) {
            var text = formatter.call({value: value});
            return text === undefined || text === null ? "" : echarts_plain(text);
        };
    } else if (labels.format) {
        var decimals = /\{value:\.(\d+)f\}/.exec(labels.format);
        if (decimals) out.formatter = function(value) { return wx_number_format(value, parseInt(decimals[1], 10)); };
    }
    if (labels.enabled === false) out.show = false;
    return out;
}

function echarts_title(hc, theme) {
    var titles = [{
        text: echarts_plain(hc.title && hc.title.text),
        subtext: echarts_plain(hc.subtitle && hc.subtitle.text),
        link: "#" + hc.chart.renderTo,
        target: "self",
        left: "center",
        top: 4,
        textStyle: {color: theme.title, fontSize: 18, fontWeight: "normal", fontFamily: theme.font},
        subtextStyle: {color: theme.text, fontSize: 13}
    }];
    var credits = hc.credits || {};
    if (credits.text) {
        var pos = credits.position || {};
        var credit = {text: credits.text, link: credits.href || "", target: "blank", bottom: 2, textStyle: {color: "#999999", fontSize: 11, fontWeight: "normal"}};
        if (pos.align === "left") credit.left = echarts_num(pos.x) || 10;
        else if (pos.align === "center") credit.left = "center";
        else credit.right = 10;
        titles.push(credit);
    }
    return titles;
}

function echarts_toolbox(hc, zoom, theme) {
    var feature = {};
    if (zoom) feature.dataZoom = {yAxisIndex: "none", filterMode: "none"};
    if (hc.exporting && hc.exporting.enabled) feature.saveAsImage = {name: hc.chart.renderTo};
    return Object.keys(feature).length ? {right: 10, top: 2, itemSize: 13, iconStyle: {borderColor: theme.text}, feature: feature} : undefined;
}

function echarts_legend(hc, theme, extra) {
    return Object.assign({
        show: !!(hc.legend && hc.legend.enabled),
        bottom: hc.credits && hc.credits.text ? 18 : 2,
        textStyle: {color: theme.text, fontSize: 12, fontWeight: theme.dark ? "bold" : "normal"},
        itemWidth: 22,
        itemHeight: 10,
        selected: {}
    }, extra || {});
}

function echarts_line_style(dash) {
    if (!dash) return "solid";
    dash = String(dash).toLowerCase();
    return dash.indexOf("dot") >= 0 && dash.indexOf("dash") < 0 ? "dotted" : dash === "solid" ? "solid" : "dashed";
}

// Line, spline, area, column and scatter charts on a time or category axis
function echarts_cartesian(hc, info, theme) {
    var categories = hc.xAxis && hc.xAxis.categories && hc.xAxis.categories.length ? hc.xAxis.categories : null;
    var y_axes = Array.isArray(hc.yAxis) ? hc.yAxis : [hc.yAxis || {}];
    var plot_options = hc.plotOptions || {};
    var connect_nulls = plot_options.series && echarts_true(plot_options.series.connectNulls);
    var legend = echarts_legend(hc, theme);
    var metas = [], series = [], extents = y_axes.map(function() { return {min: Infinity, max: -Infinity, bars: false}; });
    var x_min = Infinity, x_max = -Infinity, visual_maps = [], color_counter = 0;

    hc.series.forEach(function(s, i) {
        var type = s.type || hc.chart.type || "line";
        var color = s.color || hc.colors[color_counter++ % hc.colors.length];
        var axis = Math.min(parseInt(s.yAxis, 10) || 0, y_axes.length - 1);
        var gap = plot_options[type] && echarts_num(plot_options[type].gapSize);
        var marker = s.marker || {}, base_marker = (plot_options[type] && plot_options[type].marker) || {};
        var radius = echarts_num(marker.radius) || echarts_num(base_marker.radius) || 2;
        var markers = type === "scatter" || (marker.enabled !== undefined ? echarts_true(marker.enabled) : base_marker.enabled === true);
        var line_width = s.lineWidth !== undefined ? echarts_num(s.lineWidth) : 2;
        var data = [], last_x = null;

        (s.data || []).forEach(function(point, n) {
            var p = echarts_point(point, n), y = p.y === undefined ? null : p.y;
            if (categories) {
                data.push(y);
            } else {
                if (gap && last_x !== null && p.x - last_x > gap) data.push([echarts_local(last_x + 1), null, last_x + 1]);
                data.push([echarts_local(p.x), y, p.x]);
                last_x = p.x;
                if (p.x < x_min) x_min = p.x;
                if (p.x > x_max) x_max = p.x;
            }
            if (y !== null && !isNaN(y)) {
                extents[axis].min = Math.min(extents[axis].min, y);
                extents[axis].max = Math.max(extents[axis].max, y);
            }
        });

        var out = {
            name: s.name,
            data: data,
            yAxisIndex: axis,
            z: 2 + (echarts_num(s.zIndex) || 0),
            itemStyle: {color: color},
            connectNulls: connect_nulls,
            emphasis: {focus: "none"}
        };
        if (type === "column" || type === "bar") {
            out.type = "bar";
            out.barMaxWidth = 40;
            out.barCategoryGap = "40%";
            extents[axis].bars = true;
        } else if (type === "scatter") {
            out.type = "scatter";
            out.symbol = "circle";
            out.symbolSize = radius * 2;
        } else {
            out.type = "line";
            out.smooth = type === "spline" || type === "areaspline";
            out.symbol = "circle";
            out.showSymbol = markers;
            out.symbolSize = radius * 2;
            out.lineStyle = {width: line_width === null ? 2 : line_width, type: echarts_line_style(s.dashStyle)};
            if (line_width === 0) out.lineStyle.opacity = 0;
            if (type === "area" || type === "areaspline") {
                out.areaStyle = {opacity: echarts_num(s.fillOpacity) || 0.75, origin: "start"};
            }
            if (s.step) out.step = {left: "start", center: "middle", right: "end"}[s.step] || "start";
        }
        if (s.stacking) out.stack = "stack" + axis;
        if (s.visible !== undefined && !echarts_true(s.visible)) legend.selected[s.name] = false;
        if (Array.isArray(s.zones) && s.zones.length) {
            var pieces = [], low = null;
            s.zones.forEach(function(zone) {
                var piece = {color: zone.color || color}, value = echarts_num(zone.value);
                if (low !== null) piece.gte = low;
                if (value !== null) piece.lt = value;
                pieces.push(piece);
                low = value;
            });
            visual_maps.push({type: "piecewise", show: false, seriesIndex: i, dimension: 1, pieces: pieces});
        }
        series.push(out);
        metas.push({obsType: s.observation_type || s.obsType, rounding: s.rounding, mirrored: s.mirrored_value, numberFormat: s.numberFormat || "", color: color, name: s.name});
    });

    var y_out = y_axes.map(function(a, n) {
        var ext = extents[n];
        var axis = {
            type: "value",
            scale: !ext.bars,
            position: a.opposite ? "right" : "left",
            name: echarts_plain(a.title && a.title.text),
            nameLocation: "middle",
            nameGap: 45,
            nameTextStyle: {color: theme.text, fontSize: 13},
            axisLabel: echarts_axis_label(a.labels, theme),
            axisLine: {show: false},
            splitLine: {show: n === 0, lineStyle: {color: theme.grid}},
            minorTick: {show: !!a.minorTicks},
            alignTicks: false
        };
        var min = echarts_num(a.min), max = echarts_num(a.max);
        var soft_min = echarts_num(a.softMin), soft_max = echarts_num(a.softMax);
        if (min === null && soft_min !== null && ext.min > soft_min) min = soft_min;
        if (max === null && soft_max !== null && ext.max < soft_max) max = soft_max;
        if (a.minRange && (min !== null ? min : ext.min) + a.minRange > ext.max && max === null) max = (min !== null ? min : ext.min) + a.minRange;
        if (min !== null) axis.min = min;
        if (max !== null) axis.max = max;
        var interval = echarts_num(a.tickInterval);
        if (interval) axis.interval = interval;
        axis.alignTicks = n > 0 && min === null && max === null && !interval;
        return axis;
    });

    var x_axis = categories ? {
        type: "category",
        data: categories,
        axisLabel: {color: theme.text, fontSize: 12},
        axisLine: {onZero: false, lineStyle: {color: theme.axis}},
        axisTick: {alignWithLabel: true}
    } : {
        type: "time",
        min: echarts_local(x_min),
        max: echarts_local(x_max),
        axisLabel: {color: theme.text, fontSize: 12, hideOverlap: true, formatter: echarts_time_label(x_max - x_min)},
        axisLine: {onZero: false, lineStyle: {color: theme.axis}},
        splitLine: {show: false},
        minInterval: 900000
    };

    var tooltip = Object.assign(echarts_tooltip_base(theme), {
        trigger: "axis",
        axisPointer: {type: "line", lineStyle: {color: theme.axis}},
        formatter: function(params) {
            if (!params.length) return "";
            var head = categories ? params[0].name : tzAdjustedMoment(params[0].value[2] / 1000).format(info.tooltip_date_format);
            var lines = params.map(function(p) {
                var y = categories ? p.value : p.value[1];
                if (y === null || y === undefined || y === "-" || (typeof y === "number" && isNaN(y))) return null;
                var meta = metas[p.seriesIndex];
                return echarts_dot(meta.color) + meta.name + ": " + echarts_value_text(y, meta);
            }).filter(function(line) { return line !== null; });
            return [head].concat(lines).join("<br>");
        }
    });

    var zoom = !categories;
    var subtitle = hc.subtitle && hc.subtitle.text;
    return {
        option: {
            title: echarts_title(hc, theme),
            legend: legend,
            tooltip: tooltip,
            toolbox: echarts_toolbox(hc, zoom, theme),
            grid: {left: 15, right: 15, top: subtitle ? 70 : 50, bottom: (legend.show ? 32 : 10) + (hc.credits && hc.credits.text ? 16 : 0), outerBoundsMode: "same", outerBoundsContain: "all"},
            xAxis: x_axis,
            yAxis: y_out,
            visualMap: visual_maps.length ? visual_maps : undefined,
            series: series
        },
        zoom: zoom
    };
}

// Wind rose: stacked bars around a compass
function echarts_windrose(hc, info, theme) {
    var categories = (hc.xAxis.categories || []).slice(0, 16);
    var legend = echarts_legend(hc, theme, {orient: "vertical", right: 0, top: "middle", bottom: undefined, icon: "circle", itemWidth: 10});
    var series = hc.series.map(function(s, i) {
        return {
            type: "bar",
            coordinateSystem: "polar",
            stack: "rose",
            name: s.name,
            data: (s.data || []).slice(0, 16),
            itemStyle: {color: s.color || hc.colors[i % hc.colors.length]},
            barCategoryGap: "0%",
            emphasis: {focus: "none"}
        };
    });
    return {
        option: {
            title: echarts_title(hc, theme),
            legend: legend,
            tooltip: Object.assign(echarts_tooltip_base(theme), {
                trigger: "axis",
                axisPointer: {type: "shadow"},
                formatter: function(params) {
                    return [params.length ? params[0].name : ""].concat(params.map(function(p) {
                        return echarts_dot(p.color) + p.seriesName + ": " + p.value + "%";
                    })).join("<br>");
                }
            }),
            toolbox: echarts_toolbox(hc, false, theme),
            polar: {radius: "72%", center: [legend.show ? "42%" : "50%", "55%"]},
            angleAxis: {
                type: "category",
                data: categories,
                startAngle: 90 + 180 / Math.max(categories.length, 1),
                axisLabel: {color: theme.text, fontSize: 12},
                axisLine: {lineStyle: {color: theme.axis}},
                axisTick: {show: false},
                splitLine: {show: true, lineStyle: {color: theme.grid}}
            },
            radiusAxis: {min: 0, axisLabel: {show: false}, axisLine: {show: false}, axisTick: {show: false}, splitLine: {show: false}},
            series: series
        }
    };
}

// A range (low to high) drawn as one band, or as a column per point, on a time axis or around a circle
function echarts_range_series(rows, polar, mode, zones, color, y_min, y_max, opacity) {
    var dims = polar ? ["angle", "low", "high", "average"] : ["x", "low", "high", "average"];
    return {
        type: "custom",
        coordinateSystem: polar ? "polar" : "cartesian2d",
        dimensions: dims,
        encode: polar ? {angle: 0, radius: [1, 2], tooltip: [1, 2, 3]} : {x: 0, y: [1, 2], tooltip: [1, 2, 3]},
        data: rows.map(function(r) { return [r.x, r.low, r.high, r.average]; }),
        clip: true,
        renderItem: function(params, api) {
            var at = function(x, y) { return polar ? api.coord([y, x]) : api.coord([x, y]); };
            var fill = function() {
                if (!zones) return color;
                var stops = [], span = y_max - y_min || 1, prev = 0;
                zones.forEach(function(zone, n) {
                    var value = zone.value === undefined ? y_max : Math.min(Math.max(zone.value, y_min), y_max);
                    var pos = (value - y_min) / span;
                    if (pos < prev) return;
                    stops.push({offset: prev, color: zone.color}, {offset: pos, color: zone.color});
                    prev = pos;
                });
                if (prev < 1 && zones.length) stops.push({offset: prev, color: zones[zones.length - 1].color}, {offset: 1, color: zones[zones.length - 1].color});
                if (polar) {
                    var c = params.coordSys, outer = Math.hypot(at(rows[0].x, y_max)[0] - c.cx, at(rows[0].x, y_max)[1] - c.cy) || 1;
                    var inner = Math.hypot(at(rows[0].x, y_min)[0] - c.cx, at(rows[0].x, y_min)[1] - c.cy);
                    return {type: "radial", x: c.cx, y: c.cy, r: outer, global: true, colorStops: stops.map(function(s) { return {offset: (inner + s.offset * (outer - inner)) / outer, color: s.color}; })};
                }
                var bottom = at(rows[0].x, y_min)[1], top = at(rows[0].x, y_max)[1];
                return {type: "linear", x: 0, y: bottom, x2: 0, y2: top, global: true, colorStops: stops};
            };
            if (mode === "band") {
                if (params.dataIndex !== 0) return null;
                var shapes = [], run = [];
                var flush = function() {
                    if (run.length > 1) {
                        var points = run.map(function(r) { return at(r.x, r.high); }).concat(run.slice().reverse().map(function(r) { return at(r.x, r.low); }));
                        shapes.push({type: "polygon", shape: {points: points}, style: {fill: fill(), opacity: opacity}});
                    }
                    run = [];
                };
                rows.forEach(function(r) {
                    if (r.low === null || r.high === null || r.low === undefined || r.high === undefined) flush();
                    else run.push(r);
                });
                flush();
                return {type: "group", children: shapes};
            }
            var row = rows[params.dataIndex];
            if (row.low === null || row.high === null) return null;
            if (polar) {
                var c = params.coordSys, lo = at(row.x, row.low), hi = at(row.x, row.high);
                var angle = Math.atan2(hi[1] - c.cy, hi[0] - c.cx);
                var half = Math.PI / Math.max(rows.length, 1) * 0.8;
                return {type: "sector", shape: {cx: c.cx, cy: c.cy, r0: Math.hypot(lo[0] - c.cx, lo[1] - c.cy), r: Math.hypot(hi[0] - c.cx, hi[1] - c.cy), startAngle: angle - half, endAngle: angle + half, clockwise: true}, style: {fill: row.color || color}};
            }
            var p_low = at(row.x, row.low), p_high = at(row.x, row.high);
            var width = Math.max(api.size([rows.length > 1 ? (rows[rows.length - 1].x - rows[0].x) / (rows.length - 1) : 86400000, 0])[0] * 0.7, 1);
            return {type: "rect", shape: {x: p_low[0] - width / 2, y: p_high[1], width: width, height: Math.max(p_low[1] - p_high[1], 1)}, style: {fill: row.color || color}};
        }
    };
}

// Hays chart (wind speed range around the day) and weather range (daily low/high/average)
function echarts_range(hc, info, theme) {
    var s = hc.series[0], hays = s.obsType === "haysChart", polar = !!hc.chart.polar;
    var rows = (s.data || []).map(function(p) { return {x: echarts_local(p.x), x_raw: p.x, low: p.low, high: p.high, average: p.average, color: p.color}; });
    var mode = hays || hc.chart.type === "arearange" ? "band" : "columns";
    var zones = hc.plotOptions && hc.plotOptions.series && hc.plotOptions.series.zones;
    var y = hc.yAxis || {};
    var lows = rows.map(function(r) { return r.low; }).filter(function(v) { return v !== null && v !== undefined; });
    var highs = rows.map(function(r) { return r.high; }).filter(function(v) { return v !== null && v !== undefined; });
    var interval = echarts_num(y.tickInterval);
    var y_min = echarts_num(y.min) !== null ? echarts_num(y.min) : Math.min.apply(null, lows);
    var y_max = echarts_num(y.max) !== null ? echarts_num(y.max) : Math.max(Math.max.apply(null, highs), echarts_num(y.softMax) || -Infinity);
    if (interval) {
        y_min = Math.floor(y_min / interval) * interval;
        y_max = Math.ceil(y_max / interval) * interval;
    }
    var x_min = rows.length ? rows[0].x : 0, x_max = rows.length ? rows[rows.length - 1].x : 0;
    var color = s.color || hc.colors[0];
    var meta = {obsType: hays ? "haysChart" : "weatherRange", rounding: s.rounding, mirrored: s.mirrored_value, numberFormat: s.numberFormat || ""};
    var series = echarts_range_series(rows, polar, mode, mode === "band" && !hays ? zones : null, color, y_min, y_max, hays ? 1 : 0.75);
    var value_axis = {
        type: "value",
        min: y_min,
        max: y_max,
        interval: interval || undefined,
        name: polar ? undefined : echarts_plain(y.title && y.title.text),
        nameLocation: "middle",
        nameGap: 45,
        nameTextStyle: {color: theme.text, fontSize: 13},
        axisLabel: {color: theme.text, fontSize: 12, showMinLabel: !hays},
        axisLine: {show: false},
        splitLine: {lineStyle: {color: theme.grid}}
    };
    var time_axis = {
        type: polar && hays ? "value" : "time",
        min: x_min,
        max: x_max,
        interval: hays ? 2 * 3600000 : undefined,
        axisLabel: {color: theme.text, fontSize: 12, hideOverlap: true, formatter: echarts_time_label(x_max - x_min)},
        axisLine: {onZero: false, lineStyle: {color: theme.axis}},
        splitLine: {show: polar, lineStyle: {color: theme.grid}}
    };
    var tooltip = Object.assign(echarts_tooltip_base(theme), {
        trigger: "axis",
        axisPointer: {type: "line", lineStyle: {color: theme.axis}},
        formatter: function(params) {
            if (!params.length) return "";
            var row = rows[params[0].dataIndex];
            if (!row || row.low === null || row.high === null) return "";
            var dot = function(v) { return echarts_dot(hays ? color : get_outTemp_color(s.obsUnit, v, true)); };
            var lines = ["<strong>" + tzAdjustedMoment(row.x_raw / 1000).format(info.tooltip_date_format) + "</strong>",
                         dot(row.high) + labels.highest_temperature + ": " + echarts_value_text(row.high, meta),
                         dot(row.low) + labels.lowest_temperature + ": " + echarts_value_text(row.low, meta)];
            if (!hays) lines.push(dot(row.average) + labels.average_temperature + ": " + echarts_value_text(row.average, meta));
            return lines.join("<br>");
        }
    });
    var option = {
        title: echarts_title(hc, theme),
        legend: {show: false},
        tooltip: tooltip,
        toolbox: echarts_toolbox(hc, !polar, theme),
        series: [series]
    };
    if (polar) {
        option.polar = {radius: "75%", center: ["50%", "55%"]};
        option.angleAxis = Object.assign(time_axis, {startAngle: 90, clockwise: true});
        option.radiusAxis = value_axis;
        option.angleAxis.axisPointer = {show: true};
    } else {
        option.grid = {left: 15, right: 15, top: 50, bottom: hc.credits && hc.credits.text ? 26 : 10, outerBoundsMode: "same", outerBoundsContain: "all"};
        option.xAxis = time_axis;
        option.yAxis = value_axis;
    }
    return {option: option, zoom: !polar};
}

// Gauge and air quality: the latest value on a ring
function echarts_gauge(hc, info, theme) {
    var s = hc.series[0], point = s.data[1] || {}, labels_opt = (hc.plotOptions.solidgauge || {}).dataLabels || {};
    var y = Array.isArray(hc.yAxis) ? hc.yAxis[0] : hc.yAxis || {};
    var format = labels_opt.format || "{y}";
    var value = point.y;
    var text = format.replace(/\{y(?::\.(\d+|#)f)?\}/g, function(all, decimals) {
        if (decimals === undefined) return value;
        return wx_number_format(value, decimals === "#" ? -1 : parseInt(decimals, 10));
    });
    var parts = text.split(/<br\s*\/?>/i).map(echarts_plain);
    var size = /font-size:\s*(\d+)px/.exec(text.split(/<br\s*\/?>/i)[1] || "");
    var color = point.color || s.color || hc.colors[0];
    return {
        option: {
            title: echarts_title(hc, theme),
            series: [{
                type: "gauge",
                startAngle: 230,
                endAngle: -50,
                min: echarts_num(y.min) || 0,
                max: echarts_num(y.max) || 100,
                radius: "88%",
                center: ["50%", "58%"],
                progress: {show: true, width: 70, roundCap: !!(hc.plotOptions.solidgauge || {}).rounded, itemStyle: {color: color}},
                axisLine: {roundCap: !!(hc.plotOptions.solidgauge || {}).rounded, lineStyle: {width: 70, color: [[1, theme.pane]]}},
                pointer: {show: false},
                axisTick: {show: false},
                splitLine: {show: false},
                axisLabel: {show: false},
                anchor: {show: false},
                title: {show: false},
                detail: {
                    valueAnimation: false,
                    offsetCenter: [0, 0],
                    formatter: function() { return "{v|" + parts[0] + "}" + (parts[1] ? "\n{l|" + parts[1] + "}" : ""); },
                    rich: {
                        v: {fontSize: 50, fontWeight: "bold", color: color, lineHeight: 56},
                        l: {fontSize: size ? parseInt(size[1], 10) : 14, fontWeight: "bold", color: color, lineHeight: 24}
                    }
                },
                data: [{value: value}]
            }]
        }
    };
}

// A legend that wraps on a narrow chart needs room under the axis, and a polar chart's outer labels need room inside it
function echarts_fit(option, width, height) {
    var legend = option.legend;
    if (legend && legend.show && legend.orient !== "vertical" && option.grid) {
        var names = (option.series || []).map(function(s) { return s.name || ""; });
        var row = 0, rows = 1;
        names.forEach(function(name) {
            var item = name.length * 7 + 45;
            if (row + item > width - 20 && row > 0) { rows++; row = 0; }
            row += item;
        });
        option.grid.bottom += (rows - 1) * 20;
    }
    var gauge = option.series && option.series[0] && option.series[0].type === "gauge" ? option.series[0] : null;
    if (gauge) {
        var ring = Math.min(width, height - 40) / 2 * 0.88 * 0.4;
        gauge.progress.width = ring;
        gauge.axisLine.lineStyle.width = ring;
    }
    if (option.polar) {
        var narrow = width < 500;
        if (narrow && legend && legend.orient === "vertical") {
            Object.assign(legend, {orient: "horizontal", right: undefined, top: undefined, left: "center", bottom: option.title.length > 1 ? 20 : 2});
            option.polar.center = ["50%", "46%"];
        }
        var room = legend && legend.show && !narrow && legend.orient === "vertical" ? 130 : 0;
        var radius = Math.min((width - room) / 2 - 62, (height - (narrow && legend && legend.show ? 130 : 70)) / 2 - 30);
        option.polar.radius = Math.max(radius, 40);
        if (option.radiusAxis && option.radiusAxis.interval && radius < 150) {
            option.radiusAxis.interval *= 2;
            option.radiusAxis.axisLabel.showMaxLabel = false;
        }
    }
}

function echarts_build(hc, info, width, height) {
    var theme = echarts_theme(), built;
    var first = hc.series && hc.series[0] || {};
    if (hc.chart.type === "solidgauge") built = echarts_gauge(hc, info, theme);
    else if (String(hc.chart.className || "").indexOf("highcharts-windRose") >= 0) built = echarts_windrose(hc, info, theme);
    else if (first.obsType === "haysChart" || first.obsType === "weatherRange") built = echarts_range(hc, info, theme);
    else built = echarts_cartesian(hc, info, theme);
    echarts_fit(built.option, width || 600, height || 400);
    built.option.backgroundColor = theme.background;
    built.option.textStyle = {fontFamily: theme.font};
    built.option.animation = false;
    built.option.useUTC = true;
    built.option.aria = {enabled: true};
    return built;
}

function echarts_draw(hc, info) {
    var el = document.getElementById(hc.chart.renderTo);
    if (!el) return null;
    var old = echarts.getInstanceByDom(el);
    if (old) old.dispose();
    if (el.clientHeight < 100) el.style.height = "400px";
    echarts_dark_on = document.body.classList.contains("dark");
    var chart = echarts.init(el);
    var built = echarts_build(hc, info || {}, el.clientWidth, el.clientHeight);
    chart.setOption(built.option);
    if (built.zoom && window.matchMedia("(pointer: fine)").matches) {
        chart.dispatchAction({type: "takeGlobalCursor", key: "dataZoomSelect", dataZoomSelectActive: true});
    }
    if (!echarts_store[el.id] && window.ResizeObserver) new ResizeObserver(function() { echarts_resize(el.id); }).observe(el);
    echarts_store[el.id] = {hc: hc, info: info || {}, width: el.clientWidth};
    return chart;
}

// Legends and polar charts are laid out for a width, so a real width change draws the chart again
function echarts_resize(id) {
    var el = document.getElementById(id), entry = echarts_store[id], chart = el && echarts.getInstanceByDom(el);
    if (!chart || !entry) return;
    if (Math.abs(el.clientWidth - entry.width) > 40) echarts_draw(entry.hc, entry.info);
    else chart.resize();
}

function echarts_reflow() {
    Object.keys(echarts_store).forEach(echarts_resize);
}

function echarts_destroy() {
    Object.keys(echarts_store).forEach(function(id) {
        var el = document.getElementById(id), chart = el && echarts.getInstanceByDom(el);
        if (chart) chart.dispose();
    });
    echarts_store = {};
}

// The skin's light/dark switch recolors Highcharts with CSS; ECharts draws its own colors, so draw again
new MutationObserver(function() {
    if (!document.body || echarts_dark_on === null) return;
    var dark = document.body.classList.contains("dark");
    if (dark === echarts_dark_on) return;
    Object.keys(echarts_store).forEach(function(id) {
        var entry = echarts_store[id];
        if (document.getElementById(id)) echarts_draw(entry.hc, entry.info);
    });
}).observe(document.documentElement, {attributes: true, subtree: true, attributeFilter: ["class"]});
