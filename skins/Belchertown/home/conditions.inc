## Home page block "conditions" (see home_sections in skin.conf)
<!-- First row with temperature, observation data and radar -->
<div class="row temperature-row">
    <div class="col-lg-4 toprow-height">
        <div class="row obs-row">
        
            <!-- Temperature -->
            <div class="weather-obs-top">
                <div class="row temp-observation">
                    <div class="col-sm-6 current_obs_top">
                        #if "forecast_enabled" in $Extras and $Extras.forecast_enabled == '1' and $current_obs_icon != ""
                        <img id="wxicon" src="$relative_url/images/$current_obs_icon">
                        #end if
                    </div>
                    <div class="col-sm-6 current_temp">
                        <div class="outtemp_outer"><span class="outtemp">$current.outTemp.formatted</span><sup class="outtempunitlabelsuper">$unit.label.outTemp</sup></div><!-- AJAX -->
                    </div>
                </div>
                <div class="row">
                    <div class="col-sm-6 current-obs-container">
                        <div class="current-obs-text">
                            $current_obs_summary
                        </div>
                        #if "aqi_enabled" in $Extras and $Extras.aqi_enabled == '1'
                        <div class="aqi_outer">
                            $obs.label.aqi: <span class="wx-aqi">$aqi</span> (<span class="wx-aqi-category">$aqi_category</span>)
                            #if "aqi_location_enabled" in $Extras and $Extras.aqi_location_enabled == '1'
                            <span class="aqi_location_outer"><br>$aqi_location</span>
                            #end if
                        </div>
                        #end if
                    </div>
                    <div class="col-sm-6">
                        #if $current.appTemp.has_data
                        <div class="feelslike">$obs.label.feels_like: $current.appTemp</div><!-- AJAX -->
                        #end if
                        <div class="stn-high-low">
                            <table class="stn-high-low-table">
                                <tbody>
                                    <tr>
                                        <td class="stn-high-low-table-title">$obs.label.highest_temperature</td>
                                        <td class="stn-high-low-table-title border-left">$obs.label.lowest_temperature</td>
                                    </tr>
                                    <tr>
                                        <td class="high">$day.outTemp.max</td>
                                        <td class="border-left low">$day.outTemp.min</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Wind -->
        <div class="obs-wind-divider"></div>
        <div class="row windrow">
            <div class="weather-obs-bottom">
                <div class="col-sm-12 current_wind">
                    <div class="col-sm-6">
                        <div class="compass">
                            <div class="direction">
                                <span class="curwinddir">
                                #if $current.windDir.ordinal_compass == "N/A"
                                --
                                #else
                                $current.windDir.ordinal_compass
                                #end if
                                </span>
                                <span class="curwinddeg">
                                #if $current.windDir.raw is None:
                                -
                                #else
                                $current.windDir.format("%.0f")
                                #end if
                                </span>
                            </div>
                            <div class="arrow"></div>
                        </div>
                    </div>
                    <div class="col-sm-6 windspeedtable">
                        <table class="wind-table">
                            <tbody>
                                <tr>
                                    <td class="windtext">$obs.label.wind_speed</td>
                                    <td class="windtext border-left gust">$obs.label.wind_gust</td>
                                </tr>
                                <tr>
                                    <td>
                                        <span class="curwindspeed">
                                            $current.windSpeed.toString(addLabel=False, NONE_string="--")
                                        </span>
                                    </td>
                                    <td class="border-left gust">&nbsp;
                                        <span class="curwindgust">
                                            $current.windGust.toString(addLabel=False, NONE_string="--")
                                        </span>
                                    </td>
                                </tr>
                                <tr>
                                    <td class="mph" colspan="3">$unit.label.windSpeed</td>
                                </tr>
                                #if "beaufort_category" in $Extras and $Extras.beaufort_category == '1'
                                <tr>
                                    <td class="beaufort" colspan="4"></td>
                                </tr>
                                #end if
                            </tbody>
                        </table>
                    </div>
                </div>
                <!-- Wind Hook -->
                #if os.path.exists("index_hook_after_wind_table.inc")
                <!-- Start of index_hook_after_wind_table -->
                <div class="index_hook_after_wind_table">
                    #include "index_hook_after_wind_table.inc"
                </div>
                <!-- End of index_hook_after_wind_table -->
                #end if
            </div>
        </div>
    </div>
    
    <!-- Station observations -->
    <div class="col-lg-3 current-almanac toprow-height border-left border-right">
        <div class="station-observations weather-obs-top">
            <table cellpadding="0" cellspacing="0">
                <tbody>
                    $station_obs_html
                </tbody>
            </table>
            <!-- Station Observations Hook -->
            #if os.path.exists("index_hook_after_station_observations.inc")
            <!-- Start of index_hook_after_station_observations -->
            <div class="index_hook_after_station_observations">
                #include "index_hook_after_station_observations.inc"
            </div>
            <!-- End of index_hook_after_station_observations -->
            #end if
        </div>                        
        
        <!-- Sun and Moon section -->
        <div class="weather-obs-bottom">
            <table cellpadding="0" cellspacing="0">
                <tbody>
                    <tr>
                        <td colspan="2">
                            <div class="row small-almanac">
                                #if $obs.label.sun_and_moon and $obs.label.sun_and_moon != ''
                                <div class="sun-moon-title">
                                    $obs.label.sun_and_moon
                                </div>
                                #end if
                                <div class="col-sm-5 sun">
                                    <span class="sunrise-set-image"><img src="$relative_url/images/sunrise.png"></span><span class="sunrise-value"></span><!-- moment.js -->
                                    <br>
                                    <span class="sunrise-set-image"><img src="$relative_url/images/sunset.png"></span><span class="sunset-value"></span><!-- moment.js -->
                                </div>
                                <div class="col-sm-7 moon">
                                    <div class="moon-container">
                                        <span class="moon-icon">
                                            <div class="moon-icon"></div><!-- JS -->
                                        </span>
                                        <strong><span class="moon-phase">#echo $almanac.moon_phase.title()#</span></strong><!-- AJAX -->
                                        <br>
                                        <span class="moon-visible"><strong>$almanac.moon_fullness%</strong> $obs.label.moon_visible</span><!-- AJAX -->
                                    </div>
                                </div>
                                <div class="clear"></div>
                                #if "almanac_extras" in $Extras and $Extras.almanac_extras == '1' and $almanac.hasExtras
                                <!-- Almanac Modal -->
                                <div class="sun-moon-modal"><a href="#almanac" data-toggle="modal" data-target="#almanac">$obs.label.almanac_more_details</a></div>
                                <!-- Almanac Modal -->
                                <div class="modal fade" id="almanac" tabindex="-1" role="dialog" aria-labelledby="almanac" aria-hidden="true">
                                    <div class="modal-dialog modal-lg" role="document">
                                        <div class="modal-content">
                                            <div class="modal-header">
                                                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                                    <span aria-hidden="true">&times;</span>
                                                </button>
                                                <h4 class="modal-title" id="almanac">$obs.label.almanac_modal_title</h4>
                                            </div>
                                            <div class="almanac-extras-modal-body modal-body">
                                                #include "celestial.inc"
                                            </div><!-- AJAX -->
                                            <div class="modal-footer">
                                                <button type="button" class="btn btn-primary" data-dismiss="modal">$obs.label.close</button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                #end if
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- Radar image -->
    <div class="col-lg-5 radar-map toprow-height">
        #if os.path.exists("index_radar.inc")
        #include "index_radar.inc"
        #else
        <div class="radar_image">$radar_html</div>
        #end if
    </div>
</div>
<!-- End of first row -->
