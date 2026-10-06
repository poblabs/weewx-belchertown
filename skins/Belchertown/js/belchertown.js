// Settings come from belchertown-config.js (js/belchertown-config.js.tmpl), loaded just before this file.
var config = belchertown_config;
var extras = belchertown_config.extras;
// Like $obs.label in a template: an unknown label returns its own name.
var labels = new Proxy(belchertown_config.labels, {
    get: function(target, key) {
        return (typeof key === "string" && !(key in target)) ? key : target[key];
    }
});

var pages = ["graphs", "records", "reports", "about"];
var pageName = "";
// If this page we're on now is listed as a subpage, use ".." to get to the relative root
function get_relative_url() {
    var sPath = window.location.pathname.replace(/\/$/, "");
    pageName = sPath.substring(sPath.lastIndexOf('/') + 1);
    if (pages.includes(pageName)) {
        var relative_url = "..";
    } else {
        var relative_url = ".";
    }
    belchertown_debug("URL: Relative URL is: " + relative_url);

    return relative_url;
}

// ?view=kiosk on the home page (the class is set in header.html.tmpl before the page draws)
function is_kiosk_view() {
    return document.documentElement.classList.contains("view-kiosk");
}

// Determine if debug is on via URL var or config setting
if (getURLvar("debug") && (getURLvar("debug") == "true" || getURLvar("debug") == "1")) {
    var belchertown_debug_config = true;
    belchertown_debug("Debug: URL debug variable enabled");
} else {
    var belchertown_debug_config = config.belchertown_debug;
    belchertown_debug("Debug: skin.conf belchertown_debug enabled");
}

// Dates are formatted with Day.js, which takes the same format codes as moment.js (LLL, dddd, ...)
["utc", "timezone", "localizedFormat", "advancedFormat", "localeData"].forEach(function(plugin) {
    dayjs.extend(window["dayjs_plugin_" + plugin]);
});
fix_dayjs_catalan();
dayjs.locale(config.dayjs_locale);

// Day.js's Catalan capitalizes names and drops "de"/"d'" ("6 Octubre de 2026");
// use moment.js's wording ("6 d'octubre de 2026"), which the skin had before 2.0.
function fix_dayjs_catalan() {
    var ca = dayjs.Ls.ca;
    if (!ca) {
        return;
    }
    var standalone = "gener_febrer_març_abril_maig_juny_juliol_agost_setembre_octubre_novembre_desembre".split("_");
    var after_day = "de gener_de febrer_de març_d'abril_de maig_de juny_de juliol_d'agost_de setembre_d'octubre_de novembre_de desembre".split("_");
    var months = function(date, format) {
        // After a day number; advancedFormat has already turned Do into text such as "6è"
        return /(D[oD]?|\d+\S*)(\[[^\[\]]*\]|\s)+MMMM/.test(format) ? after_day[date.month()] : standalone[date.month()];
    };
    months.s = standalone;
    months.f = after_day;
    ca.months = months;
    ca.monthsShort = "gen._febr._març_abr._maig_juny_jul._ag._set._oct._nov._des.".split("_");
    ca.weekdays = "diumenge_dilluns_dimarts_dimecres_dijous_divendres_dissabte".split("_");
    ca.weekdaysShort = "dg._dl._dt._dc._dj._dv._ds.".split("_");
}

function belchertown_debug(message) {
    if (belchertown_debug_config > 0) {
        console.log(message);
    }
}

jQuery(document).ready(function() {

    // Bootstrap hover tooltips
    jQuery(function() {
        jQuery('[data-toggle="tooltip"]').tooltip()
    })

    // If the visitor has overridden the theme, keep that theme going throughout the full site and their visit.
    if (sessionStorage.getItem('theme') == "toggleOverride") {
        belchertown_debug("Theme: sessionStorage override in place.");
        changeTheme(sessionStorage.getItem('currentTheme'));
    }

    // Change theme if a URL variable is set
    if (window.location.search.indexOf('theme')) {
        if (getURLvar("theme") == "dark") {
            belchertown_debug("Theme: Setting dark theme because of URL override");
            changeTheme("dark", true);
        } else if (getURLvar("theme") == "light") {
            belchertown_debug("Theme: Setting light theme because of URL override");
            changeTheme("light", true);
        } else if (getURLvar("theme") == "auto") {
            belchertown_debug("Theme: Setting auto theme because of URL override");
            sessionStorage.setItem('theme', 'auto')
            if (config.almanac_times) {
                autoTheme(config.almanac_times.sunset_hour, config.almanac_times.sunset_minute, config.almanac_times.sunrise_hour, config.almanac_times.sunrise_minute);
            }
        }
    }

    if (extras.theme_toggle_enabled === '1') {
    // Dark mode checkbox toggle switcher
    try {
        document.getElementById('themeSwitch').addEventListener('change', function(event) {
            belchertown_debug("Theme: Toggle button changed");
            (event.target.checked) ? changeTheme("dark", true) : changeTheme("light", true);
        });
    } catch (err) {
        // Silently exit
    }
    }

    // After charts are loaded, if an anchor tag is in the URL, let's scroll to it
    jQuery(window).on('load', function() {
        var anchor_tag = location.hash.replace('#', '');
        if (anchor_tag != '') {
            // Scroll the webpage to the chart. The timeout is to let jQuery finish appending the outer div so the height of the page is completed.
            setTimeout(function() {
                jQuery('html, body').animate({scrollTop: jQuery('#' + anchor_tag).offset().top}, 500);
            }, 500);
        }
    });

    if (extras.back_to_top_button_enabled === '1') {
    // Back to Top Button is visible after 400px
    jQuery(window).scroll(function() {
        if (jQuery(this).scrollTop() > 400) {
            jQuery('#btn-back-to-top').css('transform', 'scale(1)');
        } else {
            jQuery('#btn-back-to-top').css('transform', 'scale(0)');
        }
    });

    jQuery('#btn-back-to-top').click(function() {
        jQuery("html, body").animate({
            scrollTop: 0
        }, 1000);
        return false;
    });

    if (extras.back_to_top_button_position === '1') {
    // Button is visible on left side
    jQuery('#btn-back-to-top').css('left','20px').css('right','auto');
    }

    if (extras.back_to_top_button_opacity >= '0.1' && extras.back_to_top_button_opacity <= '0.9') {
    jQuery('#btn-back-to-top').css('opacity',extras.back_to_top_button_opacity);
    }
    }

});

if (extras.theme === 'auto') {
// Run this on every page for dark mode if skin theme is auto
ajaxweewx().then(function(weewx_data) { // This call will make sure json/weewx_data.json is loaded before anything else
    update_weewx_data(weewx_data); // Initial call to update (date, daily high, low, etc)
    belchertown_debug(weewx_data); // Make weewx_data.json available in debugging console
}).catch(function(e) {
    console.log(e);
});
}

// Disable AJAX caching
jQuery.ajaxSetup({
    cache: false
});

// Get the URL variables. Source: https://stackoverflow.com/a/26744533/1177153
function getURLvar(k) {
    var p = {};
    location.search.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(s, k, v) {p[k] = v});
    return k ? p[k] : p;
}


// Change the color of the outTemp_F variable
function get_outTemp_color(unit, outTemp, returnColor = false) {
    outTemp = parseFloat(outTemp).toFixed(0); // Convert back to decimal literal
    if (unit == "degree_F") {
        if (outTemp <= 0) {
            var outTemp_color = "#1278c8";
        } else if (outTemp <= 25) {
            var outTemp_color = "#30bfef";
        } else if (outTemp <= 32) {
            var outTemp_color = "#1fafdd";
        } else if (outTemp <= 40) {
            var outTemp_color = "rgba(0,172,223,1)";
        } else if (outTemp <= 50) {
            var outTemp_color = "#71bc3c";
        } else if (outTemp <= 55) {
            var outTemp_color = "rgba(90,179,41,0.8)";
        } else if (outTemp <= 65) {
            var outTemp_color = "rgba(131,173,45,1)";
        } else if (outTemp <= 70) {
            var outTemp_color = "rgba(206,184,98,1)";
        } else if (outTemp <= 75) {
            var outTemp_color = "rgba(255,174,0,0.9)";
        } else if (outTemp <= 80) {
            var outTemp_color = "rgba(255,153,0,0.9)";
        } else if (outTemp <= 85) {
            var outTemp_color = "rgba(255,127,0,1)";
        } else if (outTemp <= 90) {
            var outTemp_color = "rgba(255,79,0,0.9)";
        } else if (outTemp <= 95) {
            var outTemp_color = "rgba(255,69,69,1)";
        } else if (outTemp <= 110) {
            var outTemp_color = "rgba(255,104,104,1)";
        } else if (outTemp >= 111) {
            var outTemp_color = "rgba(218,113,113,1)";
        }
    } else if (unit == "degree_C") {
        if (outTemp <= 0) {
            var outTemp_color = "#1278c8";
        } else if (outTemp <= -3.8) {
            var outTemp_color = "#30bfef";
        } else if (outTemp <= 0) {
            var outTemp_color = "#1fafdd";
        } else if (outTemp <= 4.4) {
            var outTemp_color = "rgba(0,172,223,1)";
        } else if (outTemp <= 10) {
            var outTemp_color = "#71bc3c";
        } else if (outTemp <= 12.7) {
            var outTemp_color = "rgba(90,179,41,0.8)";
        } else if (outTemp <= 18.3) {
            var outTemp_color = "rgba(131,173,45,1)";
        } else if (outTemp <= 21.1) {
            var outTemp_color = "rgba(206,184,98,1)";
        } else if (outTemp <= 23.8) {
            var outTemp_color = "rgba(255,174,0,0.9)";
        } else if (outTemp <= 26.6) {
            var outTemp_color = "rgba(255,153,0,0.9)";
        } else if (outTemp <= 29.4) {
            var outTemp_color = "rgba(255,127,0,1)";
        } else if (outTemp <= 32.2) {
            var outTemp_color = "rgba(255,79,0,0.9)";
        } else if (outTemp <= 35) {
            var outTemp_color = "rgba(255,69,69,1)";
        } else if (outTemp <= 43.3) {
            var outTemp_color = "rgba(255,104,104,1)";
        } else if (outTemp >= 43.4) {
            var outTemp_color = "rgba(218,113,113,1)";
        }
    }

    // Return the color value if requested, otherwise just set the div color
    if (returnColor) {
        return outTemp_color;
    } else {
        jQuery(".outtemp_outer").css("color", outTemp_color);
    }
}

// Change the color of the aqi variable according to US-EPA standards
// (adjusted to match skin colors better)
function get_aqi_color(aqi, returnColor = false) {
    if (aqi >= 301) {
        var aqi_color = "#cc241d";
    } else if (aqi >= 201) {
        var aqi_color = "#b16286";
    } else if (aqi >= 151) {
        var aqi_color = "rgba(255,69,69,1)";
    } else if (aqi >= 101) {
        var aqi_color = "rgba(255,127,0,1)";
    } else if (aqi >= 51) {
        var aqi_color = "rgba(255,174,0,0.9)";
    } else if (aqi < 51) {
        var aqi_color = "#71bc3c";
    }

    // Return the color value if requested, otherwise just set the div color
    if (returnColor) {
        return aqi_color;
    } else {
        jQuery(".aqi_outer").css("color", aqi_color);
    }
}

function kts_to_beaufort(windspeed) {
    // Given windspeed in knots, converts to Beaufort scale
    if (windspeed <= 1) {
        return 0
    } else if (windspeed <= 3) {
        return 1
    } else if (windspeed <= 6) {
        return 2
    } else if (windspeed <= 10) {
        return 3
    } else if (windspeed <= 15) {
        return 4
    } else if (windspeed <= 21) {
        return 5
    } else if (windspeed <= 27) {
        return 6
    } else if (windspeed <= 33) {
        return 7
    } else if (windspeed <= 40) {
        return 8
    } else if (windspeed <= 47) {
        return 9
    } else if (windspeed <= 55) {
        return 10
    } else if (windspeed <= 63) {
        return 11
    } else if (windspeed > 63) {
        return 12
    }
}

function beaufort_cat(beaufort) {
    // Given Beaufort number, returns category description
    switch (beaufort) {
        case 0:
            return labels.beaufort0
        case 1:
            return labels.beaufort1
        case 2:
            return labels.beaufort2
        case 3:
            return labels.beaufort3
        case 4:
            return labels.beaufort4
        case 5:
            return labels.beaufort5
        case 6:
            return labels.beaufort6
        case 7:
            return labels.beaufort7
        case 8:
            return labels.beaufort8
        case 9:
            return labels.beaufort9
        case 10:
            return labels.beaufort10
        case 11:
            return labels.beaufort11
        case 12:
            return labels.beaufort12
    }
}

function highcharts_tooltip_factory(obsvalue, point_obsType, highchartsReturn = false, rounding, mirrored = false, numberFormat) {
    // Mirrored values have the negative sign removed
    if (mirrored) {
        obsvalue = Math.abs(obsvalue);
    }

    if (point_obsType == "windDir") {
        if (obsvalue >= 0 && obsvalue <= 11.25) {
            ordinal = config.ordinate_names[0]; // N
        } else if (obsvalue >= 11.26 && obsvalue <= 33.75) {
            ordinal = config.ordinate_names[1]; // NNE
        } else if (obsvalue >= 33.76 && obsvalue <= 56.25) {
            ordinal = config.ordinate_names[2]; // NE
        } else if (obsvalue >= 56.26 && obsvalue <= 78.75) {
            ordinal = config.ordinate_names[3]; // ENE
        } else if (obsvalue >= 78.76 && obsvalue <= 101.25) {
            ordinal = config.ordinate_names[4]; // E
        } else if (obsvalue >= 101.26 && obsvalue <= 123.75) {
            ordinal = config.ordinate_names[5]; // ESE
        } else if (obsvalue >= 123.76 && obsvalue <= 146.25) {
            ordinal = config.ordinate_names[6]; // SE
        } else if (obsvalue >= 146.26 && obsvalue <= 168.75) {
            ordinal = config.ordinate_names[7]; // SSE
        } else if (obsvalue >= 168.76 && obsvalue <= 191.25) {
            ordinal = config.ordinate_names[8]; // S
        } else if (obsvalue >= 191.26 && obsvalue <= 213.75) {
            ordinal = config.ordinate_names[9]; // SSW
        } else if (obsvalue >= 213.76 && obsvalue <= 236.25) {
            ordinal = config.ordinate_names[10]; // SW
        } else if (obsvalue >= 236.26 && obsvalue <= 258.75) {
            ordinal = config.ordinate_names[11]; // WSW
        } else if (obsvalue >= 258.76 && obsvalue <= 281.25) {
            ordinal = config.ordinate_names[12]; // W
        } else if (obsvalue >= 281.26 && obsvalue <= 303.75) {
            ordinal = config.ordinate_names[13]; // WNW
        } else if (obsvalue >= 303.76 && obsvalue <= 326.25) {
            ordinal = config.ordinate_names[14]; // NW
        } else if (obsvalue >= 326.26 && obsvalue <= 348.75) {
            ordinal = config.ordinate_names[15]; // NNW
        } else if (obsvalue >= 348.76 && obsvalue <= 360) {
            ordinal = config.ordinate_names[0]; // N
        }

        // highchartsReturn returns the full wind direction string for highcharts tooltips. e.g "NNW (337)"
        if (highchartsReturn) {
            output = ordinal + " (" + Math.round(obsvalue) + "\xBA)";
        } else {
            output = ordinal;
        }
    } else {
        try {
            // Setup any graphs.conf overrides on formatting
            var {decimals, decimalPoint, thousandsSep} = numberFormat;

            // Try to apply the highcharts numberFormat for locale awareness. Use rounding from weewx.conf StringFormats.
            // -1 is set from Python to notate no rounding data available and decimals from graphs.conf is undefined.
            if (rounding == "-1" && typeof decimals === "undefined") {
                output = Highcharts.numberFormat(obsvalue);
            } else {
                // If the amount of decimal is defined, use that instead since rounding is provided to the function.
                if (typeof decimals !== "undefined") {
                    rounding = decimals;
                }
                // If decimalPoint is undefined, use the auto detect from the skin since this comes from the skin.
                if (typeof decimalPoint === "undefined") {
                    decimalPoint = config.highcharts_decimal;
                }
                // If thousandsSep is undefined, use the auto detect from the skin since this comes from the skin.
                if (typeof thousandsSep === "undefined") {
                    thousandsSep = config.highcharts_thousands;
                }

                output = Highcharts.numberFormat(obsvalue, rounding, decimalPoint, thousandsSep);
            }
        } catch (err) {
            // Fall back to just returning the highcharts point number value, which is a best guess.
            output = Highcharts.numberFormat(obsvalue);
        }
    }

    return output;
}

// Handle wind arrow rotation with the ability to "rollover" past 0 
// without spinning back around. e.g 350 to 3 would normally spin back around
// https://stackoverflow.com/a/19872672/1177153
function rotateThis(newRotation) {
    if (newRotation == "N/A") {return;}
    belchertown_debug("rotateThis: rotating to " + newRotation);
    var currentRotation;
    finalRotation = finalRotation || 0; // if finalRotation undefined or 0, make 0, else finalRotation
    currentRotation = finalRotation % 360;
    if (currentRotation < 0) {currentRotation += 360;}
    if (currentRotation < 180 && (newRotation > (currentRotation + 180))) {finalRotation -= 360;}
    if (currentRotation >= 180 && (newRotation <= (currentRotation - 180))) {finalRotation += 360;}
    finalRotation += (newRotation - currentRotation);
    jQuery(".wind-arrow").css("transform", "rotate(" + finalRotation + "deg)");
    jQuery(".arrow").css("transform", "rotate(" + finalRotation + "deg)");
}

// Title case strings. https://stackoverflow.com/a/45253072/1177153
function titleCase(str) {
    return str.toLowerCase().split(' ').map(function(word) {
        return word.replace(word[0], word[0].toUpperCase());
    }).join(' ');
}

async function ajaxweewx() {
    resp = await fetch(get_relative_url() + "/json/weewx_data.json");
    if (!resp.ok) {
        throw new Error("HTTP error! Unable to load weewx_data.json");
    } else {
        return await resp.json();
    }
}

// Update weewx data elements
//var station_obs_array = "";
var unit_rounding_array = "";
var unit_label_array = "";
var weewx_data = "";
function update_weewx_data(data) {
    belchertown_debug("Updating weewx data");
    weewx_data = data;
    
    if (extras.theme === 'auto') {
    // Auto theme if enabled
    autoTheme(data["almanac"]["sunset_hour"], data["almanac"]["sunset_minute"], data["almanac"]["sunrise_hour"], data["almanac"]["sunrise_minute"]);
    }

    //station_obs_array = data["station_observations"];
    unit_rounding_array = data["unit_rounding"];
    unit_label_array = data["unit_label"];

    // Daily High Low
    high = data["day"]["outTemp"]["max"];
    low = data["day"]["outTemp"]["min"];
    jQuery(".high").html(high);
    jQuery(".low").html(low);

    try {
        // Barometer trending by finding a negative number
        count = (data["current"]["barometer_trend"].match(/-/g) || []).length
    } catch (err) {
        // Returned "current" data does not have this value
    }

    if (count >= 1) {
        jQuery(".pressure-trend").html('<i class="fa fa-arrow-down barometer-down"></i>');
    } else {
        jQuery(".pressure-trend").html('<i class="fa fa-arrow-up barometer-up"></i>');
    }

    // Daily max gust span
    jQuery(".dailymaxgust").html(parseFloat(data["day"]["wind"]["max"]).toFixed(1));

    // Daily Snapshot Stats Section
    try {
        jQuery(".snapshot-records-today-header").html(tzAdjustedMoment(data["current"]["epoch"]).format(labels.time_snapshot_records_today_header));
        jQuery(".snapshot-records-month-header").html(tzAdjustedMoment(data["current"]["epoch"]).format(labels.time_snapshot_records_month_header));
    } catch (err) {
        // Returned "current" data does not have this value
    }


    jQuery(".dailystatshigh").html(data["day"]["outTemp"]["max"]);
    jQuery(".dailystatslow").html(data["day"]["outTemp"]["min"]);
    jQuery(".dailystatswindavg").html(data["day"]["wind"]["average"]);
    jQuery(".dailystatswindmax").html(data["day"]["wind"]["max"]);
    jQuery(".dailystatsrain").html(data["day"]["rain"]["sum"]);
    jQuery(".dailystatsrainrate").html(data["day"]["rain"]["max"]);
    jQuery(".dailywindrun").html(data["day"]["wind"]["windrun"]);

    // Month Snapshot Stats Section
    jQuery(".monthstatshigh").html(data["month"]["outTemp"]["max"]);
    jQuery(".monthstatslow").html(data["month"]["outTemp"]["min"]);
    jQuery(".monthstatswindavg").html(data["month"]["wind"]["average"]);
    jQuery(".monthstatswindmax").html(data["month"]["wind"]["max"]);
    jQuery(".monthstatsrain").html(data["month"]["rain"]["sum"]);
    jQuery(".monthstatsrainrate").html(data["month"]["rain"]["max"]);

    // Sunrise and Sunset            
    jQuery(".sunrise-value").html(tzAdjustedMoment(parseFloat(data["almanac"]["sunrise_epoch"]).toFixed(0)).format(labels.time_sunrise));
    jQuery(".sunset-value").html(tzAdjustedMoment(parseFloat(data["almanac"]["sunset_epoch"]).toFixed(0)).format(labels.time_sunset));
    jQuery(".moonrise-value").html(tzAdjustedMoment(parseFloat(data["almanac"]["moon"]["moon_rise_epoch"]).toFixed(0)).format(labels.time_sunrise));
    jQuery(".moonset-value").html(tzAdjustedMoment(parseFloat(data["almanac"]["moon"]["moon_set_epoch"]).toFixed(0)).format(labels.time_sunrise));

    // Moon icon, phase and illumination percent
    jQuery(".moon-icon").html(moon_icon(data["almanac"]["moon"]["moon_index"]));        
    jQuery(".moon-phase").html(titleCase(data["almanac"]["moon"]["moon_phase"])); // Javascript function above
    jQuery(".moon-visible").html("<strong>" + data["almanac"]["moon"]["moon_fullness"] + "%</strong> " + labels.moon_visible);
    if (config.almanac_has_extras) {
    // Close current modal if open
    jQuery('#almanac').modal('hide');
    jQuery(".almanac-extras-modal-body").html(data["almanac"]["almanac_extras_modal_html"]);
    try {
        almanac_updated = labels.header_last_updated + " " + tzAdjustedMoment(data["current"]["datetime_raw"]).format(labels.time_last_updated);
        jQuery(".almanac_last_updated").html(almanac_updated);
    } catch (err) {
        // Returned "current" data does not have this value
    }
    }
}

//  function returns html for moon-icon according to moonphase value and currentTheme setting
function moon_icon(moonphase){
    
    var moon_icon_dict = {
        "0": "<div class='wi wi-moon-new'></div>",
        "1": "<div class='wi wi-moon-waxing-crescent-3 " + config.hemisphere + "'></div>",
        "2": "<div class='wi wi-moon-first-quarter " + config.hemisphere + "'></div>",
        "3": "<div class='wi wi-moon-waxing-gibbous-3 " + config.hemisphere + "'></div>",
        "4": "<div class='wi wi-moon-full'></div>",
        "5": "<div class='wi wi-moon-waning-gibbous-3 " + config.hemisphere + "'></div>",
        "6": "<div class='wi wi-moon-third-quarter " + config.hemisphere + "'></div>",
        "7": "<div class='wi wi-moon-waning-crescent-4 " + config.hemisphere + "'></div>",
    }
    
    var output = moon_icon_dict[moonphase];
    if (sessionStorage.getItem('currentTheme') === 'dark') {
        return output;
    } else {
        return output.replace('-moon-','-moon-alt-');
    }
}

function tzAdjustedMoment(input) {
    let tz = config.moment_js_tz;
    if (!tz) {
        return dayjs.unix(Number(input)).utcOffset(config.moment_js_utc_offset);
    } else {
        return dayjs.unix(Number(input)).tz(tz);
    }
}
