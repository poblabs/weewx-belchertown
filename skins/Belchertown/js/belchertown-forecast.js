// Forecast (only called when forecast_enabled = 1). json/forecast.json is written by
// bin/user/belchertown_forecast.py in the same format for every provider.
function ajaxforecast() {
    jQuery.getJSON(get_relative_url() + "/json/forecast.json", update_forecast_data);
}

function aqi_category_label(category) {
    return {
        "good": labels.aqi_good,
        "moderate": labels.aqi_moderate,
        "usg": labels.aqi_usg,
        "unhealthy": labels.aqi_unhealthy,
        "very unhealthy": labels.aqi_very_unhealthy,
        "hazardous": labels.aqi_hazardous
    }[category] || labels.aqi_unknown;
}

function show_forcast_alert(data) {
    var i, forecast_alert_modal = "", forecast_alerts = [];

    // Empty anything that's been appended to the modal from the previous run
    jQuery(".wx-stn-alert-text").empty();

    (data["alerts"] || []).forEach(function(alert) {
        forecast_alerts.push({
            "title": alert["title"],
            "body": alert["body"].replace(/\n/g, '<br>'),
            "link": alert["type"],
            "expires": tzAdjustedMoment(alert["expires"]).format(labels.time_forecast_alert_expires)
        });
    });


    if (forecast_alerts.length > 0) {
        belchertown_debug("Forecast: There are " + forecast_alerts.length + " alert(s).");
        for (i = 0; i < forecast_alerts.length; i++) {

            alert_link = "<i class='fa fa-exclamation-triangle'></i> <a href='#forecast-alert-" + i + "' data-toggle='modal' data-target='#forecast-alert-" + i + "'>" + forecast_alerts[i]["title"] + " " + labels.alert_in_effect + " " + forecast_alerts[i]["expires"] + "</a><br>";
            jQuery(".wx-stn-alert-text").append(alert_link);

            forecast_alert_modal += "<!-- Forecast Alert Modal " + i + " -->";
            forecast_alert_modal += "<div class='modal fade' id='forecast-alert-" + i + "' tabindex='-1' role='dialog' aria-labelledby='forecast-alert'>";
            forecast_alert_modal += "<div class='modal-dialog' role='document'>";
            forecast_alert_modal += "<div class='modal-content'>";
            forecast_alert_modal += "<div class='modal-header'>";
            forecast_alert_modal += "<button type='button' class='close' data-dismiss='modal' aria-label='Close'><span aria-hidden='true'>&times;</span></button>";
            forecast_alert_modal += "<h4 class='modal-title' id='forecast-alert'>" + forecast_alerts[i]["title"] + "</h4>";
            forecast_alert_modal += "</div>";
            forecast_alert_modal += "<div class='modal-body'>";
            forecast_alert_modal += forecast_alerts[i]["body"];
            forecast_alert_modal += "</div>";
            forecast_alert_modal += "<div class='modal-footer'>";
            forecast_alert_modal += "<button type='button' class='btn btn-primary' data-dismiss='modal'>" + labels.close + "</button>";
            forecast_alert_modal += "</div>";
            forecast_alert_modal += "</div>";
            forecast_alert_modal += "</div>";
            forecast_alert_modal += "</div>";

            jQuery(".wx-stn-alert-text").append(forecast_alert_modal);
        }
        jQuery(".wx-stn-alert").show();
    } else {
        belchertown_debug("Forecast: There are no forecast alerts");
        jQuery(".wx-stn-alert").hide();
    }
}

function update_forecast_data(data) {
    belchertown_debug("Forecast: Updating data from " + data["provider"]);
    belchertown_debug(data);

    if (extras.forecast_provider == "N/A") {
        jQuery(".forecastrow").hide();
        belchertown_debug("Forecast: No provider, hiding forecastrow");
        return;
    }

    var forecast_subtitle = tzAdjustedMoment(data["timestamp"]).format(labels.time_forecast_last_updated);
    var current = data["current"] || {};
    var wxicon = current["icon"] ? get_relative_url() + "/images/" + current["icon"] + ".png" : "";

    // Current observation text
    if (current["text"]) {
        jQuery(".current-obs-text").html(current["text"]);
    }

    // AQI
    var aqi = data["aqi"];
    if (aqi && aqi["value"] !== "No Data") {
        jQuery(".wx-aqi").html(aqi["value"]);
        jQuery(".wx-aqi-category").html(aqi_category_label(aqi["category"]));
        if (extras.aqi_location_enabled === "1") jQuery(".aqi_location_outer").html("<br>" + aqi["place"]).css('textTransform', 'capitalize');
        get_aqi_color(aqi["value"]);
        jQuery(".station-observations .aqi").html(aqi["value"]);
    } else if (aqi) {
        jQuery(".wx-aqi").html("No Data");
        jQuery(".wx-aqi-category").html(aqi_category_label(""));
        if (extras.aqi_location_enabled === "1") jQuery(".aqi_location_outer").html("");
        jQuery(".station-observations .aqi").html("No Data");
    }

    // Visibility text in station observation table
    if (current["visibility"] != null) {
        try {
            visibility_output = parseFloat(current["visibility"]).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["visibility"], maximumFractionDigits: unit_rounding_array["visibility"]}) + " " + unit_label_array["visibility"];
            jQuery(".station-observations .visibility").html(visibility_output);
        } catch (err) {
            // Visibility not in the station observation table or any of the unit arrays
        }
    }

    var periods_for = {"forecast_1hr": "hourly", "forecast_3hr": "three_hourly", "forecast_24hr": "daily"};
    var forecast_interval;
    for (forecast_interval of ["forecast_1hr", "forecast_3hr", "forecast_24hr"]) {
        var forecast_row = [];
        var output_html = "";
        var periods = data[periods_for[forecast_interval]] || [];
        for (i = 0; i < periods.length; i++) {
            var p = periods[i];
            var image_url = get_relative_url() + "/images/" + p["icon"] + ".png";
            var condition_text = p["text"];
            //  for 24hr interval add 7200 (2 hours) to the epoch to get an hour well into the day to avoid any DST issues. This way it'll either be 1am or 2am. Without it, we get 12am or 11pm (the previous day).
            var day_time = forecast_interval == "forecast_24hr" ? p["time"] + 7200 : p["time"];
            var weekday = tzAdjustedMoment(day_time).format(forecast_interval == "forecast_24hr" ? labels.time_forecast_date : labels.time_forecast_time);

            var avgTemp = p["temp_avg"];
            var minTemp = p["temp_min"];
            var maxTemp = p["temp_max"];
            var dewPoint = p["dewpoint"];

            //  for 1hr interval determine temperature range, set to a minimum value of 2; also avoids div by zero
            if (forecast_interval == "forecast_1hr") {
                if (i == 0) {
                    var lowTemp = avgTemp;
                    var highTemp = avgTemp;
                } else {
                    if (lowTemp > avgTemp) lowTemp = avgTemp;
                    if (highTemp < avgTemp) highTemp = avgTemp;
                }
            }

            // Stations that show knots or Beaufort get the forecast wind the same way
            if (config.unit_type.windSpeed == "knot") {
                var windSpeed = p["wind_kts"];
                var windGust = p["gust_kts"];
            } else if (config.unit_type.windSpeed == "beaufort") {
                var windSpeed = kts_to_beaufort(p["wind_kts"]);
                var windGust = kts_to_beaufort(p["gust_kts"]);
            } else {
                var windSpeed = p["wind"];
                var windGust = p["gust"];
            }

            var precip = p["pop"] || 0;
            var humidity = p["humidity"];
            var snow_depth = p["snow"] || 0;
            var snow_unit = data["units"]["snow"];

            var link_day = tzAdjustedMoment(day_time);
            var forecast_link_setup = extras.forecast_daily_forecast_link.replace("YYYY", link_day.format("YYYY")).replace("MM", link_day.format("MM")).replace("DD", link_day.format("DD"));
            var forecast_link = '<a href="' + forecast_link_setup + '" target="_blank">' + labels.daily_forecast + '</a>';

            forecast_row.push({
                "weekday": weekday,
                "image_url": image_url,
                "condition_text": condition_text,
                "avgTemp": avgTemp,
                "minTemp": minTemp,
                "maxTemp": maxTemp,
                "windSpeed": windSpeed,
                "windGust": windGust,
                "snow_depth": snow_depth,
                "snow_unit": snow_unit,
                "precip": precip,
                "humidity": humidity,
                "dewPoint": dewPoint,
                "forecast_link": forecast_link
            });
        }


            //  Create individual forecast rows
            if (forecast_interval == "forecast_1hr") {
                //  set temperature range and offset to centralise output
                var rangeTemp = highTemp - lowTemp;
                var offset = 0;
                if (highTemp - lowTemp < 2) {
                    rangeTemp = 2;
                    if (highTemp - lowTemp == 0) offset = 1; //sets the only value 1/2 way down
                    else if (highTemp - lowTemp == 1) offset = 0.67;  //sets the top value 1/3 way down
                }
                // Build 1 hour forecast row
                for (i = 0; i < forecast_row.length; i++) {
                    if (i == 0) {
                        output_html += '<div class="col-sm-1-5 forecast-day forecast-1hour forecast-today">';
                    } else {
                        output_html += '<div class="col-sm-1-5 forecast-day forecast-1hour border-left">';
                    }
                    output_html += '<span id="weekday">' + forecast_time(i, forecast_interval, forecast_row[i]["weekday"]) + '</span>';
                    output_html += '<br>';
                    output_html += '<div class="forecast-conditions"';
                    if (extras.forecast_show_humidity_dewpoint > '0') {
                    output_html += ' style="min-height:155px">'
                    output_html += '<div class="forecast-temp-graph" style="padding-top:';
                    //  padding = ( ( highTemp - forecast_row[i]["avgTemp"] = offset ) * 76 / ( rangeTemp) ) where 100 ~ max calculated space available for padding
                    output_html += parseInt((highTemp - forecast_row[i]["avgTemp"] + offset) * 76 / (rangeTemp)) + 'px';
                    output_html += '; height:155px">'
                    } else {
                    output_html += '>'
                    output_html += '<div class="forecast-temp-graph" style="padding-top:';
                    //  padding = ( ( highTemp - forecast_row[i]["avgTemp"] = offset ) * 100 / ( rangeTemp) ) where 100 ~ max calculated space available for padding
                    output_html += parseInt((highTemp - forecast_row[i]["avgTemp"] + offset) * 100 / (rangeTemp)) + 'px">';
                    }
                    output_html += '<div class="forecast-image">';
                    output_html += '<img id="icon" src="' + forecast_row[i]["image_url"] + '">';
                    output_html += '</div>';
                    output_html += parseFloat(forecast_row[i]["avgTemp"]).toFixed(0) + '&deg;</div>';
                    output_html += '</div>';
                    //  output_html += '<br>';
                    output_html += '<div class="forecast-precip">';
                    if (extras.forecast_show_humidity_dewpoint === '1') {
                    output_html += '<div><i class="wi wi-humidity rain-precip"></i> <span>' + parseFloat(forecast_row[i]["humidity"]).toFixed(0) + '%</span></div>';
                    } else if (extras.forecast_show_humidity_dewpoint === '2') {
                    output_html += '<div><i class="wi wi-raindrops rain-precip"></i> <span>' + parseFloat(forecast_row[i]["dewPoint"]).toFixed(0) + '&deg;</span></div>';
                    }
                    if (forecast_row[i]["snow_depth"] > 0) {
                        output_html += '<div class="snow-precip">';
                        // output_html += '<img src="'+get_relative_url()+'/images/snowflake-icon-15px.png"> <span>';
                        output_html += '<img src="' + get_relative_url() + '/images/snowflake-icon-15px.png"> <span>' + parseFloat(forecast_row[i]["snow_depth"]).toFixed(0) + '<span> ' + forecast_row[i]["snow_unit"];
                        output_html += '</div>';
                    } else if (forecast_row[i]["precip"] > 0) {
                        output_html += '<i class="wi wi-raindrop wi-rotate-45 rain-precip"></i> <span>' + parseFloat(forecast_row[i]["precip"]).toFixed(0) + '%</span>';
                    } else {
                        output_html += '<i class="wi wi-raindrop wi-rotate-45 rain-no-precip"></i> <span>0%</span>';
                    }
                    output_html += '</div>';
                    output_html += '<div class="forecast-wind">';
                    output_html += '<i class="wi wi-strong-wind"></i> <span>' + parseFloat(forecast_row[i]["windSpeed"]).toFixed(0) + '</span>';
                    //  output_html += '<i class="wi wi-strong-wind"></i> <span>'+ parseFloat( forecast_row[i]["windSpeed"] ).toFixed(0) +'</span> | <span> '+ parseFloat( forecast_row[i]["windGust"] ).toFixed(0) +'$unit.label.windSpeed';        
                    output_html += '</div>';
                    if (extras.forecast_show_daily_forecast_link === '1') {
                    output_html += forecast_row[i]["forecast_link"];
                    }
                    output_html += '</div>';
                }
            } else {

                // Build 3 or 24 hour forecast rows
                for (i = 0; i < forecast_row.length; i++) {
                    if (forecast_interval == "forecast_3hr") {
                        if (i == 0) {
                            output_html += '<div class="col-sm-1-5 forecast-day forecast-3hour forecast-today">';
                        } else {
                            output_html += '<div class="col-sm-1-5 forecast-day forecast-3hour border-left">';
                        }
                    } else if (forecast_interval == "forecast_24hr") {
                        if (i == 0) {
                            output_html += '<div class="col-sm-1-5 forecast-day forecast-24hour forecast-today">';
                        } else {
                            output_html += '<div class="col-sm-1-5 forecast-day forecast-24hour border-left">';
                        }
                    }
                    output_html += '<span id="weekday">' + forecast_time(i, forecast_interval, forecast_row[i]["weekday"]) + '</span>';
                    output_html += '<br>';
                    output_html += '<div class="forecast-conditions">';
                    output_html += '<img id="icon" src="' + forecast_row[i]["image_url"] + '">';
                    output_html += '<br>';
                    output_html += '<span class="forecast-condition-text">' + forecast_row[i]["condition_text"] + '</span>';
                    output_html += '</div>';
                    output_html += '<span class="forecast-high">' + parseFloat(forecast_row[i]["maxTemp"]).toFixed(0) + '&deg;</span> | <span class="forecast-low">' + parseFloat(forecast_row[i]["minTemp"]).toFixed(0) + '&deg;</span>';
                    output_html += '<br>';
                    output_html += '<div class="forecast-precip">';
                    if (extras.forecast_show_humidity_dewpoint === '1') {
                    output_html += '<i class="wi wi-humidity rain-precip"></i> <span>' + parseFloat(forecast_row[i]["humidity"]).toFixed(0) + '%</span> | ';
                    } else if (extras.forecast_show_humidity_dewpoint === '2') {
                    output_html += '<i class="wi wi-raindrops rain-precip"></i> <span>' + parseFloat(forecast_row[i]["dewPoint"]).toFixed(0) + '&deg;</span> | ';
                    }
                    if (forecast_row[i]["snow_depth"] > 0) {
                        output_html += '<div class="snow-precip">';
                        output_html += '<img src="' + get_relative_url() + '/images/snowflake-icon-15px.png"> <span>' + parseFloat(forecast_row[i]["snow_depth"]).toFixed(0) + '<span> ' + forecast_row[i]["snow_unit"];
                        output_html += '</div>';
                    } else if (forecast_row[i]["precip"] > 0) {
                        output_html += '<i class="wi wi-raindrop wi-rotate-45 rain-precip"></i> <span>' + parseFloat(forecast_row[i]["precip"]).toFixed(0) + '%</span>';
                    } else {
                        output_html += '<i class="wi wi-raindrop wi-rotate-45 rain-no-precip"></i> <span>0%</span>';
                    }
                    output_html += '</div>';
                    output_html += '<div class="forecast-wind">';
                    output_html += '<i class="wi wi-strong-wind"></i> <span>' + parseFloat(forecast_row[i]["windSpeed"]).toFixed(0) + '</span> | <span> ' + parseFloat(forecast_row[i]["windGust"]).toFixed(0) + config.unit_label.windSpeed;
                    output_html += '</div>';
                    if (extras.forecast_show_daily_forecast_link === '1') {
                    output_html += forecast_row[i]["forecast_link"];
                    }
                    output_html += '</div>';
                }
            }

            // Show the forecasts rows
            if (forecast_interval == "forecast_1hr") {
                jQuery(".1hr_forecasts").html(output_html);
                belchertown_debug("html_1hr: " + output_html);
            } else if (forecast_interval == "forecast_3hr") {
                jQuery(".3hr_forecasts").html(output_html);
                belchertown_debug("html_3hr: " + output_html);
            } else if (forecast_interval == "forecast_24hr") {
                jQuery(".24hr_forecasts").html(output_html);
                belchertown_debug("html_24hr: " + output_html);
            }
            // Show the forecast_subtitle
            jQuery(".forecast-subtitle").html(labels.forecast_last_updated + " " + forecast_subtitle);
        }


    if (extras.forecast_alert_enabled === '1') {
        // Show weather alert
        show_forcast_alert(data);
    }

    // WX icon in temperature box
    if (wxicon) {
        jQuery("#wxicon").attr("src", wxicon);
    }
}

//  function to display selected forecast according to value of interval (1, 3 or 24); 0 hides all forecasts
function forecast_select(interval) {
        if (interval == 0) {
            jQuery(".forecastrow").hide();
        } else {
            oldinterval = sessionStorage.getItem("forecastInterval");
            if (interval != oldinterval) {
                //  hide the old forecast
                var forecast = document.getElementById((oldinterval + "hour-selected-forecast"));
                var button = document.getElementById(("button" + oldinterval));
                if (forecast != null) forecast.style.display = "none";
                if (button != null) button.style.borderStyle = "hidden";
                //  display the new forecast and store its interval value
                forecast = document.getElementById((interval + "hour-selected-forecast"));
                button = document.getElementById(("button" + interval));
                if (forecast != null) forecast.style.display = "block";
                if (button != null) button.style.borderStyle = "solid";
                sessionStorage.setItem("forecastInterval", interval);
            }
        }
    }

function forecast_default(interval) {
        sessionStorage.setItem("defaultInterval", interval);
    }

//  function adjusts daytime format for forecast_1hr & _3hr; assumes "ddd LT" format for daytime
function forecast_time(i, interval, daytime) {
    if ((daytime.indexOf(" ") == -1) || (interval == "forecast_24hr")) return daytime;
    var output = daytime
    var strday = daytime.substr(0, daytime.indexOf(" "));
    var strtime = daytime.substr(daytime.indexOf(" ") + 1);
    if (interval == "forecast_1hr") {
        if ((i == 0) || (strtime == "00:00") || (strtime == "12:00 AM")) {
            output = strtime + "<br>" + strday;
        } else {
            output = strtime + "<br>";
        }
    } else if (interval == "forecast_3hr") {
        if ((i != 0) && ((strtime > "02:59") || (strtime > "02:59 AM"))) {
            output = strtime;
        }
    }
    return output;
}
