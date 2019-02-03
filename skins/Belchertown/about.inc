<p>This website is automatically updated in near real time (about every 2.5 seconds) with weather observations from a <a href="https://www.davisinstruments.com/solution/vantage-vue/" target="_blank">Davis Vantage Vue</a> personal weather station located in my backyard in Biltmore Lake, NC. Weather data, sent wirelessly to a Davis weather console in my home, is output and processed by the weeWX weather software running on a $35 <a href="https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus/" target="_blank">Raspberry Pi 3B+</a> single board computer which archives it and feeds the website. The weather station provides the following readings:</p>

<ul> 
     <li>Temperature
     <li>Humidity 
     <li>Wind speed  
     <li>Wind direction  
     <li>Rainfall  
     <li>Barometric Pressure
</ul>

<p>The rest of the observations indicated on this website are done via software calculations and quality control checks to make sure the data is valid.</p>

All weather observations are also posted to:

<br>
<ul>
      <li><a href="https://www.pwsweather.com/obs/KNCBL.html" target="_blank">KNCBL</a> on PWSWeather.com</li>
	  <li><a href="http://www.findu.com/cgi-bin/wxpage.cgi?last=24&amp;call=FW3054" target="_blank">FW3054</a> on CWOP</li>
	  <li><a href="https://www.wunderground.com/personal-weather-station/dashboard?ID=KNCCANDL38" target="_blank">KNCCANDL38</a> on Weather Underground</li>
</ul>

Software used:
<ul> 
     <li><a href="http://weewx.com/" target="_blank">weeWX</a> open source weather station software
     <li><a href="https://www.highcharts.com/" target="_blank">HighCharts</a> for the various charts on the website
     <li>A custom-built theme designed by Pat O'Brien (developer and owner of the <a href="https://belchertownweather.com/" target="_blank">belchertownweather.com</a> website).
     <li>ncat for a socket server that the weather station directly connects to for live station data
     <li><a href="https://mosquitto.org/" target="_blank">Eclipse Mosquitto</a> message broker using the MQTT protocol for instant data transfer from weather station to website
     <li>Custom PHP and JavaScript scripts, written and/or adapted by Pat O'Brien, to connect to the socket, parse the live station data and present it to you in real time
</ul>
 

Credits:

    <br>Special thanks to Pat O'Brien for his theme and personal help to me to implement it on my website!
    <br>Thanks to Thomas Keffer for developing weeWX and making it available to everyone
    <br>Support from members of the weewx-user group - many of whom have contributed to weeWX development and extensions to it
    <br>Forecast data Powered by <a href="https://darksky.net" target="_blank">Dark Sky</a>
    <br>Earthquake data from <a href="https://earthquake.usgs.gov/earthquakes/" target="_blank">USGS.gov</a> Earthquake Catalog Developer API

