<script type="text/javascript">
    var moment_locale = "$system_locale_js";
    moment.locale(moment_locale);

    jQuery(document).ready(function() {

      jQuery("#year-inTemp-max-ts").text( moment.unix($year.inTemp.maxtime.raw).format( "$obs.label.time_records_page_full_date" ) );
      jQuery("#at-inTemp-max-ts").text( moment.unix($alltime.inTemp.maxtime.raw).format( "$obs.label.time_records_page_full_date" ) );

      jQuery("#year-inTemp-min-ts").text( moment.unix($year.inTemp.mintime.raw).format( "$obs.label.time_records_page_full_date" ) );
      jQuery("#at-inTemp-min-ts").text( moment.unix($alltime.inTemp.mintime.raw).format( "$obs.label.time_records_page_full_date" ) );


    });
</script>



            <tr>
                <td class="records-header" colspan=5>$obs.label.records_inTemp_records</td>
            </tr>
            <tr>
                <td colspan=1> </td>
                <td class="records-header-year" colspan=2>$current.dateTime.format("%Y")</td>
                <td class="records-header-alltime" colspan=2>$obs.label.records_all_time</td>
            </tr>
            <tr>
                <td>$obs.label.records_high_inTemp</td>
                <td class="leftborder">$year.inTemp.max</td>
                <td><span id="year-inTemp-max-ts"></span></td><!-- moment.js -->
                <td class="leftborder"><span id="at-inTemp-max-ts"></span></td><!-- moment.js -->
                <td>$alltime.inTemp.max</td>
            </tr>
            <tr>
                <td>$obs.label.records_low_inTemp</td>
                <td class="leftborder">$year.inTemp.min</td>
                <td id="year-inTemp-min-ts"></td><!-- moment.js -->
                <td class="leftborder" id="at-inTemp-min-ts"></td><!-- moment.js -->
                <td>$alltime.inTemp.min</td>
            </tr>
