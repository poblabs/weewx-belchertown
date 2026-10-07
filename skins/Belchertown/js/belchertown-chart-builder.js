// Chart builder page (chart-builder/): pick observations and options, preview the chart with the skin's own
// chart code, and get the graphs.conf section that draws it. Data comes from json/chart_builder.json.

var cb_data = null;
var CB_COLORS = ["#7cb5ec", "#b2df8a", "#f7a35c", "#8c6bb1", "#dd3497", "#e4d354", "#268bd2", "#f45b5b", "#6a3d9a", "#33a02c"];

function cb_el(id) {
    return document.getElementById(id);
}

function cb_esc(text) {
    return String(text).replace(/[&<>"]/g, function(c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; });
}

// The unit label the visitor is looking at: the station's, or the other system's after the unit switch
function cb_unit_label(o) {
    var alt = units_alt_on() && alt_unit(o.unit);
    var label = (alt ? units_config.labels[alt] : o.unit_label || "").trim();
    return label ? " (" + label + ")" : "";
}

// The observations the builder offers: what the station recorded lately, plus rainTotal (rain added up over the chart)
function cb_observations() {
    var list = Object.keys(cb_data.observations).map(function(obs) {
        var o = cb_data.observations[obs];
        return {obs: obs, label: o.label + cb_unit_label(o)};
    });
    if (cb_data.observations.rain) list.push({obs: "rainTotal", label: labels.chart_builder_rain_total + cb_unit_label(cb_data.observations.rain)});
    return list.sort(function(a, b) { return a.label.localeCompare(b.label); });
}

function cb_add_line(obs) {
    var n = cb_el("cb-lines").children.length;
    var row = document.createElement("div");
    row.className = "cb-line";
    row.innerHTML =
        '<select class="cb-obs">' + cb_observations().map(function(o) {
            return '<option value="' + o.obs + '"' + (o.obs === obs ? " selected" : "") + ">" + cb_esc(o.label) + "</option>";
        }).join("") + "</select>" +
        '<label>' + labels.chart_builder_name + ' <input type="text" class="cb-name"></label>' +
        '<label>' + labels.chart_builder_color + ' <input type="color" class="cb-color" value="' + CB_COLORS[n % CB_COLORS.length] + '"></label>' +
        '<label class="cb-check"><input type="checkbox" class="cb-right"> ' + labels.chart_builder_right_axis + "</label>" +
        '<button type="button" class="cb-remove" title="' + labels.chart_builder_remove + '" aria-label="' + labels.chart_builder_remove + '"><i class="fa fa-times"></i></button>';
    row.querySelector(".cb-color").dataset.auto = "1";
    cb_el("cb-lines").appendChild(row);
    cb_update();
}

function cb_lines() {
    return Array.from(document.querySelectorAll(".cb-line")).map(function(row) {
        var obs = row.querySelector(".cb-obs").value;
        var color = row.querySelector(".cb-color");
        return {obs: obs, name: row.querySelector(".cb-name").value.replace(/"/g, "'").trim(), color: color.value, color_set: color.dataset.auto !== "1",
                right: row.querySelector(".cb-right").checked};
    });
}

// graphs.conf values are written in double quotes, so a typed double quote becomes a single one
function cb_text(id, fallback) {
    return cb_el(id).value.replace(/"/g, "'").trim() || fallback;
}

function cb_settings() {
    var time = cb_el("cb-time"), detail = cb_el("cb-detail").value.split(" ");
    return {title: cb_text("cb-title", labels.chart_builder_default_title), type: cb_el("cb-type").value,
            time: time.value, span: time.selectedOptions[0].dataset.span, aggregate: detail[0] || "", interval: detail[1] || "",
            group: cb_el("cb-group").value, group_title: cb_text("cb-group-title", labels.chart_builder_default_page_title),
            lines: cb_lines()};
}

// Group readings into hours or days the way weewx does, for the preview
function cb_aggregate(points, how, interval) {
    if (!how) return points;
    var size = interval === "day" ? 86400000 : 3600000, buckets = {};
    points.forEach(function(p) {
        if (p[1] === null) return;
        var key = interval === "day" ? tzAdjustedMoment(p[0] / 1000).startOf("day").valueOf() : Math.floor(p[0] / size) * size;
        (buckets[key] = buckets[key] || []).push(p[1]);
    });
    return Object.keys(buckets).sort().map(function(k) {
        var v = buckets[k], value;
        if (how === "max") value = Math.max.apply(null, v);
        else if (how === "min") value = Math.min.apply(null, v);
        else if (how === "sum") value = v.reduce(function(a, b) { return a + b; }, 0);
        else value = v.reduce(function(a, b) { return a + b; }, 0) / v.length;
        return [Number(k), Math.round(value * 100) / 100];
    });
}

function cb_series_data(obs, s) {
    var source = cb_data.observations[obs === "rainTotal" ? "rain" : obs];
    var points = (source.spans[s.span] || []).slice();
    if (s.time === "today") {
        var midnight = tzAdjustedMoment(cb_data.generated).startOf("day").valueOf();
        points = points.filter(function(p) { return p[0] >= midnight; });
    }
    if (obs === "rainTotal") {
        var total = 0;
        return points.map(function(p) { total += p[1] || 0; return [p[0], Math.round(total * 100) / 100]; });
    }
    return cb_aggregate(points, s.aggregate, s.interval);
}

function cb_preview(s) {
    var series = {};
    s.lines.forEach(function(line, i) {
        var source = cb_data.observations[line.obs === "rainTotal" ? "rain" : line.obs];
        var name = line.name || (line.obs === "rainTotal" ? labels.chart_builder_rain_total : source.label);
        series[line.obs + "_" + i] = {obsType: line.obs, name: name, data: cb_series_data(line.obs, s), color: line.color,
                                     unit: source.unit, rounding: 2, yAxis: line.right ? 1 : 0,
                                     yAxis_label: name + (source.unit_label ? " (" + source.unit_label.trim() + ")" : "")};
    });
    var plot = {options: {renderTo: "cb-chart", title: s.title, subtitle: "", type: s.type, gapsize: 0, connectNulls: "false",
                          xAxis_categories: [], plot_tooltip_date_format: "LLL", css_class: "", css_height: "", css_width: "",
                          legend: "true", exporting: "false"},
                series: series};
    if (units_alt_on()) convert_chart_units({preview: plot});
    Highcharts.charts.forEach(function(c) { if (c) c.destroy(); });
    render_chart(plot, {colors: CB_COLORS, credits: "highcharts_default", credits_url: "", credits_position: "{}"}, "chart_builder", false);
}

// A section name graphs.conf accepts, unique among the charts already in that group
function cb_chart_id(s) {
    var base = s.title.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "chart";
    var taken = (config.charts[s.group] || []);
    var id = base, n = 2;
    while (taken.indexOf(id) >= 0) id = base + "_" + n++;
    return id;
}

function cb_conf(s) {
    var out = [], new_group = s.group === "";
    var group = new_group ? (s.group_title.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "mycharts") : s.group;
    if (new_group) {
        out.push("[" + group + "]");
        out.push('    title = "' + s.group_title + '"');
        out.push("    show_button = true");
        out.push('    button_text = "' + s.group_title + '"');
        out.push("");
    }
    out.push("    [[" + cb_chart_id(s) + "]]");
    out.push('        title = "' + s.title + '"');
    out.push("        type = " + s.type);
    out.push("        time_length = " + s.time);
    if (s.aggregate) {
        out.push("        aggregate_type = " + s.aggregate);
        out.push("        aggregate_interval = " + s.interval);
    }
    s.lines.forEach(function(line) {
        out.push("        [[[" + line.obs + "]]]");
        var name = line.name || (line.obs === "rainTotal" ? labels.chart_builder_rain_total : "");
        if (name) out.push('            name = "' + name + '"');
        if (line.color_set) out.push('            color = "' + line.color + '"');
        if (line.right) out.push("            yAxis = 1");
    });
    return {text: out.join("\n") + "\n", group: group, new_group: new_group};
}

function cb_update() {
    if (!cb_data) return;
    var s = cb_settings();
    cb_el("cb-new-group").style.display = s.group === "" ? "" : "none";
    var conf = cb_conf(s);
    cb_el("cb-output").value = conf.text;
    cb_el("cb-step-paste").textContent = conf.new_group ? labels.chart_builder_step_paste_new : labels.chart_builder_step_paste_group.replace("{group}", conf.group);
    if (s.lines.length) cb_preview(s);
}

wx_ready(function() {
    var groups = cb_el("cb-group");
    Object.keys(config.charts).forEach(function(g) {
        groups.insertAdjacentHTML("beforeend", '<option value="' + cb_esc(g) + '">' + cb_esc(config.graphpage_titles[g] || g) + "</option>");
    });
    groups.insertAdjacentHTML("beforeend", '<option value="">' + labels.chart_builder_new_page + "</option>");

    wx_json(get_relative_url() + "/json/chart_builder.json").then(function(data) {
        cb_data = data;
        cb_add_line(data.observations.outTemp ? "outTemp" : Object.keys(data.observations)[0]);
    }).catch(function() {
        cb_el("cb-chart").innerHTML = '<p class="cb-note">' + labels.chart_builder_no_data + "</p>";
    });

    document.addEventListener("wx-units", function() {
        if (!cb_data) return;
        var names = {};
        cb_observations().forEach(function(o) { names[o.obs] = o.label; });
        document.querySelectorAll(".cb-obs option").forEach(function(opt) { opt.textContent = names[opt.value]; });
        cb_update();
    });
    cb_el("cb-add").addEventListener("click", function() { cb_add_line(); });
    document.querySelector(".chart-builder").addEventListener("input", function(e) {
        if (e.target.classList.contains("cb-color")) e.target.dataset.auto = "0";
        if (e.target.id !== "cb-output") cb_update();
    });
    document.querySelector(".chart-builder").addEventListener("change", cb_update);
    cb_el("cb-lines").addEventListener("click", function(e) {
        var remove = e.target.closest(".cb-remove");
        if (remove) {
            remove.closest(".cb-line").remove();
            cb_update();
        }
    });
    cb_el("cb-copy").addEventListener("click", function() {
        var text = cb_el("cb-output");
        var done = function() { cb_el("cb-copied").textContent = labels.chart_builder_copied; };
        if (navigator.clipboard) navigator.clipboard.writeText(text.value).then(done, function() { text.select(); document.execCommand("copy"); done(); });
        else { text.select(); document.execCommand("copy"); done(); }
    });
});
