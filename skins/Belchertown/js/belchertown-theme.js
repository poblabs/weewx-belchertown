function autoTheme(sunset_hour, sunset_min, sunrise_hour, sunrise_min) {
    // First check if ?theme= is in URL. If so, bail out and do not change anything. 
    if (getURLvar("theme") && getURLvar("theme") != "auto") {
        belchertown_debug("Auto theme: theme override detected in URL. Skipping auto theme");
        return true;
    }
    belchertown_debug("Auto theme: checking to see if theme needs to be switched");

    var d = new Date();
    var nowHour = d.getHours();
    var nowMinutes = d.getMinutes();
    nowHour = nowHour;
    sunrise_hour = sunrise_hour;
    sunset_hour = sunset_hour;

    // Determine if it's day time. https://stackoverflow.com/a/14718577/1177153
    if (sunrise_hour <= nowHour && nowHour < sunset_hour) {
        dayTime = true;
    } else {
        dayTime = false;
    }

    belchertown_debug("Auto theme: sunrise: " + sunrise_hour);
    belchertown_debug("Auto theme: now: " + nowHour);
    belchertown_debug("Auto theme: sunset: " + sunset_hour);
    belchertown_debug("Auto theme: are we in daylight hours: " + dayTime);
    belchertown_debug("Auto theme: sessionStorage.getItem('theme') = " + sessionStorage.getItem('theme'));

    if (dayTime == true) {
        // Day time, set light if needed
        // Only change theme if user has not overridden the auto option with the toggle
        if (sessionStorage.getItem('theme') == "auto") {
            belchertown_debug("Auto theme: setting light theme since dayTime variable is true (day)");
            changeTheme("light");
        } else {
            belchertown_debug("Auto theme: cannot set light theme since visitor used toggle to override theme. Refresh to reset the override.");
        }
    } else {
        // Night time, set dark if needed
        // Only change theme if user has not overridden the auto option with the toggle
        if (sessionStorage.getItem('theme') == "auto") {
            belchertown_debug("Auto theme: setting dark theme since dayTime variable is false (night)");
            changeTheme("dark");
        } else {
            belchertown_debug("Auto theme: cannot set dark theme since visitor used toggle to override theme. Refresh to reset the override.");
        }
    }
}

function changeTheme(themeName, toggleOverride = false) {
    belchertown_debug("Theme: Changing to " + themeName);
    // If the configured theme is auto, but the user toggles light/dark, remove the auto option.
    if (toggleOverride) {
        belchertown_debug("Theme: toggle override clicked.");
        belchertown_debug("Theme: sessionStorage.getItem('theme') was previously: " + sessionStorage.getItem('theme'));
        // This was applied only to auto theme config, but now it's applied to all themes so visitor has full control on light/dark mode
        //if ( sessionStorage.getItem('theme') == "auto" ) { }
        sessionStorage.setItem('theme', 'toggleOverride');
        belchertown_debug("Theme: sessionStorage.getItem('theme') is now: " + sessionStorage.getItem('theme'));
    }
    if (themeName == "dark") {
        // Apply dark theme
        if (config.radar_html_dark !== "None") {
        jQuery('.radar_image').html(config.radar_html_dark);
        }
        jQuery('body').addClass("dark");
        jQuery('body').removeClass("light");
        if (extras.theme_toggle_enabled === '1') {
        jQuery("#themeSwitch").prop("checked", true);
        }
        if (extras.logo_image_dark !== undefined && extras.logo_image_dark !== "") {
        belchertown_debug("Theme: logo_image_dark is defined.");
        jQuery("#logo_image").attr("src", extras.logo_image_dark);
        }
        sessionStorage.setItem('currentTheme', 'dark');
    } else if (themeName == "light") {
        // Apply light theme
        if (config.radar_html_dark !== "None") {
        jQuery('.radar_image').html(config.radar_html);
        }
        jQuery('body').addClass("light");
        jQuery('body').removeClass("dark");
        if (extras.theme_toggle_enabled === '1') {
        jQuery("#themeSwitch").prop("checked", false);
        }
        if (extras.logo_image !== undefined && extras.logo_image !== "") {
        belchertown_debug("Theme: logo_image is defined.");
        jQuery("#logo_image").attr("src", extras.logo_image);
        }
        sessionStorage.setItem('currentTheme', 'light');
    }
}
