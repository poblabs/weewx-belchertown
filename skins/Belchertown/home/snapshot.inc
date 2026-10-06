## Home page block "snapshot" (see home_sections in skin.conf)
<!-- Start of third row -->
<div class="row eq-stats-row">            
    #if 'earthquake_enabled' in $Extras and $Extras.earthquake_enabled == '1'
    <div class="col-sm-9 stn-quick-stats">
    #else
    <div class="col-sm-12 stn-quick-stats">
    #end if
        
        <!-- Today Snapshot Stats -->
        <div class="row">
            <div class="snapshot-records-text">
                $obs.label.weather_snapshots <a href="$relative_url/records">$obs.label.weather_snapshots_link</a>
            </div>
            
            <div class="col-sm-6 stn-quick-stats">
                <div class="stats-title">
                    <span class="snapshot-records-today-header"></span><!-- JS and AJAX -->
                </div>
                <table>
                    <tr>
                        <td><b>$obs.label.snapshot_high:</b></td>    <td><span class="dailystatshigh">$day.outTemp.max</span></td><!-- AJAX -->
                        <td><b>$obs.label.snapshot_low:</b></td>    <td><span class="dailystatslow">$day.outTemp.min</span></td><!-- AJAX -->
                    </tr>
                    <tr>
                        <td><b>$obs.label.snapshot_today_avg_wind:</b></td>    <td><span class="dailystatswindavg">$day.wind.avg</span></td><!-- AJAX -->
                        <td><b>$obs.label.snapshot_today_high_wind:</b></td>        <td><span class="dailystatswindmax">$day.wind.max</span></td><!-- AJAX -->                    
                    </tr>
                    <tr>
                        <td><b>$obs.label.snapshot_today_rain:</b></td>    <td><span class="dailystatsrain">$day.rain.sum</span></td><!-- AJAX -->
                        <td><b>$obs.label.snapshot_today_rainrate:</b></td>    <td><span class="dailystatsrainrate">$day.rainRate.max</span></td><!-- AJAX -->
                    </tr>
                </table>
            </div>

            <!-- This Month Snapshot Stats -->
            <div class="col-sm-6 stn-quick-stats border-left">
                <div class="stats-title">
                    <span class="snapshot-records-month-header"></span><!-- JS and AJAX -->
                </div>
                <table>
                    <tr>
                        <td><b>$obs.label.snapshot_high:</b></td>    <td><span class="monthstatshigh">$month.outTemp.max</span></td><!-- AJAX -->
                        <td><b>$obs.label.snapshot_low:</b></td>    <td><span class="monthstatslow">$month.outTemp.min</span></td><!-- AJAX -->
                    </tr>
                    <tr>
                        <td><b>$obs.label.snapshot_month_avg_wind:</b></td>    <td><span class="monthstatswindavg">$month.wind.avg</span></td><!-- AJAX -->
                        <td><b>$obs.label.snapshot_month_high_wind:</b></td>        <td><span class="monthstatswindmax">$month.wind.max</span></td><!-- AJAX -->
                    </tr>
                    <tr>
                        <td><b>$obs.label.snapshot_month_rain:</b></td>        <td><span class="monthstatsrain">$month.rain.sum</span></td><!-- AJAX -->
                        <td><b>$obs.label.snapshot_month_rainrate:</b></td>    <td><span class="monthstatsrainrate">$month.rainRate.max</span></td><!-- AJAX -->
                    </tr>
                </table>
            </div>
        </div>
    </div>
    
    #if 'earthquake_enabled' in $Extras and $Extras.earthquake_enabled == '1'
    <!-- Earthquake data -->
    <div class="col-sm-3 earthquake-container border-left">
        <div class="eq-title">$obs.label.earthquake_title</div>
        <div class="eq-region">
            <span class="earthquake-time"></span><!-- moment.js -->
            #if $earthquake_place != ''
            <br>
            <i class="fa fa-map-marker"></i> <a href="$earthquake_url" target="_blank">$earthquake_place</a>
            <div class="row earthquake-info">
                <div class="col-sm-6">
                    <i class="wi wi-earthquake"></i>$obs.label.earthquake_magnitude <span class="magnitude">$earthquake_magnitude</span>
                </div>
                <div class="col-sm-6 earthquake-distance-outer border-left">
                    <span class="earthquake-distance">$earthquake_distance_away $earthquake_distance_label $earthquake_bearing</span>
                </div>
            </div>
            #end if
        </div>
    </div>
    #end if
</div>
<!-- End of third row -->
