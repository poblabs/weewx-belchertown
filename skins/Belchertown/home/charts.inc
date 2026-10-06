## Home page block "charts" (see home_sections in skin.conf)
#if 'highcharts_enabled' in $Extras and $Extras.highcharts_enabled == '1'
<!-- Begin of fourth row - dynamic charts -->
<div class="row highcharts-row graph">
    <div class="col-sm-12 wx-graph-front">
        <span class="homepage-graphgroup-title">$graphpage_titles_dict[$Extras.highcharts_homepage_graphgroup]</span> <a href="$relative_url/graphs">$obs.label.homepage_graphs_link</a>
    </div>
    
    <div class="graph-outer row"></div><!-- JS populated -->
    
</div>
<!-- End of fourth row -->
#end if
<div class="clear"></div>
