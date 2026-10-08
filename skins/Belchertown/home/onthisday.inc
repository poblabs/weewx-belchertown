## Home page block "onthisday" (see home_sections in skin.conf): today against the same date in past years
#set $otd = $on_this_day_summary
#if $otd
#set $otd_date = '<time data-ts="%s" data-format="time_records_page_rainfall_range_begin"></time>' % $current.dateTime.raw
<section class="wx-onthisday">
    <div class="wx-section-head">
        <h2 class="wx-section-title"><i class="fa fa-calendar" aria-hidden="true"></i> $obs.label.records_on_this_day $otd_date</h2>
        <a class="wx-section-link" href="$relative_url/records/#on-this-day">$obs.label.onthisday_link</a>
    </div>
    #if $otd.note
    #set $note = str($obs.label["onthisday_" + $otd.note]).replace("{date}", $otd_date).replace("{year}", str($otd.note_year))
    <p class="wx-otd-note wx-otd-$otd.note">$note</p>
    #end if
    <div class="wx-otd-scale">
        <div class="wx-otd-end wx-otd-cold">
            <div class="wx-otd-label">$obs.label.onthisday_record_low</div>
            <div class="wx-otd-value">$otd.low</div>
            <div class="wx-otd-year">$str($obs.label.onthisday_record_year).replace("{year}", str($otd.low_year))</div>
        </div>
        <div class="wx-otd-track">
            <span class="wx-otd-average" style="left: ${otd.avg_bar.left}%; width: ${otd.avg_bar.width}%"></span>
            #if $otd.today_bar
            <span class="wx-otd-today" style="left: ${otd.today_bar.left}%; width: ${otd.today_bar.width}%"></span>
            #end if
        </div>
        <div class="wx-otd-end wx-otd-warm">
            <div class="wx-otd-label">$obs.label.onthisday_record_high</div>
            <div class="wx-otd-value">$otd.high</div>
            <div class="wx-otd-year">$str($obs.label.onthisday_record_year).replace("{year}", str($otd.high_year))</div>
        </div>
    </div>
    <div class="wx-otd-legend">
        #if $otd.today
        <span class="wx-otd-legend-today"><i class="wx-otd-key wx-otd-key-today"></i>$obs.label.onthisday_today: $otd.today.low – $otd.today.high</span>
        #end if
        <span><i class="wx-otd-key wx-otd-key-average"></i>$obs.label.onthisday_average: $otd.avg_low – $otd.avg_high</span>
        #if $otd.wettest
        <span><i class="wi wi-raindrop" aria-hidden="true"></i> $obs.label.onthisday_wettest: $otd.wettest ($otd.wettest_year)</span>
        #end if
    </div>
</section>
#end if
