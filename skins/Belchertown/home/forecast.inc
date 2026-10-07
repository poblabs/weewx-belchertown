## Home page block "forecast" (see home_sections in skin.conf)
#if "forecast_enabled" in $Extras and $Extras.forecast_enabled == '1' and (("forecast_interval_hours" in $Extras and $Extras.forecast_interval_hours != '0') or not ("forecast_interval_hours" in $Extras))
<section class="forecastrow wx-forecast">
    <div class="wx-section-head">
        <h2 class="wx-section-title forecast-title"><i class="wi wi-day-cloudy" aria-hidden="true"></i> $obs.label.forecast_header <span class="forecast-subtitle"></span></h2><!-- JS -->
        <div class="forecast-menu">
            $obs.label.forecast_interval_caption
            <button type="button" class="forecast-button" onclick="forecast_select(1);" id="button1">1</button>
            <button type="button" class="forecast-button" onclick="forecast_select(3);" id="button3">3</button>
            <button type="button" class="forecast-button" onclick="forecast_select(24);" id="button24">24</button>
        </div>
    </div>
        
    #if "forecast_interval_hours" in $Extras and $Extras.forecast_interval_hours != '0'
    #if "forecast_interval_hours" in $Extras and $Extras.forecast_interval_hours == '1'
    <script>forecast_default(1);</script>
    #end if
    <div id="1hour-selected-forecast" style="display: none;">
        <!-- 1hour Forecast -->
        <div class="wx-forecast-days 1hr_forecasts"></div><!-- JS -->
    </div>
    #end if

    #if "forecast_interval_hours" in $Extras and $Extras.forecast_interval_hours == '3'
    <script>forecast_default(3);</script>
    #end if
    <div id="3hour-selected-forecast" style="display: none;">
        <!-- 3hour-Forecast -->
        <div class="wx-forecast-days 3hr_forecasts"></div><!-- JS -->
    </div>        

    #if ("forecast_interval_hours" in $Extras and $Extras.forecast_interval_hours == '24') or not ("forecast_interval_hours" in $Extras)
    <script>forecast_default(24);</script>
    #end if
    <div id="24hour-selected-forecast" style="display: none;">
        <!-- 24hour-Forecast -->
        <div class="wx-forecast-days 24hr_forecasts"></div><!-- JS -->
    </div>
</section>
#end if
