var graphgroups_raw = config.charts;
var graphgroups_titles = config.graphpage_titles;
var graphpage_content = config.graphpage_content;

// http://stackoverflow.com/a/14887961/1177153
var weatherdirection = config.windDir_ordinals;

function get_gauge_color(value, options) {
    if (options.color1) {
        // Failsafe in case value drops below the lowest color position user has set.
        // Otherwise color is undefined when the value is below color1_position
        var color = options.color1
    }
    if (options.color2) {
        if (value >= options.color2_position) {
            var color = options.color2
        }
    }
    if (options.color3) {
        if (value >= options.color3_position) {
            var color = options.color3
        }
    }
    if (options.color4) {
        if (value >= options.color4_position) {
            var color = options.color4
        }
    }
    if (options.color5) {
        if (value >= options.color5_position) {
            var color = options.color5
        }
    }
    if (options.color6) {
        if (value >= options.color6_position) {
            var color = options.color6
        }
    }
    if (options.color7) {
        if (value >= options.color7_position) {
            var color = options.color7
        }
    }
    return color
}

function get_gauge_label(value, options) {
    if (options.color1) {
        if (options.color1_label) {
            var label = options.color1_label
        }
    }
    if (options.color2) {
        if (value >= options.color2_position) {
            var label = null
            if (options.color2_label) {
                var label = options.color2_label
            }
        }
    }
    if (options.color3) {
        if (value >= options.color3_position) {
            var label = null
            if (options.color3_label) {
                var label = options.color3_label
            }
        }
    }
    if (options.color4) {
        if (value >= options.color4_position) {
            var label = null
            if (options.color4_label) {
                var label = options.color4_label
            }
        }
    }
    if (options.color5) {
        if (value >= options.color5_position) {
            var label = null
            if (options.color5_label) {
                var label = options.color5_label
            }
        }
    }
    if (options.color6) {
        if (value >= options.color6_position) {
            var label = null
            if (options.color6_label) {
                var label = options.color6_label
            }
        }
    }
    if (options.color7) {
        if (value >= options.color7_position) {
            var label = null
            if (options.color7_label) {
                var label = options.color7_label
            }
        }
    }
    return label
}

Highcharts.setOptions({
    global: {
        //useUTC: false
        timezoneOffset: config.highcharts_timezoneoffset
    },
    lang: {
        months: dayjs.months(),
        shortMonths: dayjs.monthsShort(),
        weekdays: dayjs.weekdays(),
        shortWeekdays: dayjs.weekdaysShort(),
        decimalPoint: config.highcharts_decimal,
        thousandsSep: config.highcharts_thousands
    }
});

function showChart(json_file, prepend_renderTo = false) {
    // Relative URL by finding what page we're on currently.
    jQuery.getJSON(get_relative_url() + '/json/' + json_file + '.json', function(data) {
        var group = {
            colors: data.colors.split(","),
            credits: data.credits.split(",")[0],
            credits_url: data.credits_url.split(",")[0],
            credits_position: data.credits_position
        };
        jQuery.each(data, function(plotname, plot) {
            if (plot && plot.options) {
                render_chart(plot, group, json_file, prepend_renderTo);
            }
        });
    });
}

// Build one chart from its entry in a chart group's JSON file.
function render_chart(plot, group, json_file, prepend_renderTo) {
    var opt = plot.options;
    var tooltip_date_format = opt.plot_tooltip_date_format;
    var observation_type = undefined;
    var options = chart_base_options(opt.exporting, opt.legend, tooltip_date_format);


    // Set the chart render div and title
    if (prepend_renderTo) {
        options.chart.renderTo = json_file + "_" + opt.renderTo;
    } else {
        options.chart.renderTo = opt.renderTo;
    }

    belchertown_debug(options.chart.renderTo + ": building a " + opt.type + " chart");

    if (opt.css_class) {
        jQuery("#" + options.chart.renderTo).addClass(opt.css_class);
        belchertown_debug(options.chart.renderTo + ": div id is " + options.chart.renderTo + " and adding CSS class: " + opt.css_class);
    }

    options.chart.type = opt.type;
    options.title.text = "<a href='#" + options.chart.renderTo + "'>" + opt.title + "</a>"; // Anchor link to chart for direct linking
    options.subtitle.text = opt.subtitle;
    options.plotOptions.area.gapSize = opt.gapsize;
    options.plotOptions.line.gapSize = opt.gapsize;
    options.plotOptions.spline.gapSize = opt.gapsize;
    options.plotOptions.scatter.gapSize = opt.gapsize;
    if (opt.connectNulls == "true") {
        options.plotOptions.series = {connectNulls: opt.connectNulls};
    }
    options.colors = group.colors;

    // If we have xAxis categories, reset xAxis and populate it from these options. Also need to reset tooltip since there's no datetime for moment.js to use.
    if (opt.xAxis_categories.length >= 1) {
        belchertown_debug(options.chart.renderTo + ": has " + opt.xAxis_categories.length + " xAxis categories. Resetting xAxis and tooltips for grouping");
        options.xAxis = {}
        options.xAxis.categories = opt.xAxis_categories;
        options.tooltip = {}
        options.tooltip = {
            enabled: true,
            crosshairs: true,
            split: true,
            formatter: function() {
                // The first returned item is the header, subsequent items are the points
                return [this.x].concat(
                    this.points.map(function(point) {
                        // If observation_type is in the series array, use that otherwise use the obsType
                        var point_obsType = point.series.userOptions.observation_type ? point.series.userOptions.observation_type : point.series.userOptions.obsType;
                        var rounding = point.series.userOptions.rounding;
                        var mirrored = point.series.userOptions.mirrored_value;
                        var numberFormat = point.series.userOptions.numberFormat ? point.series.userOptions.numberFormat : "";
                        return "<span style='color:" + point.series.color + "'>\u25CF</span> " + point.series.name + ': ' + highcharts_tooltip_factory(point.y, point_obsType, true, rounding, mirrored, numberFormat);
                    })
                );
            },
        }
    }

    // Reset the series everytime we loop.
    options.series = [];

    // Build the series
    var i = 0;
    jQuery.each(plot.series, function(seriesName, seriesVal) {
        observation_type = plot.series[seriesName]["obsType"];
        options.series[i] = plot.series[seriesName];
        i++;
    });

    /* yAxis customization handler and label handling
    Take the following example. 
    yAxis is in observation 0 (rainTotal), so that label is caught and set by yAxis1_active. 
    If you move yAxis to observation 1 (rainRate), then the label is caught and set by yAxis_index.
    There may be a more efficient way to do this. If so, please submit a pull request :)
    [[[chart3]]]
        title = Rain
        [[[[rainTotal]]]]
            name = Rain Total
            yAxis = 1
        [[[[rainRate]]]]
    */

    var yAxis1_active = undefined;

    // Find if any series have yAxis = 1. If so, save the array number so we can set labels correctly.
    // We really care if yAxis is in array 1+, so we can go back and set yAxis 0 to the right label.
    var yAxis_index = options.series.findIndex(function(item) {return item.yAxis == 1})

    // Handle series specific data, overrides and non-Highcharts options that we passed through
    options.series.forEach(s => {
        if (s.yAxis == "1") {
            // If yAxis = 1 is set for the observation, add a new yAxis and associate that observation to the right side of the chart
            yAxis1_active = true;
            options.yAxis.push({ // Secondary yAxis
                opposite: true,
                title: {
                    text: s.yAxis_label,
                },
            }),
                // Associate this series to the new yAxis 1
                s.yAxis = 1

            // We may have already passed through array 0 in the series without setting the "multi axis label", go back and explicitly define it.
            if (yAxis_index >= 1) {
                options.yAxis[0].title.text = options.series[0].yAxis_label;
            }
        } else {
            if (yAxis1_active) {
                // This yAxis is first in the data series, so we can set labels without needing to double back
                options.yAxis[0].title.text = s.yAxis_label;
            } else {
                // Apply the normal yAxis 0's label without observation name
                options.yAxis[0].title.text = s.yAxis_label;
            }
            // Associate this series to yAxis 1
            s.yAxis = 0;
        }

        // Run yAxis customizations
        var this_yAxis = s.yAxis;

        belchertown_debug(options.chart.renderTo + ": " + s.obsType + " is on yAxis " + this_yAxis);

        // Some charts may require a defined min/max on the yAxis
        options.yAxis[this_yAxis].min = s.yAxis_min !== "undefined" ? s.yAxis_min : null;
        options.yAxis[this_yAxis].max = s.yAxis_max !== "undefined" ? s.yAxis_max : null;

        // Some charts may require a defined soft min/max on the yAxis
        options.yAxis[this_yAxis].softMin = s.yAxis_softMin !== "undefined" ? parseInt(s.yAxis_softMin) : null;
        options.yAxis[this_yAxis].softMax = s.yAxis_softMax !== "undefined" ? parseInt(s.yAxis_softMax) : null;

        // Set the yAxis tick interval. Mostly used for barometer. 
        if (s.yAxis_tickInterval) {
            options.yAxis[this_yAxis].tickInterval = s.yAxis_tickInterval;
        }

        // Set yAxis minorTicks. This is a graph-wide setting so setting it for any of the yAxis will set it for the graph itself
        if (s.yAxis_minorTicks) {
            options.yAxis[this_yAxis].minorTicks = true;
        }

        // Barometer chart plots get a higher precision yAxis tick
        if (s.obsType == "barometer") {
            // Define yAxis label float format if rounding is defined. Default to 2 decimals if nothing defined
            if (typeof s.rounding !== "undefined") {
                options.yAxis[this_yAxis].labels = {format: '{value:.' + s.rounding + 'f}'}
            } else {
                options.yAxis[this_yAxis].labels = {format: '{value:.2f}'}
            }
        }

        // Rain, RainRate and rainTotal (special Belchertown skin observation) get yAxis precision
        if (s.obsType == "rain" || s.obsType == "rainRate" || s.obsType == "rainTotal") {
            options.yAxis[this_yAxis].min = 0;
            options.yAxis[this_yAxis].minRange = 0.01;
            options.yAxis[this_yAxis].minorGridLineWidth = 1;
        }

        if (s.obsType == "windDir") {
            options.yAxis[this_yAxis].tickInterval = 90;
            options.yAxis[this_yAxis].labels = {
                useHTML: true,
                formatter: function() {var value = weatherdirection[this.value]; return value !== 'undefined' ? value : this.value;}
            }
        }

        // Check if this series has a gapsize override
        if (s.gapsize) {
            options.plotOptions.area.gapSize = s.gapsize;
            options.plotOptions.line.gapSize = s.gapsize;
            options.plotOptions.spline.gapSize = s.gapsize;
            options.plotOptions.scatter.gapSize = s.gapsize;
        }

        // If this chart is a mirrored chart, make the yAxis labels non-negative
        if (s.mirrored_value) {
            belchertown_debug(options.chart.renderTo + ": mirrored chart due to mirrored_value = true");
            options.yAxis[s.yAxis].labels = {formatter: function() {return Math.abs(this.value);}}
        }

        // Lastly, apply any numberFormat label overrides
        if (typeof s.numberFormat !== "undefined" && Object.keys(s.numberFormat).length >= 1) {
            var {decimals, decimalPoint, thousandsSep} = s.numberFormat
            options.yAxis[this_yAxis].labels = {formatter: function() {return Highcharts.numberFormat(this.value, decimals, decimalPoint, thousandsSep);}}
        }

    });

    if (observation_type == "windRose") {
        windrose_chart(options);
    }
    if (options.chart.type == "gauge") {
        gauge_chart(options, observation_type);
    }
    if (observation_type == "aqiChart") {
        aqi_chart(options);
    }
    if (observation_type == "haysChart") {
        hays_chart(options, observation_type, tooltip_date_format);
    }
    if (observation_type == "weatherRange") {
        weather_range_chart(options, observation_type, tooltip_date_format);
    }

    // Apply any width, height CSS overrides to the parent div of the chart
    if (opt.css_height != "") {
        jQuery("#" + options.chart.renderTo).parent().css({
            'height': opt.css_height,
            'padding': '0px 15px',
            'margin-bottom': '20px'
        });
    }
    if (opt.css_width != "") {
        jQuery("#" + options.chart.renderTo).parent().css('width', opt.css_width);
    }

    if (group.credits != "highcharts_default") {
        options.credits.text = group.credits;
    }

    if (group.credits_url != "highcharts_default") {
        options.credits.href = group.credits_url;
    }

    if (group.credits_position != "highcharts_default") {
        options.credits.position = JSON.parse(group.credits_position);
    }

    // Finally all options are done, now show the chart
    var chart = new Highcharts.chart(options);

    // If using debug, show a copy paste debug for use with jsfiddle
    belchertown_debug(options);
    belchertown_debug("Highcharts.chart('container', " + JSON.stringify(options) + ");");
}

function chart_base_options(exporting_enabled, legend_enabled, tooltip_date_format) {
    var options = {
        chart: {
            renderTo: '',
            spacing: [5, 10, 10, 0],
            type: '',
            zoomType: 'x'
        },

        exporting: {
            chartOptions: {
                chart: {
                    events: {
                        load: function() {
                            this.title.update({style: {color: '#e5554e'}});

                            if (sessionStorage.getItem('currentTheme') === 'dark') {
                                var darktheme_textcolor = '#fff';
                                for (var i = this.yAxis.length - 1; i >= 0; i--) {
                                    this.yAxis[i].update({
                                        title: {style: {color: darktheme_textcolor}},
                                        labels: {style: {color: darktheme_textcolor}},
                                        gridLineColor: '#707073',
                                        tickColor: '#707073'
                                    });
                                }

                                for (var i = this.xAxis.length - 1; i >= 0; i--) {
                                    this.xAxis[i].update({
                                        title: {style: {color: darktheme_textcolor}},
                                        labels: {style: {color: darktheme_textcolor}},
                                        gridLineColor: '#707073',
                                        tickColor: '#707073'
                                    });
                                }

                                this.legend.update({itemStyle: {color: darktheme_textcolor}});

                                //this.credits.update({style:{color: darktheme_textcolor}});

                                this.subtitle.update({style: {color: darktheme_textcolor}});

                                this.chartBackground.attr({fill: jQuery(".highcharts-background").css("fill")});
                            } else {
                                var lighttheme_textcolor = '#666666';
                                for (var i = this.yAxis.length - 1; i >= 0; i--) {
                                    this.yAxis[i].update({
                                        title: {style: {color: lighttheme_textcolor}},
                                        labels: {style: {color: lighttheme_textcolor}},
                                    });
                                }

                                for (var i = this.xAxis.length - 1; i >= 0; i--) {
                                    this.xAxis[i].update({
                                        title: {style: {color: lighttheme_textcolor}},
                                        labels: {style: {color: lighttheme_textcolor}},
                                    });
                                }
                            }
                        }
                    }
                }
            },
            // scale: 1,
            // width: 1000,
            // sourceWidth: 1000,
            enabled: JSON.parse(String(exporting_enabled)) // Convert string to bool
        },

        title: {
            useHTML: true,
            text: ''
        },

        subtitle: {
            text: ''
        },

        legend: {
            enabled: JSON.parse(String(legend_enabled)) // Convert string to bool
        },

        xAxis: {
            dateTimeLabelFormats: {
                day: '%e %b',
                week: '%e %b',
                month: '%b %y',
            },
            lineColor: '#555',
            minRange: 900000,
            minTickInterval: 900000,
            title: {
                style: {
                    font: 'bold 12px Lucida Grande, Lucida Sans Unicode, Verdana, Arial, Helvetica, sans-serif'
                }
            },
            ordinal: false,
            type: 'datetime'
        },

        yAxis: [{
            endOnTick: true,
            lineColor: '#555',
            minorGridLineWidth: 0,
            startOnTick: true,
            showLastLabel: true,
            title: {
            },
            opposite: false
        }],

        plotOptions: {
            area: {
                lineWidth: 2,
                gapSize: '',
                gapUnit: 'value',
                marker: {
                    enabled: false,
                    radius: 2
                },
                threshold: null,
                softThreshold: true
            },
            line: {
                lineWidth: 2,
                gapSize: '',
                gapUnit: 'value',
                marker: {
                    enabled: false,
                    radius: 2
                },
            },
            spline: {
                lineWidth: 2,
                gapSize: '',
                gapUnit: 'value',
                marker: {
                    enabled: false,
                    radius: 2
                },
            },
            areaspline: {
                lineWidth: 2,
                gapSize: '',
                gapUnit: 'value',
                marker: {
                    enabled: false,
                    radius: 2
                },
                threshold: null,
                softThreshold: true
            },
            scatter: {
                gapSize: '',
                gapUnit: 'value',
                marker: {
                    radius: 2
                },
            },
        },

        // Highstock is needed for gapsize. Disable these 3 to make it look like standard Highcharts
        scrollbar: {
            enabled: false
        },
        navigator: {
            enabled: false
        },
        rangeSelector: {
            enabled: false
        },

        tooltip: {
            enabled: true,
            crosshairs: true,
            dateTimeLabelFormats: {
                hour: '%e %b %H:%M'
            },
            // For locale control with moment.js
            formatter: function(tooltip) {
                try {
                    // The first returned item is the header, subsequent items are the points.
                    // Mostly applies to line style charts (line, spline, area)
                    return [tzAdjustedMoment(this.x / 1000).format(tooltip_date_format)].concat(
                        this.points.map(function(point) {
                            // If observation_type is in the series array, use that otherwise use the obsType
                            var point_obsType = point.series.userOptions.observation_type ? point.series.userOptions.observation_type : point.series.userOptions.obsType;
                            var rounding = point.series.userOptions.rounding;
                            var mirrored = point.series.userOptions.mirrored_value;
                            var numberFormat = point.series.userOptions.numberFormat ? point.series.userOptions.numberFormat : "";
                            return "<span style='color:" + point.series.color + "'>\u25CF</span> " + point.series.name + ': ' + highcharts_tooltip_factory(point.y, point_obsType, true, rounding, mirrored, numberFormat);
                        })
                    );
                } catch (e) {
                    // There's an error so check if it's windDir to apply wind direction label, or if it's a scatter. If none of those revert back to default tooltip.
                    if (this.series.userOptions.obsType == "windDir" || this.series.userOptions.observation_type == "windDir") {
                        // If observation_type is in the series array, use that otherwise use the obsType
                        var point_obsType = this.series.userOptions.observation_type ? this.series.userOptions.observation_type : this.series.userOptions.obsType;
                        var rounding = this.series.userOptions.rounding;
                        var mirrored = this.series.userOptions.mirrored_value;
                        return tzAdjustedMoment(this.x / 1000).format(tooltip_date_format) + '<br><b>' + highcharts_tooltip_factory(this.point.y, point_obsType, true, rounding, mirrored);
                    } else if (this.series.userOptions.type == "scatter") {
                        // Catch anything else that might be a scatter plot. Scatter plots will just show x,y coordinates without this.
                        return "<span style='color:" + this.series.color + "'>\u25CF</span> " + this.series.name + ': ' + Highcharts.numberFormat(this.y);
                    } else {
                        return tooltip.defaultFormatter.call(this, tooltip);
                    }
                }
            },
            split: true,
        },

        credits: {},

        series: [{}]

    };
    return options;
}

// Wind rose: a polar stacked column chart.
function windrose_chart(options) {
    var categories = config.ordinate_names;
    options.chart.className = "highcharts-windRose"; // Used for dark mode
    options.chart.type = "column";
    options.chart.polar = true;
    options.chart.alignTicks = false;
    options.pane = {size: '80%'}
    // Reset xAxis and rebuild
    options.xAxis = {}
    options.xAxis.min = 0;
    options.xAxis.max = 16;
    options.xAxis.crosshair = true;
    options.xAxis.categories = categories;
    options.xAxis.tickmarkPlacement = 'on';
    options.xAxis.labels = {useHTML: true}
    //options.legend.align = "right";
    options.legend.verticalAlign = "top";
    options.legend.x = 210;
    options.legend.y = 119;
    options.legend.layout = "vertical";
    options.legend.floating = true;
    options.yAxis[0].min = 0;
    options.yAxis[0].endOnTick = false;
    options.yAxis[0].reversedStacks = false;
    options.yAxis[0].title.text = labels.graphs_windrose_frequency + " (%)";
    options.yAxis[0].gridLineWidth = 0;
    options.yAxis[0].labels = {enabled: false}
    options.yAxis[0].zIndex = 800;
    options.plotOptions = {
        column: {
            stacking: 'normal',
            shadow: false,
            groupPadding: 0,
            pointPlacement: 'on',
        }
    }
    // Reset the tooltip
    options.tooltip = {}
    options.tooltip.shared = true;
    options.tooltip.valueSuffix = '%';
    options.tooltip.followPointer = true;
    options.tooltip.useHTML = true;

    // Since wind rose is a special observation, I did not re-do the JSON arrays to accomodate it as a separate array.
    // So we need to grab the data array within the series and save it to a temporary array, delete the entire chart series, 
    // and reapply the windrose data back to the series.
    var newSeries = options.series[0].data;
    options.series = [];
    newSeries.forEach(ns => {
        options.series.push(ns);
    });
}

// Gauge: shows the most recent value as a solid gauge.
function gauge_chart(options, observation_type) {
    // Highcharts does not allow the guage background to have rounded ends. To get around
    // this, define a "dummy" series that fills the gauge with the appropriate color.
    // This way, the ends are rounded if the user specifies.
    //
    // Gauge chart works best with only one data point, so the most recent (last) data point
    // is used
    options.series[0].data = [{
        y: 9999999,
        color: '#e6e6e6',
        className: 'highcharts-pane',
        zIndex: 0,
        dataLabels: {enabled: false}
    }, {
        y: options.series[0].data.pop()[1],
        color: options.series[0].color,
    }]
    options.chart.type = "solidgauge"
    options.pane = {
        startAngle: -140,
        endAngle: 140,
        background: [{
            outerRadius: 0,
            innerRadius: 0,
        }]
    }
    // If user has set colors_enabled, change the color according to the value
    if (options.series[0].colors_enabled) {
        options.series[0].data[1].color = get_gauge_color(options.series[0].data[1]["y"], options.series[0])
    }
    options.plotOptions = {
        solidgauge: {
            dataLabels: {
                useHTML: true,
                enabled: true,
                borderWidth: 0,
                style: {
                    fontWeight: 'bold',
                    lineHeight: '0.5em',
                    textAlign: 'center',
                    fontSize: '50px',
                    // Match color if set by user
                    color: options.series[0].data[1].color,
                    textOutline: 'none'
                }
            },
        }
    }
    if (get_gauge_label(options.series[0].data[1]["y"], options.series[0])) {
        options.plotOptions.solidgauge.dataLabels.format = "<span style='text-align:center'>{y:.#f}</span><br><span style='font-size:14px;text-align:center'>" + get_gauge_label(options.series[0].data[1]["y"], options.series[0]) + '</span>'
        options.plotOptions.solidgauge.dataLabels.y = -25
    } else if (unit_label_array[observation_type] == null) {
        options.plotOptions.solidgauge.dataLabels.format = "<span style='text-align:center'>{y:.#f}</span>"
    } else {
        options.plotOptions.solidgauge.dataLabels.format = "<span style='text-align:center'>{y:.#f}</span><br><span style='font-size:20px;text-align:center'>" + unit_label_array[observation_type] + '</span>'
        options.plotOptions.solidgauge.dataLabels.y = -25
    }
    options.yAxis = {
        min: 0,
        max: 100,
        lineColor: null,
        tickPositions: []
    }
    // Override default max and min if user has specified
    if (options.series[0].yAxis_max) {
        options.yAxis.max = options.series[0].yAxis_max;
    }
    if (options.series[0].yAxis_min) {
        options.yAxis.min = options.series[0].yAxis_min;
    }
    options.tooltip.enabled = false
    options.xAxis.crosshair = false
}

// Air quality as a solid gauge.
function aqi_chart(options) {
    // Highcharts does not allow the guage background to have rounded ends. To get around
    // this, define a "dummy" series that fills the gauge with the appropriate color.
    // This way, the ends are rounded if the user specifies.
    options.series[0].data = [{
        y: 500,
        color: '#e6e6e6',
        className: 'highcharts-pane',
        zIndex: 0,
        dataLabels: {enabled: false}
    }, {
        y: options.series[0].data[0]['y'],
        color: get_aqi_color(options.series[0].data[0]['y'], true),
        category: options.series[0].data[0]['category']
    }]
    options.chart.type = "solidgauge"
    options.pane = {
        startAngle: -140,
        endAngle: 140,
        background: [{
            outerRadius: 0,
            innerRadius: 0,
        }]
    }
    options.plotOptions = {
        solidgauge: {
            dataLabels: {
                useHTML: true,
                enabled: true,
                y: -30,
                borderWidth: 0,
                format: '<span style="text-align:center">{y}</span><br><span style="font-size:14px;text-align:center">' + options.series[0].data[1]['category'] + '</span>',
                style: {
                    fontWeight: 'bold',
                    lineHeight: '0.5em',
                    textAlign: 'center',
                    fontSize: '50px',
                    color: options.series[0].data[1].color,
                    textOutline: 'none'
                }
            },
            linecap: 'round',
            rounded: true
        }
    }
    options.yAxis = {
        min: 0,
        max: 500,
        lineColor: null,
        tickPositions: []
    }
    options.tooltip.enabled = false
    options.xAxis.crosshair = false
}

// Hays chart: a polar area range.
function hays_chart(options, observation_type, tooltip_date_format) {
    options.chart.type = "arearange"
    options.chart.polar = true;
    options.plotOptions = {
        turboThreshold: 0,
        series: {
            marker: {
                enabled: false
            }
        }
    };
    // Find min and max of the series data for the yAxis min and max
    var maximum_flattened = [];
    options.series[0].data.forEach(seriesData => {
        maximum_flattened.push(seriesData[2]);
    });
    var range_max = Math.max(...maximum_flattened);
    if (options.series[0].yAxis_softMax) {
        var range_max = options.series[0].yAxis_softMax;
    }
    options.legend = {"enabled": false}
    options.yAxis = {
        showFirstLabel: false,
        tickInterval: 2,
        tickmarkPlacement: 'on',
        min: -1,
        softMax: range_max,
        title: {
            text: options.series[0].yAxis_label,
        },
        labels: {
            align: 'center',
            x: 0,
            y: 0
        },
    }
    options.tooltip = {
        split: false,
        shared: true,
        followPointer: true,
        useHTML: true,
        formatter: function(tooltip) {
            return this.points.map(function(point) {
                var rounding = point.series.userOptions.rounding;
                var mirrored = point.series.userOptions.mirrored_value;
                var numberFormat = point.series.userOptions.numberFormat ? point.series.userOptions.numberFormat : "";
                return "<strong>" + tzAdjustedMoment(point.x / 1000).format(tooltip_date_format) + "</strong><br><span style='color:" + options.series[0].color + "'>\u25CF</span> " + labels.highest_temperature + ": " + highcharts_tooltip_factory(point.point.high, observation_type, true, rounding, mirrored, numberFormat) + "<br><span style='color:" + options.series[0].color + "'>\u25CF</span> " + labels.lowest_temperature + ": " + highcharts_tooltip_factory(point.point.low, observation_type, true, rounding, mirrored, numberFormat);
            });
        }
    }
    var currentSeries = options.series;
    var currentSeriesData = options.series[0].data;
    var range_unit = options.series[0].range_unit;
    var rounding = options.series[0].rounding;
    var newSeriesData = [];
    var currentSeriesColor = options.series[0].color;
    currentSeriesData.forEach(seriesData => {
        newSeriesData.push({
            x: seriesData[0],
            low: seriesData[1],
            high: seriesData[2],
        });
    });
    options.series = [];
    options.series.push({
        data: newSeriesData,
        obsType: "haysChart",
        obsUnit: range_unit,
        rounding: rounding,
        color: currentSeriesColor,
        fillColor: currentSeriesColor,
        connectEnds: false,
    });
}

// Weather range: daily low/high/average as columns or an area, optionally polar.
function weather_range_chart(options, observation_type, tooltip_date_format) {
    if (options.series[0].area_display) {
        options.chart.type = "arearange";
    } else {
        options.chart.type = "columnrange";
    }

    // If polar is defined, use it and add a special dark mode CSS class
    if (JSON.parse(String(options.series[0].polar.toLowerCase()))) {
        options.chart.polar = true; // Make sure the option is a string, then convert to bool
        options.chart.className = "highcharts-weatherRange belchertown-polar"; // Used for dark mode
    } else {
        options.chart.className = "highcharts-weatherRange"; // Used for dark mode
    }

    options.legend = {"enabled": false}

    // Find min and max of the series data for the yAxis min and max
    var minimum_flattened = [];
    var maximum_flattened = [];
    options.series[0].data.forEach(seriesData => {
        minimum_flattened.push(seriesData[1]);
        maximum_flattened.push(seriesData[2]);
    });
    var range_min = Math.min(...minimum_flattened);
    var range_max = Math.max(...maximum_flattened);

    var yAxis_tickInterval = Math.ceil(Math.round(range_max / 5) / 5) * 5; // Divide max outTemp by 5 and round it, then round that value up to the nearest 5th multiple. This gives clean yAxis tick lines. 

    options.yAxis = {
        showFirstLabel: true,
        tickInterval: yAxis_tickInterval,
        min: range_min,
        max: range_max,
        title: {
            text: options.series[0].yAxis_label,
        },
    }

    options.xAxis = {
        dateTimeLabelFormats: {
            day: '%e %b',
            week: '%e %b',
            month: '%b %y',
        },
        showLastLabel: true,
        crosshair: true,
        type: "datetime"
    }

    options.plotOptions = {}
    options.plotOptions = {
        series: {
            turboThreshold: 0,
            showInLegend: false,
            borderWidth: 0,
            marker: {
                enabled: false,
            },
        }
    }

    if (options.series[0].area_display) {
        if (options.series[0].range_unit == "degree_F") {
            options.plotOptions.series.zones = [
                {value: 0, color: "#1278c8"},
                {value: 25, color: "#30bfef"},
                {value: 32, color: "#1fafdd"},
                {value: 40, color: "rgba(0,172,223,1)"},
                {value: 50, color: "#71bc3c"},
                {value: 55, color: "rgba(90,179,41,0.8)"},
                {value: 65, color: "rgba(131,173,45,1)"},
                {value: 70, color: "rgba(206,184,98,1)"},
                {value: 75, color: "rgba(255,174,0,0.9)"},
                {value: 80, color: "rgba(255,153,0,0.9)"},
                {value: 85, color: "rgba(255,127,0,1)"},
                {value: 90, color: "rgba(255,79,0,0.9)"},
                {value: 95, color: "rgba(255,69,69,1)"},
                {value: 110, color: "rgba(255,104,104,1)"},
                {color: "rgba(218,113,113,1)"},
            ]
        } else {
            options.plotOptions.series.zones = [
                {value: -5, color: "#1278c8"},
                {value: -3.8, color: "#30bfef"},
                {value: 0, color: "#1fafdd"},
                {value: 4.4, color: "rgba(0,172,223,1)"},
                {value: 10, color: "#71bc3c"},
                {value: 12.7, color: "rgba(90,179,41,0.8)"},
                {value: 18.3, color: "rgba(131,173,45,1)"},
                {value: 21.1, color: "rgba(206,184,98,1)"},
                {value: 23.8, color: "rgba(255,174,0,0.9)"},
                {value: 26.6, color: "rgba(255,153,0,0.9)"},
                {value: 29.4, color: "rgba(255,127,0,1)"},
                {value: 32.2, color: "rgba(255,79,0,0.9)"},
                {value: 35, color: "rgba(255,69,69,1)"},
                {value: 43.3, color: "rgba(255,104,104,1)"},
                {color: "rgba(218,113,113,1)"},
            ]
        }
    } else {
        options.plotOptions.series.stacking = "normal"
    }

    options.tooltip = {
        split: false,
        shared: true,
        followPointer: true,
        useHTML: true,
        formatter: function(tooltip) {
            return this.points.map(function(point) {
                var rounding = point.series.userOptions.rounding;
                var mirrored = point.series.userOptions.mirrored_value;
                var numberFormat = point.series.userOptions.numberFormat ? point.series.userOptions.numberFormat : "";
                return "<strong>" + tzAdjustedMoment(point.x / 1000).format(tooltip_date_format) + "</strong><br><span style='color:" + get_outTemp_color(point.series.userOptions.obsUnit, point.point.high, true) + "'>\u25CF</span> " + labels.highest_temperature + ": " + highcharts_tooltip_factory(point.point.high, observation_type, true, rounding, mirrored, numberFormat) + "<br><span style='color:" + get_outTemp_color(point.series.userOptions.obsUnit, point.point.low, true) + "'>\u25CF</span> " + labels.lowest_temperature + ": " + highcharts_tooltip_factory(point.point.low, observation_type, true, rounding, mirrored, numberFormat) + "<br><span style='color:" + get_outTemp_color(point.series.userOptions.obsUnit, point.point.average, true) + "'>\u25CF</span> " + labels.average_temperature + ": " + highcharts_tooltip_factory(point.point.average, observation_type, true, rounding, mirrored, numberFormat);
            });
        }
    }

    // Update data
    var currentSeries = options.series;
    var currentSeriesData = options.series[0].data;
    var range_unit = options.series[0].range_unit;
    var rounding = options.series[0].rounding;
    var newSeriesData = [];
    currentSeriesData.forEach(seriesData => {
        if (options.series[0].color) {
            var color = options.series[0].color;
        } else {
            // Set color of the column based on the average temperature, or return default if not temperature
            var color = get_outTemp_color(range_unit, seriesData[3], true);
        }
        newSeriesData.push({
            x: seriesData[0],
            low: seriesData[1],
            high: seriesData[2],
            average: seriesData[3],
            color: color
        });
    });
    options.series = [];
    options.series.push({
        data: newSeriesData,
        obsType: "weatherRange",
        obsUnit: range_unit,
        rounding: rounding
    });
}
