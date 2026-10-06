//  declare icon_dict as global variable
var icon_dict = {};

// Forecast (only called when forecast_enabled = 1)
function ajaxforecast() {
    forecast_data = {};
    jQuery.when(
        // Get the iconlist - original source is // https://www.xweather.com/docs/weather-api/reference/icon-list
        jQuery.getJSON(get_relative_url() + '/images/aeris-icon-list.json', function(iconlist) {
        icon_dict = iconlist;
            }
        ),
        // Get the forecast
        jQuery.getJSON(get_relative_url() + "/json/forecast.json", function(forecast) {
        forecast_data = forecast;
            }
        )
    ).then(function() {
        //  update forecast once both promises are fulfilled
        update_forecast_data(forecast_data);
        }
    );
}

function aeris_coded_weather(data, full_observation = false) {
    // https://www.xweather.com/docs/weather-api/reference/weather-codes
    var output = "";
    var coverage_code = data.split(":")[0]
    var intensity_code = data.split(":")[1]
    var weather_code = data.split(":")[2]

    var cloud_dict = {
        "CL": labels.forecast_cloud_code_CL,
        "FW": labels.forecast_cloud_code_FW,
        "SC": labels.forecast_cloud_code_SC,
        "BK": labels.forecast_cloud_code_BK,
        "OV": labels.forecast_cloud_code_OV
    }

    var coverage_dict = {
        "AR": labels.forecast_coverage_code_AR,
        "BR": labels.forecast_coverage_code_BR,
        "C": labels.forecast_coverage_code_C,
        "D": labels.forecast_coverage_code_D,
        "FQ": labels.forecast_coverage_code_FQ,
        "IN": labels.forecast_coverage_code_IN,
        "IS": labels.forecast_coverage_code_IS,
        "L": labels.forecast_coverage_code_L,
        "NM": labels.forecast_coverage_code_NM,
        "O": labels.forecast_coverage_code_O,
        "PA": labels.forecast_coverage_code_PA,
        "PD": labels.forecast_coverage_code_PD,
        "S": labels.forecast_coverage_code_S,
        "SC": labels.forecast_coverage_code_SC,
        "VC": labels.forecast_coverage_code_VC,
        "WD": labels.forecast_coverage_code_WD
    }

    var intensity_dict = {
        "VL": labels.forecast_intensity_code_VL,
        "L": labels.forecast_intensity_code_L,
        "H": labels.forecast_intensity_code_H,
        "VH": labels.forecast_intensity_code_VH
    }

    var weather_dict = {
        "A": labels.forecast_weather_code_A,
        "BD": labels.forecast_weather_code_BD,
        "BN": labels.forecast_weather_code_BN,
        "BR": labels.forecast_weather_code_BR,
        "BS": labels.forecast_weather_code_BS,
        "BY": labels.forecast_weather_code_BY,
        "F": labels.forecast_weather_code_F,
        "FR": labels.forecast_weather_code_FR,
        "H": labels.forecast_weather_code_H,
        "IC": labels.forecast_weather_code_IC,
        "IF": labels.forecast_weather_code_IF,
        "IP": labels.forecast_weather_code_IP,
        "K": labels.forecast_weather_code_K,
        "L": labels.forecast_weather_code_L,
        "R": labels.forecast_weather_code_R,
        "RW": labels.forecast_weather_code_RW,
        "RS": labels.forecast_weather_code_RS,
        "SI": labels.forecast_weather_code_SI,
        "WM": labels.forecast_weather_code_WM,
        "S": labels.forecast_weather_code_S,
        "SW": labels.forecast_weather_code_SW,
        "T": labels.forecast_weather_code_T,
        "UP": labels.forecast_weather_code_UP,
        "VA": labels.forecast_weather_code_VA,
        "WP": labels.forecast_weather_code_WP,
        "ZF": labels.forecast_weather_code_ZF,
        "ZL": labels.forecast_weather_code_ZL,
        "ZR": labels.forecast_weather_code_ZR,
        "ZY": labels.forecast_weather_code_ZY
    }

    // Check if the weather_code is in the cloud_dict and use that if it's there. If not then it's a combined weather code.
    if (cloud_dict.hasOwnProperty(weather_code)) {
        return cloud_dict[weather_code];
    } else {
        // Add the coverage if it's present, and full observation forecast is requested
        if ((coverage_code) && (full_observation)) {
            output += coverage_dict[coverage_code] + " ";
        }
        // Add the intensity if it's present
        if (intensity_code) {
            output += intensity_dict[intensity_code] + " ";
        }
        // Weather output
        output += weather_dict[weather_code];
    }

    return output;
}

function aeris_coded_alerts(data, full_observation = false) {
    // https://www.xweather.com/docs/maps/reference/alert-types

    var alert_dict = {
        "TOE": labels.forecast_alert_code_TOE,
        "ADR": labels.forecast_alert_code_ADR,
        "AQA": labels.forecast_alert_code_AQA,
        "AQ.S": labels.forecast_alert_code_AQ_S,
        "AS.Y": labels.forecast_alert_code_AS_Y,
        "AR.W": labels.forecast_alert_code_AR_W,
        "AF.Y": labels.forecast_alert_code_AF_Y,
        "MH.Y": labels.forecast_alert_code_MH_Y,
        "AF.W": labels.forecast_alert_code_AF_W,
        "AVW": labels.forecast_alert_code_AVW,
        "AVA": labels.forecast_alert_code_AVA,
        "BH.S": labels.forecast_alert_code_BH_S,
        "BZ.W": labels.forecast_alert_code_BZ_W,
        "DU.Y": labels.forecast_alert_code_DU_Y,
        "BS.Y": labels.forecast_alert_code_BS_Y,
        "BW.Y": labels.forecast_alert_code_BW_Y,
        "CAE": labels.forecast_alert_code_CAE,
        "CDW": labels.forecast_alert_code_CDW,
        "CEM": labels.forecast_alert_code_CEM,
        "CF.Y": labels.forecast_alert_code_CF_Y,
        "CF.S": labels.forecast_alert_code_CF_S,
        "CF.W": labels.forecast_alert_code_CF_W,
        "CF.A": labels.forecast_alert_code_CF_A,
        "FG.Y": labels.forecast_alert_code_FG_Y,
        "MF.Y": labels.forecast_alert_code_MF_Y,
        "FO.Y": labels.forecast_alert_code_FO_Y,
        "SM.Y": labels.forecast_alert_code_SM_Y,
        "MS.Y": labels.forecast_alert_code_MS_Y,
        "DS.W": labels.forecast_alert_code_DS_W,
        "EQW": labels.forecast_alert_code_EQW,
        "EVI": labels.forecast_alert_code_EVI,
        "EH.W": labels.forecast_alert_code_EH_W,
        "EH.A": labels.forecast_alert_code_EH_A,
        "EC.W": labels.forecast_alert_code_EC_W,
        "EC.A": labels.forecast_alert_code_EC_A,
        "RFD": labels.forecast_alert_code_RFD,
        "EW.W": labels.forecast_alert_code_EW_W,
        "FRW": labels.forecast_alert_code_FRW,
        "FW.A": labels.forecast_alert_code_FW_A,
        "FF.S": labels.forecast_alert_code_FF_S,
        "FF.W": labels.forecast_alert_code_FF_W,
        "FF.A": labels.forecast_alert_code_FF_A,
        "FE.W": labels.forecast_alert_code_FE_W,
        "FL.Y": labels.forecast_alert_code_FL_Y,
        "FL.S": labels.forecast_alert_code_FL_S,
        "FL.W": labels.forecast_alert_code_FL_W,
        "FA.W": labels.forecast_alert_code_FA_W,
        "FL.A": labels.forecast_alert_code_FL_A,
        "FA.A": labels.forecast_alert_code_FA_A,
        "FZ.W": labels.forecast_alert_code_FZ_W,
        "FZ.A": labels.forecast_alert_code_FZ_A,
        "ZL.Y": labels.forecast_alert_code_ZL_Y,
        "ZF.Y": labels.forecast_alert_code_ZF_Y,
        "ZR.W": labels.forecast_alert_code_ZR_W,
        "UP.Y": labels.forecast_alert_code_UP_Y,
        "FR.Y": labels.forecast_alert_code_FR_Y,
        "GL.W": labels.forecast_alert_code_GL_W,
        "GL.A": labels.forecast_alert_code_GL_A,
        "HZ.W": labels.forecast_alert_code_HZ_W,
        "HZ.A": labels.forecast_alert_code_HZ_A,
        "HMW": labels.forecast_alert_code_HMW,
        "SE.W": labels.forecast_alert_code_SE_W,
        "SE.A": labels.forecast_alert_code_SE_A,
        "HWO": labels.forecast_alert_code_HWO,
        "HT.Y": labels.forecast_alert_code_HT_Y,
        "HT.W": labels.forecast_alert_code_HT_W,
        "UP.W": labels.forecast_alert_code_UP_W,
        "UP.A": labels.forecast_alert_code_UP_A,
        "SU.Y": labels.forecast_alert_code_SU_Y,
        "SU.W": labels.forecast_alert_code_SU_W,
        "HW.W": labels.forecast_alert_code_HW_W,
        "HW.A": labels.forecast_alert_code_HW_A,
        "HF.W": labels.forecast_alert_code_HF_W,
        "HF.A": labels.forecast_alert_code_HF_A,
        "HU.S": labels.forecast_alert_code_HU_S,
        "HU.W": labels.forecast_alert_code_HU_W,
        "HU.A": labels.forecast_alert_code_HU_A,
        "FA.Y": labels.forecast_alert_code_FA_Y,
        "IS.W": labels.forecast_alert_code_IS_W,
        "LE.W": labels.forecast_alert_code_LE_W,
        "LW.Y": labels.forecast_alert_code_LW_Y,
        "LS.Y": labels.forecast_alert_code_LS_Y,
        "LS.S": labels.forecast_alert_code_LS_S,
        "LS.W": labels.forecast_alert_code_LS_W,
        "LS.A": labels.forecast_alert_code_LS_A,
        "LEW": labels.forecast_alert_code_LEW,
        "LAE": labels.forecast_alert_code_LAE,
        "LO.Y": labels.forecast_alert_code_LO_Y,
        "MA.S": labels.forecast_alert_code_MA_S,
        "NUW": labels.forecast_alert_code_NUW,
        "RHW": labels.forecast_alert_code_RHW,
        "RA.W": labels.forecast_alert_code_RA_W,
        "FW.W": labels.forecast_alert_code_FW_W,
        "RFW": labels.forecast_alert_code_RFW,
        "RP.S": labels.forecast_alert_code_RP_S,
        "SV.W": labels.forecast_alert_code_SV_W,
        "SV.A": labels.forecast_alert_code_SV_A,
        "SV.S": labels.forecast_alert_code_SV_S,
        "TO.S": labels.forecast_alert_code_TO_S,
        "SPW": labels.forecast_alert_code_SPW,
        "NOW": labels.forecast_alert_code_NOW,
        "SC.Y": labels.forecast_alert_code_SC_Y,
        "SW.Y": labels.forecast_alert_code_SW_Y,
        "RB.Y": labels.forecast_alert_code_RB_Y,
        "SI.Y": labels.forecast_alert_code_SI_Y,
        "SO.W": labels.forecast_alert_code_SO_W,
        "SQ.W": labels.forecast_alert_code_SQ_W,
        "SQ.A": labels.forecast_alert_code_SQ_A,
        "SB.Y": labels.forecast_alert_code_SB_Y,
        "SN.W": labels.forecast_alert_code_SN_W,
        "MA.W": labels.forecast_alert_code_MA_W,
        "SP.S": labels.forecast_alert_code_SPS,
        "SG.W": labels.forecast_alert_code_SG_W,
        "SS.W": labels.forecast_alert_code_SS_W,
        "SS.A": labels.forecast_alert_code_SS_A,
        "SR.W": labels.forecast_alert_code_SR_W,
        "SR.A": labels.forecast_alert_code_SR_A,
        "TO.W": labels.forecast_alert_code_TO_W,
        "TO.A": labels.forecast_alert_code_TO_A,
        "TC.S": labels.forecast_alert_code_TC_S,
        "TR.S": labels.forecast_alert_code_TR_S,
        "TR.W": labels.forecast_alert_code_TR_W,
        "TR.A": labels.forecast_alert_code_TR_A,
        "TS.Y": labels.forecast_alert_code_TS_Y,
        "TS.W": labels.forecast_alert_code_TS_W,
        "TS.A": labels.forecast_alert_code_TS_A,
        "TY.S": labels.forecast_alert_code_TY_S,
        "TY.W": labels.forecast_alert_code_TY_W,
        "TY.A": labels.forecast_alert_code_TY_A,
        "VOW": labels.forecast_alert_code_VOW,
        "WX.Y": labels.forecast_alert_code_WX_Y,
        "WX.W": labels.forecast_alert_code_WX_W,
        "WI.Y": labels.forecast_alert_code_WI_Y,
        "WC.Y": labels.forecast_alert_code_WC_Y,
        "WC.W": labels.forecast_alert_code_WC_W,
        "WC.A": labels.forecast_alert_code_WC_A,
        "WI.W": labels.forecast_alert_code_WI_W,
        "WS.W": labels.forecast_alert_code_WS_W,
        "WS.A": labels.forecast_alert_code_WS_A,
        "LE.A": labels.forecast_alert_code_LE_A,
        "BZ.A": labels.forecast_alert_code_BZ_A,
        "WW.Y": labels.forecast_alert_code_WW_Y,
        "LE.Y": labels.forecast_alert_code_LE_Y,
        "ZR.Y": labels.forecast_alert_code_ZR_Y,
        "AW.WI.MN": labels.forecast_alert_code_AW_WI_MN,
        "AW.WI.MD": labels.forecast_alert_code_AW_WI_MD,
        "AW.WI.SV": labels.forecast_alert_code_AW_WI_SV,
        "AW.WI.EX": labels.forecast_alert_code_AW_WI_EX,
        "AW.SI.MN": labels.forecast_alert_code_AW_SI_MN,
        "AW.SI.MD": labels.forecast_alert_code_AW_SI_MD,
        "AW.SI.SV": labels.forecast_alert_code_AW_SI_SV,
        "AW.SI.EX": labels.forecast_alert_code_AW_SI_EX,
        "AW.TS.MN": labels.forecast_alert_code_AW_TS_MN,
        "AW.TS.MD": labels.forecast_alert_code_AW_TS_MD,
        "AW.TS.SV": labels.forecast_alert_code_AW_TS_SV,
        "AW.TS.EX": labels.forecast_alert_code_AW_TS_EX,
        "AW.LI.MN": labels.forecast_alert_code_AW_LI_MN,
        "AW.LI.MD": labels.forecast_alert_code_AW_LI_MD,
        "AW.LI.SV": labels.forecast_alert_code_AW_LI_SV,
        "AW.LI.EX": labels.forecast_alert_code_AW_LI_EX,
        "AW.FG.MN": labels.forecast_alert_code_AW_FG_MN,
        "AW.FG.MD": labels.forecast_alert_code_AW_FG_MD,
        "AW.FG.SV": labels.forecast_alert_code_AW_FG_SV,
        "AW.FG.EX": labels.forecast_alert_code_AW_FG_EX,
        "AW.HT.MN": labels.forecast_alert_code_AW_HT_MN,
        "AW.HT.MD": labels.forecast_alert_code_AW_HT_MD,
        "AW.HT.SV": labels.forecast_alert_code_AW_HT_SV,
        "AW.HT.EX": labels.forecast_alert_code_AW_HT_EX,
        "AW.LT.MN": labels.forecast_alert_code_AW_LT_MN,
        "AW.LT.MD": labels.forecast_alert_code_AW_LT_MD,
        "AW.LT.SV": labels.forecast_alert_code_AW_LT_SV,
        "AW.LT.EX": labels.forecast_alert_code_AW_LT_EX,
        "AW.CE.MN": labels.forecast_alert_code_AW_CE_MN,
        "AW.CE.MD": labels.forecast_alert_code_AW_CE_MD,
        "AW.CE.SV": labels.forecast_alert_code_AW_CE_SV,
        "AW.CE.EX": labels.forecast_alert_code_AW_CE_EX,
        "AW.FR.MN": labels.forecast_alert_code_AW_FR_MN,
        "AW.FR.MD": labels.forecast_alert_code_AW_FR_MD,
        "AW.FR.SV": labels.forecast_alert_code_AW_FR_SV,
        "AW.FR.EX": labels.forecast_alert_code_AW_FR_EX,
        "AW.AV.MN": labels.forecast_alert_code_AW_AV_MN,
        "AW.AV.MD": labels.forecast_alert_code_AW_AV_MD,
        "AW.AV.SV": labels.forecast_alert_code_AW_AV_SV,
        "AW.AV.EX": labels.forecast_alert_code_AW_AV_EX,
        "AW.RA.MN": labels.forecast_alert_code_AW_RA_MN,
        "AW.RA.MD": labels.forecast_alert_code_AW_RA_MD,
        "AW.RA.SV": labels.forecast_alert_code_AW_RA_SV,
        "AW.RA.EX": labels.forecast_alert_code_AW_RA_EX,
        "AW.FL.MN": labels.forecast_alert_code_AW_FL_MN,
        "AW.FL.MD": labels.forecast_alert_code_AW_FL_MD,
        "AW.FL.SV": labels.forecast_alert_code_AW_FL_SV,
        "AW.FL.EX": labels.forecast_alert_code_AW_FL_EX,
        "AW.RF.MN": labels.forecast_alert_code_AW_RF_MN,
        "AW.RF.MD": labels.forecast_alert_code_AW_RF_MD,
        "AW.RF.SV": labels.forecast_alert_code_AW_RF_SV,
        "AW.RF.EX": labels.forecast_alert_code_AW_RF_EX,
        "AW.UK.MN": labels.forecast_alert_code_AW_UK_MN,
        "AW.UK.MD": labels.forecast_alert_code_AW_UK_MD,
        "AW.UK.SV": labels.forecast_alert_code_AW_UK_SV,
        "AW.UK.EX": labels.forecast_alert_code_AW_UK_EX
    }

    return alert_dict[data];
}

function aeris_icon(data) {
    // https://www.xweather.com/docs/weather-api/reference/icon-list
    var icon_name = data.split(".")[0]; // Remove .png
        icon_out = icon_dict[icon_name];
        if ( icon_out === undefined ) {
            icon_out ='unknown' 
            }
        return icon_out;
}

function show_forcast_alert(data, forecast_provider) {
    belchertown_debug("Forecast: Updating alert data for " + forecast_provider);
    var i, forecast_alert_modal, forecast_alerts;
    forecast_alert_modal = "";
    forecast_alerts = [];

    // Empty anything that's been appended to the modal from the previous run
    jQuery(".wx-stn-alert-text").empty();

    if (forecast_provider == "darksky") {
        if (data['alerts']) {
            for (i = 0; i < data['alerts'].length; i++) {
                forecast_alert_title = data['alerts'][i]['title'];
                forecast_alert_body = data['alerts'][i]['description'].replace(/\n/g, '<br>');
                forecast_alert_link = data['alerts'][i]['title'];
                forecast_alert_expires = tzAdjustedMoment(data['alerts'][i]['expires']).format(labels.time_forecast_alert_expires);
                forecast_alerts.push({"title": forecast_alert_title, "body": forecast_alert_body, "link": forecast_alert_link, "expires": forecast_alert_expires});
            }
        }
    } else if (forecast_provider == "aeris") {
        if (data['alerts'][0]['response'][0]) {
            for (i = 0; i < data['alerts'][0]['response'].length; i++) {
                //forecast_alert_title = data['alerts'][0]['response'][i]['details']['name'];
                forecast_alert_title = aeris_coded_alerts(data['alerts'][0]['response'][i]['details']['type']);
                if (typeof forecast_alert_title === "undefined") {
                    // If the type can't be decoded then use the raw name in the alert. I have seen this for "Hurricane Local Statement" not matching a coded weather value
                    forecast_alert_title = data['alerts'][0]['response'][i]['details']['name'];
                }
                forecast_alert_body = data['alerts'][0]['response'][i]['details']['body'].replace(/\n/g, '<br>');
                //forecast_alert_link = data['alerts'][0]['response'][i]['details']['name'];
                forecast_alert_link = data['alerts'][0]['response'][i]['details']['type'];
                forecast_alert_expires = tzAdjustedMoment(data['alerts'][0]['response'][i]['timestamps']['expires']).format(labels.time_forecast_alert_expires);
                forecast_alerts.push({"title": forecast_alert_title, "body": forecast_alert_body, "link": forecast_alert_link, "expires": forecast_alert_expires});
            }
        }
    }

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

function aeris_aqi_translate(data) {
    if (data === "good") data = labels.aqi_good;
    else if (data === "moderate") data = labels.aqi_moderate;
    else if (data === "usg") data = labels.aqi_usg;
    else if (data === "unhealthy") data = labels.aqi_unhealthy;
    else if (data === "very unhealthy") data = labels.aqi_very_unhealthy;
    else if (data === "hazardous") data = labels.aqi_hazardous;
    else data = labels.aqi_unknown;

    return data;
}

function update_forecast_data(data) {
    forecast_provider = extras.forecast_provider;
    belchertown_debug("Forecast: Provider is " + forecast_provider);
    belchertown_debug("Forecast: Updating data");
    belchertown_debug(data);

    if (forecast_provider == "N/A") {
        jQuery(".forecastrow").hide();
        belchertown_debug("Forecast: No provider, hiding forecastrow");
        return;
    } else if (forecast_provider == "aeris") {
        var forecast_subtitle = tzAdjustedMoment(data["timestamp"]).format(labels.time_forecast_last_updated);

        try {
            var wxicon = get_relative_url() + "/images/" + aeris_icon(data["current"][0]["response"]["ob"]["icon"]) + ".png";
        } catch (err) {
            // Returned "current" data does not have this value
        }
        
        // Current observation text
        try {
            jQuery(".current-obs-text").html(aeris_coded_weather(data["current"][0]["response"]["ob"]["weatherPrimaryCoded"], true));
        } catch (err) {
            // Returned "current" data does not have this value
        }

        
        // AQI
        if (data["aqi"][0]["success"] && !data["aqi"][0]["error"]) {
            jQuery(".wx-aqi").html(data["aqi"][0]["response"][0]["periods"][0]["aqi"]);
            jQuery(".wx-aqi-category").html(aeris_aqi_translate(data["aqi"][0]["response"][0]["periods"][0]["category"]));
            if (extras.aqi_location_enabled === "1") jQuery(".aqi_location_outer").html("<br>" + data["aqi"][0]["response"][0]["place"]["name"]).css('textTransform', 'capitalize');
            get_aqi_color(data["aqi"][0]["response"][0]["periods"][0]["aqi"]);
            try {
                jQuery(".station-observations .aqi").html(data["aqi"][0]["response"][0]["periods"][0]["aqi"]);
            } catch (err) {
                // AQI not in the station observation table, so silently exit
            }
        } else if (data["aqi"][0]["success"] && data["aqi"][0]["error"]["code"] === "warn_no_data") {
            jQuery(".wx-aqi").html("No Data");
            jQuery(".wx-aqi-category").html(aeris_aqi_translate(""));
            if (extras.aqi_location_enabled === "1") jQuery(".aqi_location_outer").html("");
            try {
                jQuery(".station-observations .aqi").html("No Data");
            } catch (err) {
                // AQI not in the station observation table, so silently exit
            }
        }

        // Visibility text in station observation table
        try {
            if ((extras.forecast_units == "si") || (extras.forecast_units == "ca")) {
                // si and ca = kilometer
                visibility = data["current"][0]["response"]["ob"]["visibilityKM"];

            } else {
                // us and uk2 and default = miles
                visibility = data["current"][0]["response"]["ob"]["visibilityMI"];
            }
        } catch (err) {
            // Returned "current" data does not have this value
        }

        try {
            visibility_output = parseFloat(parseFloat(visibility)).toLocaleString(config.system_locale_js, {minimumFractionDigits: unit_rounding_array["visibility"], maximumFractionDigits: unit_rounding_array["visibility"]}) + " " + unit_label_array["visibility"];

            jQuery(".station-observations .visibility").html(visibility_output);
        } catch (err) {
            // Visibility not in the station observation table or any of the unit arrays, so silently exit
        }

        //  start of new composite version of forecast code

        var forecast_types = ["forecast_1hr", "forecast_3hr", "forecast_24hr"];
        var forecast_interval
        for (forecast_interval of forecast_types) {
            var forecast_row = [];
            var output_html = "";
            for (i = 0; i < data[(forecast_interval)][0]["response"][0]["periods"].length; i++) {

                //  for 24hr interval add 7200 (2 hours) to the epoch to get an hour well into the day to avoid any DST issues. This way it'll either be 1am or 2am. Without it, we get 12am or 11pm (the previous day).
                if (forecast_interval == "forecast_24hr") {
                    var image_url = get_relative_url() + "/images/" + aeris_icon(data[(forecast_interval)][0]["response"][0]["periods"][i]["icon"]) + ".png";
                    var condition_text = aeris_coded_weather(data[(forecast_interval)][0]["response"][0]["periods"][i]["weatherPrimaryCoded"], false);
                    var weekday = tzAdjustedMoment(data[(forecast_interval)][0]["response"][0]["periods"][i]["timestamp"] + 7200).format(labels.time_forecast_date);
                } else {
                    var image_url = get_relative_url() + "/images/" + aeris_icon(data[(forecast_interval)][0]["response"][0]["periods"][i]["icon"]) + ".png";
                    var condition_text = aeris_coded_weather(data[(forecast_interval)][0]["response"][0]["periods"][i]["weatherPrimaryCoded"], false);
                    var weekday = tzAdjustedMoment(data[(forecast_interval)][0]["response"][0]["periods"][i]["timestamp"]).format(labels.time_forecast_time);
                }

                // Determine temperature units
                if ((extras.forecast_units == "ca") || (extras.forecast_units == "uk2") || (extras.forecast_units == "si")) {
                    avgTemp = data[(forecast_interval)][0]["response"][0]["periods"][i]["avgTempC"];
                    minTemp = data[(forecast_interval)][0]["response"][0]["periods"][i]["minTempC"];
                    maxTemp = data[(forecast_interval)][0]["response"][0]["periods"][i]["maxTempC"];
                    var dewPoint = data[(forecast_interval)][0]["response"][0]["periods"][i]["dewpointC"];
                } else {
                    // Default
                    avgTemp = data[(forecast_interval)][0]["response"][0]["periods"][i]["avgTempF"];
                    minTemp = data[(forecast_interval)][0]["response"][0]["periods"][i]["minTempF"];
                    maxTemp = data[(forecast_interval)][0]["response"][0]["periods"][i]["maxTempF"];
                    var dewPoint = data[(forecast_interval)][0]["response"][0]["periods"][i]["dewpointF"];
                }

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

                // Determine wind units
                if (config.unit_type.windSpeed == "knot") {
                    windSpeed = data[(forecast_interval)][0]["response"][0]["periods"][i]["windSpeedKTS"];
                    windGust = data[(forecast_interval)][0]["response"][0]["periods"][i]["windGustKTS"];
                } else if (config.unit_type.windSpeed == "beaufort") {
                    windSpeed = kts_to_beaufort(data[(forecast_interval)][0]["response"][0]["periods"][i]["windSpeedKTS"]);
                    windGust = kts_to_beaufort(data[(forecast_interval)][0]["response"][0]["periods"][i]["windGustKTS"]);
                } else if (extras.forecast_units == "ca") {
                    // ca = kph
                    windSpeed = data[(forecast_interval)][0]["response"][0]["periods"][i]["windSpeedKPH"];
                    windGust = data[(forecast_interval)][0]["response"][0]["periods"][i]["windGustKPH"];
                } else if (extras.forecast_units == "si") {
                    // si = meters per second. MPS is KPH / 3.6
                    windSpeed = data[(forecast_interval)][0]["response"][0]["periods"][i]["windSpeedKPH"] / 3.6;
                    windGust = data[(forecast_interval)][0]["response"][0]["periods"][i]["windGustKPH"] / 3.6;
                } else {
                    // us and uk2 and default = mph
                    windSpeed = data[(forecast_interval)][0]["response"][0]["periods"][i]["windSpeedMPH"];
                    windGust = data[(forecast_interval)][0]["response"][0]["periods"][i]["windGustMPH"];
                }

                /*
                As per API specification, "pop" is either a number from 0 to
                100 or null. We convert to 0 in the second case.
                */
                var precip = data[(forecast_interval)][0]["response"][0]["periods"][i]["pop"] || 0;

                // Humidity
                var humidity = data[(forecast_interval)][0]["response"][0]["periods"][i]["humidity"];

                /*
                Determine snow unit. "snowCM" and "snowIN" are specified
                to always return a number. We still convert to 0 if we ever get
                null.
                */
                if ((extras.forecast_units == "si") || (extras.forecast_units == "ca") || (extras.forecast_units == "uk2")) {
                    var snow_depth = data[(forecast_interval)][0]["response"][0]["periods"][i]["snowCM"] || 0;
                    var snow_unit = "cm";
                } else {
                    var snow_depth = data[(forecast_interval)][0]["response"][0]["periods"][i]["snowIN"] || 0;
                    var snow_unit = "in";
                }

                //  for 24hr interval add 7200 (2 hours) to the epoch to get an hour well into the day to avoid any DST issues. This way it'll either be 1am or 2am. Without it, we get 12am or 11pm (the previous day).
                if (forecast_interval == "forecast_24hr") {
                    var forecast_link_setup = extras.forecast_daily_forecast_link.replace("YYYY", tzAdjustedMoment(data[(forecast_interval)][0]["response"][0]["periods"][i]["timestamp"] + 7200).format("YYYY")).replace("MM", tzAdjustedMoment(data[(forecast_interval)][0]["response"][0]["periods"][i]["timestamp"] + 7200).format("MM")).replace("DD", tzAdjustedMoment(data[(forecast_interval)][0]["response"][0]["periods"][i]["timestamp"] + 7200).format("DD"));
                } else {
                    var forecast_link_setup = extras.forecast_daily_forecast_link.replace("YYYY", tzAdjustedMoment(data[(forecast_interval)][0]["response"][0]["periods"][i]["timestamp"]).format("YYYY")).replace("MM", tzAdjustedMoment(data[(forecast_interval)][0]["response"][0]["periods"][i]["timestamp"]).format("MM")).replace("DD", tzAdjustedMoment(data[(forecast_interval)][0]["response"][0]["periods"][i]["timestamp"]).format("DD"));

                }

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

//	End of new composite version of forecast code
    
    if (extras.forecast_alert_enabled === '1') {
        // Show weather alert
        show_forcast_alert(data, forecast_provider);
    }

    // WX icon in temperature box    
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
