#encoding UTF-8
<div class="wx-stn-info-container wx-page-header">
    <div class="wx-stn-info-current-obs">
        <span class="obs-header-icon">
            #if "forecast_enabled" in $Extras and $Extras.forecast_enabled == '1' and $current_obs_icon != ""
            <img id="wxicon" src="$relative_url/images/$current_obs_icon" alt="">
            #end if
        </span>
        <span class="obs-header-outtemp">$current.outTemp</span>
    </div>
    <div class="wx-stn-name">
        #if $page == "graphs"
        <h1>$obs.label.graphs_page_header</h1>
        #else if $page == "records"
        <h1>$obs.label.records_page_header</h1>
        #else if $page == "reports"
        <h1>$obs.label.reports_page_header</h1>
        #else if $page == "about"
        <h1>$obs.label.about_page_header</h1>
        #end if
    </div>
    <div class="wx-page-header-info">
        <div class="wx-stn-info">
            $obs.label.powered_by
        </div>
        #if $social_html != ""
        <div class="wx-stn-info-social">
            $social_html
        </div>
        #end if
    </div>
</div>
