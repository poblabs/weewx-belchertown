## Home page block "conditions" (see home_sections in skin.conf)
<div class="wx-conditions">

    <section class="wx-tile wx-now">
        <div class="wx-now-main">
            <div class="wx-now-icon">
                #if "forecast_enabled" in $Extras and $Extras.forecast_enabled == '1' and $current_obs_icon != ""
                <img id="wxicon" src="$relative_url/images/$current_obs_icon" alt="">
                #end if
            </div>
            <div class="outtemp_outer"><span class="outtemp" data-unit-group="group_temperature">$current.outTemp.formatted</span><sup class="outtempunitlabelsuper" data-unit-label="group_temperature">$unit.label.outTemp</sup></div><!-- AJAX -->
        </div>
        <div class="wx-now-details">
            <div class="wx-now-text">
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
            <div class="wx-now-feel">
                #if $current.appTemp.has_data
                <div class="feelslike">$obs.label.feels_like: $current.appTemp</div><!-- AJAX -->
                #end if
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
    </section>

    <section class="wx-tile wx-wind">
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
        <table class="wind-table">
            <tbody>
                <tr>
                    <td class="windtext">$obs.label.wind_speed</td>
                    <td class="windtext border-left gust">$obs.label.wind_gust</td>
                </tr>
                <tr>
                    <td><span class="curwindspeed" data-unit-group="group_speed">$current.windSpeed.toString(addLabel=False, NONE_string="--")</span></td>
                    <td class="border-left gust"><span class="curwindgust" data-unit-group="group_speed">$current.windGust.toString(addLabel=False, NONE_string="--")</span></td>
                </tr>
                <tr>
                    <td class="mph" colspan="2" data-unit-label="group_speed">$unit.label.windSpeed</td>
                </tr>
                #if "beaufort_category" in $Extras and $Extras.beaufort_category == '1'
                <tr>
                    <td class="beaufort" colspan="2"></td>
                </tr>
                #end if
            </tbody>
        </table>
        #if os.path.exists("index_hook_after_wind_table.inc")
        <div class="index_hook_after_wind_table">
            #include "index_hook_after_wind_table.inc"
        </div>
        #end if
    </section>

    <section class="wx-tile wx-readings station-observations">
        <table>
            <tbody>
                $station_obs_html
            </tbody>
        </table>
        #if os.path.exists("index_hook_after_station_observations.inc")
        <div class="index_hook_after_station_observations">
            #include "index_hook_after_station_observations.inc"
        </div>
        #end if
    </section>

    <section class="wx-tile wx-sunmoon">
        #if $obs.label.sun_and_moon and $obs.label.sun_and_moon != ''
        <h2 class="sun-moon-title">$obs.label.sun_and_moon</h2>
        #end if
        <div class="wx-sunmoon-row">
            <div class="sun">
                <span class="sunrise-set-image"><img src="$relative_url/images/sunrise.png" alt=""></span><span class="sunrise-value"></span><!-- Day.js -->
                <br>
                <span class="sunrise-set-image"><img src="$relative_url/images/sunset.png" alt=""></span><span class="sunset-value"></span><!-- Day.js -->
            </div>
            <div class="moon">
                <div class="moon-container">
                    <span class="moon-icon">
                        <div class="moon-icon"></div><!-- JS -->
                    </span>
                    <strong><span class="moon-phase">#echo $almanac.moon_phase.title()#</span></strong><!-- AJAX -->
                    <br>
                    <span class="moon-visible"><strong>$almanac.moon_fullness%</strong> $obs.label.moon_visible</span><!-- AJAX -->
                </div>
            </div>
        </div>
        #if "almanac_extras" in $Extras and $Extras.almanac_extras == '1' and $almanac.hasExtras
        <div class="sun-moon-modal"><a href="#almanac" data-toggle="modal" data-target="#almanac">$obs.label.almanac_more_details</a></div>
        <div class="modal fade" id="almanac" tabindex="-1" role="dialog" aria-labelledby="almanac-title" aria-hidden="true">
            <div class="modal-dialog modal-lg" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                        <h4 class="modal-title" id="almanac-title">$obs.label.almanac_modal_title</h4>
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
    </section>

    <section class="wx-tile wx-radar radar-map">
        #if os.path.exists("index_radar.inc")
        #include "index_radar.inc"
        #else
        <div class="radar_image">$radar_html</div>
        #end if
    </section>

</div>
