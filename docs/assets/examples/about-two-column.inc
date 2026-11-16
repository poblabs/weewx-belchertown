#encoding UTF-8
<style>
    .about-cols { display: grid; grid-template-columns: 1fr 2fr; gap: 30px; margin-top: 15px; }
    .about-cols img { max-width: 100%; margin-bottom: 10px; }
    .about-facts { font-size: 90%; margin: 0 auto; }
    .about-facts td { padding: 4px 8px 0 0; }
    .about-facts td:first-child { text-align: right; }
    .about-facts td:last-child { font-weight: bold; }
    @media (max-width: 800px) { .about-cols { grid-template-columns: 1fr; } }
</style>
<script>showChart("about");</script>

<div class="entry-content about-outer" itemprop="text">
<div class="about-cols">

    <div>
        <a href="https://example.com/webcam/latest.jpg" target="_blank"><img src="https://example.com/webcam/latest.jpg" alt="Webcam"></a>
        <img src="https://example.com/station-photo.jpg" alt="The weather station">
        <table class="about-facts">
            <tr><td>Hardware</td><td>$station.hardware</td></tr>
            <tr><td>Location</td><td>$station.location</td></tr>
            <tr><td>Altitude</td><td>$station.altitude</td></tr>
            #if $day.rxCheckPercent.has_data
            <tr><td>Signal quality</td><td>$current.rxCheckPercent</td></tr>
            #end if
            #if $day.txBatteryStatus.has_data
            <tr><td>Transmitter battery</td><td>#if $current.txBatteryStatus.raw == 0#<span style="color:#44aa44;">OK</span>#else#<span style="color:#aa4444;">LOW</span>#end if#</td></tr>
            #end if
            #if $day.consBatteryVoltage.has_data
            <tr><td>Console battery</td><td>$current.consBatteryVoltage</td></tr>
            #end if
            <tr><td>weewx version</td><td>$station.version</td></tr>
            <tr><td><a href="https://poblabs.github.io/weewx-belchertown/" target="_blank">Belchertown skin</a></td><td>$belchertown_version</td></tr>
        </table>
        <div id="aboutchart1" style="margin-top:30px;"></div>
        <div id="aboutchart2" style="margin-top:30px;"></div>
    </div>

    <div>
        <p>This website is updated automatically with readings from a $station.hardware weather station in $station.location. Tell your visitors a little about it here: where it sits, how long it has been running, and who looks after it.</p>

        <p>The station measures:</p>
        <ul>
            <li>Temperature and humidity</li>
            <li>Wind speed and direction</li>
            <li>Rainfall</li>
            <li>Barometric pressure</li>
        </ul>

        <p>Its readings are also shared with:</p>
        <ul>
            <li><a href="https://www.wunderground.com/dashboard/pws/YOURID" target="_blank">YOURID</a> on Weather Underground</li>
            <li><a href="https://www.pwsweather.com/station/pws/YOURID" target="_blank">YOURID</a> on PWSweather</li>
        </ul>

        <p>Software used:</p>
        <ul>
            <li><a href="https://weewx.com/" target="_blank">weewx</a> weather station software</li>
            <li>The <a href="https://poblabs.github.io/weewx-belchertown/" target="_blank">Belchertown skin</a> for weewx</li>
            <li>#if $chart_library == "echarts"#<a href="https://echarts.apache.org/" target="_blank">Apache ECharts</a>#else#<a href="https://www.highcharts.com/" target="_blank">Highcharts</a>#end if# for the charts</li>
        </ul>

        <p>Credits:</p>
        <ul>
            <li>Forecast from <a href="https://open-meteo.com/" target="_blank">Open-Meteo</a> and alerts from the <a href="https://www.weather.gov/" target="_blank">National Weather Service</a></li>
            <li>Earthquake data from the <a href="https://earthquake.usgs.gov/" target="_blank">USGS</a></li>
        </ul>
    </div>

</div>
</div>
