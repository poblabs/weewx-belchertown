## Home page block "charts" (see home_sections in skin.conf)
#if 'highcharts_enabled' in $Extras and $Extras.highcharts_enabled == '1'
<div class="highcharts-row graph">
    <div class="wx-section-head">
        <h2 class="wx-section-title homepage-graphgroup-title"><i class="fa fa-line-chart" aria-hidden="true"></i> $graphpage_titles_dict[$Extras.highcharts_homepage_graphgroup]</h2>
        <a class="wx-section-link" href="$relative_url/graphs">$obs.label.homepage_graphs_link</a>
    </div>
    <div class="graph-outer wx-chart-grid"></div><!-- JS populated -->
</div>
#end if
<div class="clear"></div>
