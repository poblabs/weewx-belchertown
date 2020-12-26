## celestial module for weewx skins
## Copyright Tom Keffer, Matthew Wall
## See LICENSE.txt for your rights
#errorCatcher Echo
## If extended almanac information is available, do extra calculations.
#if $almanac.hasExtras
  #import locale
  #set $sun_azimuth = locale.format_string( "%.1f&deg;", $almanac.sun.az )
  #set $sun_ra = locale.format_string( "%.1f&deg;", $almanac.sun.ra )
  #set $sun_dec = locale.format_string( "%.1f&deg;", $almanac.sun.dec )
  #set $moon_azimuth = locale.format_string( "%.1f&deg;", $almanac.moon.az )
  #set $moon_altitude = locale.format_string( "%.1f&deg;", $almanac.moon.alt )
  #set $moon_ra = locale.format_string( "%.1f&deg;", $almanac.moon.ra )
  #set $moon_dec = locale.format_string( "%.1f&deg;", $almanac.moon.dec )
  #set $sun_altitude = $almanac.sun.alt
  #if $sun_altitude < 0
    #set $sun_None="<i>(%s)</i>" % $obs.label.sun_always_down
    #set $daylight_str = "00:00"
  #else
    #set $sun_None="<i>(%s)</i>" % $obs.label.sun_always_up
    #set $daylight_str = "24:00"
  #end if
  #set $sunrise_ts = $almanac.sun.rise.raw
  #set $sunset_ts = $almanac.sun.set.raw
  #if $sunrise_ts and $sunset_ts
    #set $now = $current.dateTime.raw
    #set $today_daylight = $sunset_ts -  $sunrise_ts
    #set $seconds = $today_daylight
    #set $hours = $seconds // 3600
    #set $seconds %= 3600
    #set $minutes = $seconds // 60
    #set $seconds %= 60
    #set $daylight_str = "%d %s, %d %s, %d %s" % ($hours, $obs.label.hour[0] if ( $hours == 1 ) else $obs.label.hour[1], $minutes, $obs.label.minute[0] if ( $minutes == 1 ) else $obs.label.minute[1], $seconds, $obs.label.second[0] if ( $seconds == 1 ) else $obs.label.second[1])
    #set $yesterday = $now - 24*3600
    #set $yesterday_daylight = $almanac($almanac_time=$yesterday).sun.set.raw - $almanac($almanac_time=$yesterday).sun.rise.raw
    #set $difference = $today_daylight - $yesterday_daylight
    #if $difference
      #set $delta = abs($difference)
      #set $minute_difference = (int($delta) // 60)
      #set $minutes_text = $obs.label.minute[0] if ( $minute_difference == 1 ) else $obs.label.minute[1]
      #set $seconds_text = $obs.label.second[0] if ( int($delta) == 1 ) else $obs.label.second[1]
      #set $amt_str = "%s%d %s" % (str(int($delta) // 60) + ' ' + $minutes_text + ', ' if ($delta // 60) > 0 else '', $delta % 60 if ($delta // 60) > 0 else $delta, $seconds_text)
      #if $difference > 0
        #set $delta_str = "%s %s" % ( $amt_str, $obs.label.more_than_yesterday )
      #else
        #set $delta_str = "%s %s" % ( $amt_str, $obs.label.less_than_yesterday )
      #end if
      #set $daylight_str = "%s<br/>%s" % ($daylight_str, $delta_str)
    #end if
  #end if
  #set $sun_altitude = locale.format_string( "%.1f&deg;", $almanac.sun.alt )
#end if
## Compressed for the weewx_data.json file to stay consistent
<div id='celestial_widget' class='widget'> <div class='widget_contents'> <div id='celestial_details'> <div class='celestial_body'> <table class='celestial'> <tr><th>&#9728; $obs.label.sun</th><th></th></tr> <tr> <td class='label'>$obs.label.start_civil_twilight</td> <td class='data'>$almanac(horizon=-6).sun(use_center=1).rise</td> </tr> <tr> <td class='label'>$obs.label.rise</td> <td class='data'>$almanac.sun.rise.format(None_string=$sun_None)</td> </tr> <tr> <td class='label'>$obs.label.transit</td> <td class='data'>$almanac.sun.transit</td> </tr> <tr> <td class='label'>$obs.label.set</td> <td class='data'>$almanac.sun.set.format(None_string=$sun_None)</td> </tr> <tr> <td class='label'>$obs.label.end_civil_twilight</td> <td class='data'>$almanac(horizon=-6).sun(use_center=1).set</td> </tr> <tr> <td class='label'>$obs.label.azimuth</td> <td class='data'>$sun_azimuth</td> </tr> <tr> <td class='label'>$obs.label.altitude</td> <td class='data'>$sun_altitude</td> </tr> <tr> <td class='label'>$obs.label.right_ascension</td> <td class='data'>$sun_ra</td> </tr> <tr> <td class='label'>$obs.label.declination</td> <td class='data'>$sun_dec</td> </tr>#slurp
#if $almanac.next_equinox.raw < $almanac.next_solstice.raw
## The equinox is before the solstice. Display them in order.
<tr><td class='label'>$obs.label.equinox</td><td class='data'>$almanac.next_equinox</td></tr><tr><td class='label'>$obs.label.solstice</td><td class='data'>$almanac.next_solstice</td></tr>#slurp
#else
## The solstice is before the equinox. Display them in order.
<tr><td class='label'>$obs.label.solstice</td><td class='data'>$almanac.next_solstice</td></tr><tr><td class='label'>$obs.label.equinox</td><td class='data'>$almanac.next_equinox</td></tr>#slurp
#end if
<tr> <td class='label'>$obs.label.total_daylight</td> <td class='data'>$daylight_str</td> </tr> </table> </div> <div class='celestial_body'> <table class='celestial'> <tr><th>&#9789; $obs.label.moon</th><th></th></tr> <tr><td class='label'>&nbsp;</td><td class='data'>&nbsp;</td></tr> <tr> <td class='label'>$obs.label.rise</td> <td class='data'>$almanac.moon.rise</td> </tr> <tr> <td class='label'>$obs.label.transit</td> <td class='data'>$almanac.moon.transit</td> </tr> <tr> <td class='label'>$obs.label.set</td> <td class='data'>$almanac.moon.set</td> </tr> <tr><td class='label'>&nbsp;</td><td class='data'>&nbsp;</td></tr> <tr> <td class='label'>$obs.label.azimuth</td> <td class='data'>$moon_azimuth</td> </tr> <tr> <td class='label'>$obs.label.altitude</td> <td class='data'>$moon_altitude</td> </tr> <tr> <td class='label'>$obs.label.right_ascension</td> <td class='data'>$moon_ra</td> </tr> <tr> <td class='label'>$obs.label.declination</td> <td class='data'>$moon_dec</td> </tr>#slurp
#if $almanac.next_full_moon.raw < $almanac.next_new_moon.raw
<tr> <td class='label'>$obs.label.full_moon</td> <td class='data'>$almanac.next_full_moon</td> </tr> <tr> <td class='label'>$obs.label.new_moon</td> <td class='data'>$almanac.next_new_moon</td> </tr>#slurp
#else
<tr> <td class='label'>$obs.label.new_moon</td> <td class='data'>$almanac.next_new_moon</td> </tr> <tr> <td class='label'>$obs.label.full_moon</td> <td class='data'>$almanac.next_full_moon</td> </tr>#slurp
#end if
<tr> <td class='label'>$obs.label.phase</td> <td class='data'>$almanac.moon_phase<br/> $almanac.moon_fullness% $obs.label.full</td> </tr> </table> </div> </div> </div> </div> <div class='clear'></div><div class='almanac_last_updated'></div>
