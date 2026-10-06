## Home page block "snapshot" (see home_sections in skin.conf)
<section class="eq-stats-row wx-snapshot">
    <div class="snapshot-records-text">
        $obs.label.weather_snapshots <a href="$relative_url/records">$obs.label.weather_snapshots_link</a>
    </div>
    <div class="wx-snapshot-cards">
        <div class="wx-snapshot-card">
            <h3 class="stats-title"><span class="snapshot-records-today-header"></span></h3><!-- JS -->
            <dl class="wx-stats">
                <div><dt>$obs.label.snapshot_high</dt><dd class="dailystatshigh">$day.outTemp.max</dd></div>
                <div><dt>$obs.label.snapshot_low</dt><dd class="dailystatslow">$day.outTemp.min</dd></div>
                <div><dt>$obs.label.snapshot_today_rain</dt><dd class="dailystatsrain">$day.rain.sum</dd></div>
                <div><dt>$obs.label.snapshot_today_avg_wind</dt><dd class="dailystatswindavg">$day.wind.avg</dd></div>
                <div><dt>$obs.label.snapshot_today_high_wind</dt><dd class="dailystatswindmax">$day.wind.max</dd></div>
                <div><dt>$obs.label.snapshot_today_rainrate</dt><dd class="dailystatsrainrate">$day.rainRate.max</dd></div>
            </dl>
        </div>
        <div class="wx-snapshot-card">
            <h3 class="stats-title"><span class="snapshot-records-month-header"></span></h3><!-- JS -->
            <dl class="wx-stats">
                <div><dt>$obs.label.snapshot_high</dt><dd class="monthstatshigh">$month.outTemp.max</dd></div>
                <div><dt>$obs.label.snapshot_low</dt><dd class="monthstatslow">$month.outTemp.min</dd></div>
                <div><dt>$obs.label.snapshot_month_rain</dt><dd class="monthstatsrain">$month.rain.sum</dd></div>
                <div><dt>$obs.label.snapshot_month_avg_wind</dt><dd class="monthstatswindavg">$month.wind.avg</dd></div>
                <div><dt>$obs.label.snapshot_month_high_wind</dt><dd class="monthstatswindmax">$month.wind.max</dd></div>
                <div><dt>$obs.label.snapshot_month_rainrate</dt><dd class="monthstatsrainrate">$month.rainRate.max</dd></div>
            </dl>
        </div>
        #if 'earthquake_enabled' in $Extras and $Extras.earthquake_enabled == '1'
        <div class="wx-snapshot-card wx-quake">
            <h3 class="stats-title">$obs.label.earthquake_title</h3>
            <div class="eq-region">
                <span class="earthquake-time"></span><!-- JS -->
                #if $earthquake_place != ''
                <div><i class="fa fa-map-marker"></i> <a href="$earthquake_url" target="_blank">$earthquake_place</a></div>
                <div class="earthquake-info">
                    <span><i class="wi wi-earthquake"></i> $obs.label.earthquake_magnitude <span class="magnitude">$earthquake_magnitude</span></span>
                    <span class="earthquake-distance">$earthquake_distance_away $earthquake_distance_label $earthquake_bearing</span>
                </div>
                #end if
            </div>
        </div>
        #end if
    </div>
</section>
