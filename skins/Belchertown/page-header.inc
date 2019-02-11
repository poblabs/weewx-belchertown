<div class="wx-stn-info-container">
    <div class="row">
        <div class="col-sm-1 wx-stn-info-current-obs">
            <span class="obs-header-icon">$current_obs_icon</span>
            <span class="obs-header-outtemp">$current.outTemp</span>
        </div>
        <div class="col-sm-5">
            <div class="wx-stn-name">
		#if $page == "graphs"
                <h1>$Extras.graphs_page_header</h1>
		#else if $page == "records"
                <h1>$Extras.records_page_header</h1>
		#else if $page == "reports"
                <h1>$Extras.reports_page_header</h1>
		#else if $page == "records"
                <h1>$Extras.records_page_header</h1>
		#else if $page == "about"
                <h1>$Extras.about_page_header</h1>
		#end if
            </div>
        </div>
        <div class="col-sm-5" style="float:right;">
            <div class="wx-stn-info">
                Observations are powered by a <a href="$belchertown_root_url/about" target="_blank">Personal Weather Station</a>
            </div>
            #if $social_html != ""
            <div class="col-sm-10 wx-stn-info-social" style="float:right;">
                $social_html
            </div>
            #end if
        </div>
    </div>
    <div class="clear"></div>
</div>