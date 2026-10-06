//============================================//
// Live website using MQTT Websockets         //
// (only called when mqtt_websockets_enabled = 1)
//============================================//

var mqttConnected = false;

function ajaximages(section = false, reload_timer_interval_seconds = false) {
    // This function only runs if the elements have an img src.
    // Update images within the specific section
    if (!section || section == "radar") {
        belchertown_debug("Updating radar image");
    // Reload images
        if (document.querySelectorAll(".radar-map img").length > 0) {
            var radar_img = document.querySelectorAll(".radar-map img")[0].src;
            var new_radar_img = radar_img + "&t=" + Math.floor(Math.random() * 999999999);
            document.querySelectorAll(".radar-map img")[0].src = new_radar_img;
            //var radar_html = jQuery('.radar-map').children('img').attr('src').split('?')[0] // Get the img src and remove everything after "?" so we don't stack ?'s onto the image during updates
            //jQuery('.radar-map').children('img').attr('src', radar_html + "?" + Math.floor(Math.random() * 999999999));
        }
        // Reload iframe - https://stackoverflow.com/a/4249946/1177153
        if (document.querySelectorAll(".radar-map iframe").length > 0) {
            jQuery(".radar-map iframe").each(function() {
                jQuery(this).attr('src', function(i, val) {return val;});
            });
        }
        } else if (!section || section != "radar") {
        belchertown_debug("Updating " + section + " images");
        // Reload images
        jQuery('.' + section + ' img').each(function() {
            new_image_url = jQuery(this).attr('src').split('?')[0] + "?" + Math.floor(Math.random() * 999999999);
            jQuery(this).attr('src', new_image_url);
        });
        // Reload iframes
        jQuery('.' + section + ' iframe').each(function() {
            jQuery(this).attr('src', function(i, val) {return val;});
        });
    }
    // Set the new timer
    if (reload_timer_interval_seconds) {
        var reload_timer_ms = reload_timer_interval_seconds * 1000; // convert to millis
        setTimeout(function() {ajaximages(section, reload_timer_interval_seconds);}, reload_timer_ms);
    }
}

var reconnect_using_inactive_timestamp = false;
var inactive_timestamp = "";

// MQTT connect
function connect() {
    if (reconnect_using_inactive_timestamp) {
            updated = tzAdjustedMoment(inactive_timestamp).format(labels.time_last_updated);
        } else {
            updated = tzAdjustedMoment(config.current_datetime_raw).format(labels.time_last_updated);
        }
    reported = labels.mqtt_websockets_connecting + " " + labels.header_last_updated + " " + updated;
    jQuery(".updated").html(reported);
    jQuery(".onlineMarker").hide();
    jQuery(".offlineMarker").hide();
    jQuery(".loadingMarker").show();

    // A wall display (?view=kiosk) can use its own broker settings, e.g. a broker on the same network
    if (is_kiosk_view() && extras.mqtt_websockets_host_kiosk) {
        var host = extras.mqtt_websockets_host_kiosk;
        var port = config.mqtt_websockets_port_kiosk;
        var useSSL = config.mqtt_websockets_ssl_kiosk === '1';
    } else {
        var host = extras.mqtt_websockets_host;
        var port = extras.mqtt_websockets_port;
        var useSSL = extras.mqtt_websockets_ssl === '1';
    }
    belchertown_debug("MQTT: Connecting to MQTT Websockets: " + host + " " + port + (useSSL ? " (SSL Enabled)" : " (SSL Disabled)"));
    client = new Paho.Client(host, Number(port), mqttclient);
    client.onConnectionLost = onConnectionLost;
    client.onMessageArrived = onMessageArrived;
    var options = {
        useSSL: useSSL,
        // mqttVersion: 4 is spec MQTTv3.1.1 - mqttVersion: 3 is spec MQTTv3.1
        mqttVersion: 4,
        // If mqttVersionExplicit is true, it will force the connection to use the selected MQTT Version or will fail to connect.
        // If mqttVersionExplicit is false and mqttVersion is 4, it will try mqttVersion: 4 and if it fails it will fallback to mqttVersion: 3
        // Here's the relevant code: https://github.com/eclipse/paho.mqtt.javascript/blob/f5859463aba9a9b7c19f99ab7c4849a723f8d832/src/paho-mqtt.js#L1610
        mqttVersionExplicit: false,
        reconnect: true,
        onSuccess: onConnect,
        onFailure: onFailure
    }
    if (extras.mqtt_websockets_username && extras.mqtt_websockets_password) {
        options.userName = extras.mqtt_websockets_username;
        options.password = extras.mqtt_websockets_password;
    }
    client.connect(options);
}

// MQTT connect callback
function onConnect() {
    mqttConnected = true;
    belchertown_debug("MQTT: MQTT Connected. Subscribing.");
    if (reconnect_using_inactive_timestamp) {
        updated = tzAdjustedMoment(inactive_timestamp).format(labels.time_last_updated);
    } else {
        updated = tzAdjustedMoment(config.current_datetime_raw).format(labels.time_last_updated);
    }
    reported = labels.mqtt_websockets_waiting + " " + labels.header_last_updated + " " + updated;
    jQuery(".updated").html(reported);
    jQuery(".onlineMarker").hide();
    jQuery(".offlineMarker").hide();
    jQuery(".loadingMarker").show();
    client.subscribe(extras.mqtt_websockets_topic);
    if (extras.disconnect_live_website_visitor !== undefined && extras.disconnect_live_website_visitor !== '0') {
    if (getURLvar("stayconnected") && (getURLvar("stayconnected") == "true" || getURLvar("stayconnected") == "1")) {
        belchertown_debug("MQTT: stayconnected URL var found: ignoring disconnect_live_website_visitor value");
    } else {
        if (is_kiosk_view()) {
            belchertown_debug("MQTT: kiosk view stays connected; ignoring disconnect_live_website_visitor");
        }
        else {
            var activityTimeout = setTimeout(inactive, Number(extras.disconnect_live_website_visitor)); // Stop automatic ajax refresh
        }
    }
    }
}

// MQTT Failure
function onFailure() {
    mqttConnected = false;
    jQuery(".onlineMarker").hide();
    jQuery(".offlineMarker").show();
    jQuery(".loadingMarker").hide();
    var d = new Date();
    epoch = parseFloat((d / 1000)).toFixed(0); // Convert millis to seconds
    if (client.isConnected()) {
        updated = tzAdjustedMoment(epoch).format(labels.time_last_updated);
    } else {
        updated = tzAdjustedMoment(config.current_datetime_raw).format(labels.time_last_updated);
    }
    jQuery(".updated").html(labels.mqtt_websockets_failed + " " + labels.header_last_updated + " " + updated);
    console.log("MQTT: " + tzAdjustedMoment(epoch).format() + ": Cannot connect to MQTT broker");
}

// MQTT connection lost
function onConnectionLost(responseObject) {
    mqttConnected = false;
    jQuery(".onlineMarker").hide();
    jQuery(".offlineMarker").show();
    jQuery(".loadingMarker").hide();
    var d = new Date();
    epoch = parseFloat((d / 1000)).toFixed(0);  // Convert millis to seconds
    if (client.isConnected()) {
        updated = tzAdjustedMoment(epoch).format(labels.time_last_updated);
    } else {
        updated = tzAdjustedMoment(config.current_datetime_raw).format(labels.time_last_updated);
    }
    jQuery(".updated").html(labels.mqtt_websockets_lost + " " + labels.header_last_updated + " " + updated);
    if (responseObject.errorCode !== 0) {
        console.log("MQTT: " + tzAdjustedMoment(epoch).format() + ": mqtt Connection Lost: " + responseObject.errorMessage);
    }
}

function inactive() {
    client.disconnect(); // Disconnect mqtt
    belchertown_debug("MQTT: Inactive timer expired. MQTT Disconnected");
    jQuery(".onlineMarker").hide(); // Hide online beacon
    jQuery(".offlineMarker").show(); // Show offline beacon
    jQuery(".loadingMarker").hide(); // Hide loading beacon
    var d = new Date();
    epoch = parseFloat((d / 1000)).toFixed(0);  // Convert millis to seconds
    updated = tzAdjustedMoment(epoch).format(labels.time_last_updated);
    jQuery(".updated").html(labels.mqtt_websockets_stopped + " " + labels.header_last_updated + " " + updated + " <button type='button' class='btn btn-primary restart-interval'>" + labels.mqtt_websockets_continue + "</button>");
    reconnect_using_inactive_timestamp = true; // Set a flag to use the inactive timestamp in case we reconnect we have the latest last updated time
    inactive_timestamp = epoch; // Store this timestamp in case we reconnect
}

var mqtt_payload = "";
// New message from mqtt, process it
function onMessageArrived(message) {
    belchertown_debug("MQTT: " + message.payloadString);
    update_current_wx(message.payloadString);
    mqtt_payload = jQuery.parseJSON(message.payloadString);
}

function refreshHooks() {
    // Empty function for hooks to extend/re-use
    //belchertown_debug(mqtt_payload);
}

// Handle MQTT message
function update_current_wx(data) {
    data = jQuery.parseJSON(data);

    try {
        refreshHooks();
    } catch (e) {
    }
    
    if (extras.googleAnalyticsId !== undefined) {
    // Send a pageview
    gtag('config', extras.googleAnalyticsId);
    }

    // This message is a weewx archive update. Update weewx data, forecast data and highcharts graphs
    if (data.hasOwnProperty("interval_minute")) {
        // Delays are recommended to allow the other skins to complete processing
        belchertown_debug("MQTT: MQTT message indicates this is an archive interval.");
        if (!home_charts_shown()) {
            belchertown_debug("Skipping chart update, no charts on this page.");
        }
        else {
            setTimeout(showChart, 30000, homepage_graphgroup); // Load updated charts.
        }
        ajaxweewx().then(function(weewx_data) { // This call will make sure json/weewx_data.json is loaded before anything else
            setTimeout(update_weewx_data.bind(null, weewx_data), 10000); // Initial call to update (date, daily high, low, etc)
            setTimeout(belchertown_debug.bind(null, weewx_data), 10000); // Make weewx_data.json available in debugging console
        if (extras.forecast_enabled === '1') {
            setTimeout(ajaxforecast, 10000); // Update forecast data
        }
        }).catch(function(e) {
            console.log(e);
        });
    } else {
        // Only show the updated time on non-archive packets
        epoch = parseFloat(data["dateTime"]).toFixed(0);
        updated = tzAdjustedMoment(epoch).format(labels.time_last_updated);
        updated_text = labels.mqtt_websockets_connected + " " + updated;
        jQuery(".updated").html(updated_text);
    }
    // If we're in this function, show the online beacon and hide the others
    jQuery(".onlineMarker").show(); // Show the online beacon
    jQuery(".offlineMarker").hide();
    jQuery(".loadingMarker").hide();

    // Update the station observation box elements
    station_mqtt_data = Object.keys(data); // Turn data (mqtt message) into an object we can forEach
    // Get all span elements within the table. This is setup by Python initially
    jQuery('.station-observations').find("span").each(function() {
        // The class name is the same as the Extras.station_observations name (weewx schema)
        thisElementClass = jQuery(this).attr("class")
        // Loop through each MQTT payload item
        station_mqtt_data.forEach(mqttdata => {
            if (thisElementClass == "rainWithRainRate") {
                // Force dayRain since that's the MQTT payload name
                thisElementClass = "dayRain";
            }
            if (thisElementClass == "barometer" || thisElementClass == "pressure" || thisElementClass == "altimeter" || thisElementClass == "cloudbase") {
                // Do not group number into thousands,hundreds format
                localeStringUseGrouping = false;
            } else {
                localeStringUseGrouping = true;
            }
            // If this MQTT payload key begins with the name of the span class name, update the info. Can also use mqttdata.includes(thisElementClass) if weewx-mqtt changes in future
            if (mqttdata.startsWith(thisElementClass)) {
                html_output = parseFloat(parseFloat(data[mqttdata])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array[thisElementClass], maximumFractionDigits: unit_rounding_array[thisElementClass], useGrouping: localeStringUseGrouping}) + unit_label_array[thisElementClass];

                // Finally update the element class
                jQuery("." + thisElementClass).html(html_output);
            }
        });
    });
    // End dynamic station observation box

    // Temperature F
    if (data.hasOwnProperty("outTemp_F")) {
        // Inside parseFloat converts str to int. Outside parseFloat processes the locale string
        // Help from: https://stackoverflow.com/a/40152286/1177153 and https://stackoverflow.com/a/31581206/1177153
        outTemp = parseFloat(parseFloat(data["outTemp_F"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["outTemp"], maximumFractionDigits: unit_rounding_array["outTemp"]});
        get_outTemp_color("degree_F", outTemp);
        jQuery(".outtemp").html(outTemp);

        // Feels like temp as defined by NOAA's "Apparent Temperature" at: http://www.nws.noaa.gov/ndfd/definitions.htm
        //if ( data["outTemp_F"] <= 50 ) {
        //    jQuery(".feelslike").html( "Feels like: " + parseFloat(parseFloat(data["windchill_F"])).toLocaleString("$system_locale_js", {minimumFractionDigits: 1, maximumFractionDigits: 1}) + " $unit.label.outTemp" );
        //} else if ( data["outTemp_F"] >= 80 ) {
        //    jQuery(".feelslike").html( "Feels like: " + parseFloat(parseFloat(data["heatindex_F"])).toLocaleString("$system_locale_js", {minimumFractionDigits: 1, maximumFractionDigits: 1}) + " $unit.label.outTemp" );
        //} else {
        //    jQuery(".feelslike").html( "Feels like: " + parseFloat(parseFloat(data["outTemp_F"])).toLocaleString("$system_locale_js", {minimumFractionDigits: 1, maximumFractionDigits: 1}) + " $unit.label.outTemp" );
        //}
    }

    // Temperature C
    if (data.hasOwnProperty("outTemp_C")) {
        outTemp = parseFloat(parseFloat(data["outTemp_C"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["outTemp"], maximumFractionDigits: unit_rounding_array["outTemp"]});
        get_outTemp_color("degree_C", outTemp);
        jQuery(".outtemp").html(outTemp);
    }

    // Apparent Temperature US
    if (data.hasOwnProperty("appTemp_F")) {
        jQuery(".feelslike").html(labels.feels_like + ": " + parseFloat(parseFloat(data["appTemp_F"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["outTemp"], maximumFractionDigits: unit_rounding_array["outTemp"]}) + " " + config.unit_label.outTemp);
    }

    // Apparent Temperature Metric
    if (data.hasOwnProperty("appTemp_C")) {
        jQuery(".feelslike").html(labels.feels_like + ": " + parseFloat(parseFloat(data["appTemp_C"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["outTemp"], maximumFractionDigits: unit_rounding_array["outTemp"]}) + " " + config.unit_label.outTemp);
    }

    // Wind
    if (data.hasOwnProperty("windDir")) {
        // No toLocaleString() here since there is no float decimal needed.
        rotateThis(data["windDir"]);
        //jQuery(".wind-arrow").css( "transform", "rotate(" + data["windDir"] + "deg)" );
        jQuery(".curwinddeg").html(parseFloat(data["windDir"]).toFixed(0) + "&deg;");
        jQuery(".curwinddir").html(highcharts_tooltip_factory(parseFloat(data["windDir"]).toFixed(0), "windDir"));
    }

    // Windspeed US
    if (data.hasOwnProperty("windSpeed_mph")) {
        jQuery(".curwindspeed").html(parseFloat(parseFloat(data["windSpeed_mph"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["windSpeed"], maximumFractionDigits: unit_rounding_array["windSpeed"]}));
    }
    // Windspeed Metric
    if (data.hasOwnProperty("windSpeed_kph")) {
        jQuery(".curwindspeed").html(parseFloat(parseFloat(data["windSpeed_kph"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["windSpeed"], maximumFractionDigits: unit_rounding_array["windSpeed"]}));
    }
    // Windspeed METRICWX
    if (data.hasOwnProperty("windSpeed_mps")) {
        jQuery(".curwindspeed").html(parseFloat(parseFloat(data["windSpeed_mps"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["windSpeed"], maximumFractionDigits: unit_rounding_array["windSpeed"]}));
    }
    // Windspeed Beaufort
    if (data.hasOwnProperty("windSpeed_beaufort")) {
        jQuery(".curwindspeed").html(parseFloat(parseFloat(data["windSpeed_beaufort"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["windSpeed"], maximumFractionDigits: unit_rounding_array["windSpeed"]}));
    }
    // Windspeed knots
    if (data.hasOwnProperty("windSpeed_knot")) {
        jQuery(".curwindspeed").html(parseFloat(parseFloat(data["windSpeed_knot"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["windSpeed"], maximumFractionDigits: unit_rounding_array["windSpeed"]}));
    }

    // Beaufort
    if (extras.beaufort_category === '1') {
    if (data.hasOwnProperty("beaufort")) {
        jQuery(".beaufort").html(beaufort_cat(parseFloat(data["beaufort"])));
    }
    }

    // Wind Gust US
    // May not be provided in mqtt, but just in case.
    if (data.hasOwnProperty("windGust_mph")) {
        jQuery(".curwindgust").html(parseFloat(parseFloat(data["windGust_mph"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["windGust"], maximumFractionDigits: unit_rounding_array["windGust"]}));
    }
    // Wind Gust Metric
    if (data.hasOwnProperty("windGust_kph")) {
        jQuery(".curwindgust").html(parseFloat(parseFloat(data["windGust_kph"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["windGust"], maximumFractionDigits: unit_rounding_array["windGust"]}));
    }
    // Wind Gust METRICWX
    if (data.hasOwnProperty("windGust_mps")) {
        jQuery(".curwindgust").html(parseFloat(parseFloat(data["windGust_mps"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["windGust"], maximumFractionDigits: unit_rounding_array["windGust"]}));
    }
    // Wind Gust Beaufort
    if (data.hasOwnProperty("windGust_beaufort")) {
        jQuery(".curwindgust").html(parseFloat(parseFloat(data["windGust_beaufort"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["windSpeed"], maximumFractionDigits: unit_rounding_array["windSpeed"]}));
    }
    // Windspeed knots
    if (data.hasOwnProperty("windGust_knot")) {
        jQuery(".curwindgust").html(parseFloat(parseFloat(data["windGust_knot"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["windSpeed"], maximumFractionDigits: unit_rounding_array["windSpeed"]}));
    }

    // Windchill US
    if (data.hasOwnProperty("windchill")) {
        jQuery(".curwindchill").html(parseFloat(parseFloat(data["windchill"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["windchill"], maximumFractionDigits: unit_rounding_array["windchill"]}) + config.unit_label.outTemp);
    }
    // Windchill Metric
    if (data.hasOwnProperty("windchill_C")) {
        jQuery(".curwindchill").html(parseFloat(parseFloat(data["windchill_C"])).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["windchill"], maximumFractionDigits: unit_rounding_array["windchill"]}) + config.unit_label.outTemp);
    }
};
