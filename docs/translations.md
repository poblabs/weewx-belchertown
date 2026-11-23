# Translations

Every piece of text on a Belchertown site is a "label": the page headings, the menu, the forecast words, the chart buttons. Labels can be changed one at a time, or a whole language file can replace them all at once. This page explains both, and how to write a new language.

Dates, numbers and units have their own settings, covered at the end.

## Languages that come with the skin

Belchertown includes five language files, in the `lang` folder of the skin:

| Language | Setting | File | Written by
| -------- | ------- | ---- | ----------
| Catalan | `lang = ca` | `lang/ca.conf` | Dani Talens, based on the German file
| German | `lang = de` | `lang/de.conf` | Johanna Roedenbeck
| French | `lang = fr` | `lang/fr.conf` | trollix
| Italian | `lang = it` | `lang/it.conf` | Daniele Putti
| Swedish | `lang = sv` | `lang/sv.conf` | jorgbj (since 3.2.3)

Without a `lang` setting the site is in English.

## Turn on a language

1. Open `weewx.conf` in a text editor. It's at `/etc/weewx/weewx.conf` if you installed weewx as a package (`apt`, `yum`, `dnf`), or `~/weewx-data/weewx.conf` if you installed it with `pip`.
2. Find the `[[Belchertown]]` section under `[StdReport]` and add a `lang` line:

   ```
   [StdReport]
       [[Belchertown]]
           skin = Belchertown
           lang = fr
   ```

3. Save the file and restart weewx:

   ```
   sudo systemctl restart weewx
   ```

The pages change language at the next report.

A language file can also set a few options. The German, French, Catalan and Swedish files set `forecast_units = si` (metric forecasts) and `forecast_lang` (the language of Xweather alert text); the Italian file sets `forecast_units = ca`. Anything you set yourself under `[[[Extras]]]` in `weewx.conf` wins over the language file.

### Dates and numbers

The month and day names, and whether numbers use a decimal point or a comma, follow the `belchertown_locale` option. Its default, `"auto"`, uses your server's setting. To choose one yourself:

```
[StdReport]
    [[Belchertown]]
        lang = fr
        [[[Extras]]]
            belchertown_locale = "fr_FR.UTF-8"
```

The locale must be installed on your server first (on Debian and Ubuntu, `sudo dpkg-reconfigure locales`). To change the date formats themselves, open "Dates and times in your language" under [Change the site title and other text](customize.md#change-the-site-title-and-other-text).

## Missing labels fall back to English

A language file only needs the labels it changes. Any label it leaves out is taken from the English in `skins/Belchertown/skin.conf`, under `[Labels]` → `[[Generic]]`.

So a partial translation works. The untranslated parts show in English until someone translates them.

## Change one label without a language file

To change a single piece of text, for example the home page heading, put that label under `[[[Labels]]]` → `[[[[Generic]]]]` in the `[[Belchertown]]` section of `weewx.conf`:

```
[StdReport]
    [[Belchertown]]
        skin = Belchertown
        lang = fr
        [[[Labels]]]
            [[[[Generic]]]]
                home_page_header = "La météo à Belchertown"
                footer_copyright_text = "Ma station météo"
```

This works with or without a `lang` setting, and it wins over the language file. Put your changes here rather than in `skin.conf` or a file in `lang`: the skin's folder is replaced when you upgrade, and your changes there would be lost.

The full list of labels is in `skin.conf` under `[Labels]` → `[[Generic]]`. [Change the site title and other text](customize.md#change-the-site-title-and-other-text) lists the most common ones.

## Write a new language

These steps make a file for a language the skin doesn't have yet. `xx` stands for the two-letter code of your language, for example `es` for Spanish or `nl` for Dutch.

1. Open `skins/Belchertown/skin.conf` in a text editor and find the `[Labels]` section. Copy the whole `[[Generic]]` block under it, down to the next line that starts with a single `[` (that's `[Almanac]`).
2. Make a new file with this at the top, then paste the block under it:

   ```
   # Language file for Spanish, by Your Name

   [Labels]
   ```

3. Translate the text after each `=` sign. Leave the label names on the left as they are. You can delete any label you don't translate; it will show in English.
4. Optional: copy the `[Almanac]` (moon phase names) and `[Units]` → `[[Labels]]` (the words for day, hour, minute) sections from one of the existing language files and translate those too.
5. Save the file as `xx.conf` in the `skins/Belchertown/lang` folder, with UTF-8 encoding. Most text editors have an encoding choice in their Save As window.
6. Add `lang = xx` under `[[Belchertown]]` in `weewx.conf`, restart weewx, and check every page.

Keep a copy of your file outside the skin folder, because an upgrade replaces that folder. Better still, send it in so it comes with the skin (see [Share your translation](#share-your-translation)).

### What still needs translating in 3.0

Belchertown 3.0 added many labels that none of the four language files has yet. They show in English in every language today, and they're the best place to start if you'd like to help:

* `view_toggle_title`, `view_dashboard`, `view_forecast`, `view_radar`, `view_charts` (the home page layout button)
* `unit_toggle_title` and `menu_toggle_title` (the units and menu buttons)
* every label that starts with `chart_builder_` (the chart builder page)
* every label that starts with `onthisday_` (the "On this day" block)
* the new `records_` labels: `records_yearly_rainfall`, `records_set_this_year`, `records_none_this_year`, `records_on_this_day`, `records_so_far`, `records_warmest`, `records_coldest`, `records_wettest`

Some `onthisday_` labels contain `{year}` or `{date}`. Keep those words in braces exactly as they are; the skin fills in the year or date there.

## Two things that break a language file

The language files are read by the same reader as `weewx.conf` (called configobj). One mistake in a file stops the whole skin, not just the language. Before 3.0, a stray quote in `ca.conf` and a label listed twice in `it.conf` meant `lang = ca` and `lang = it` produced no site at all.

Watch for these:

* **Quotes must come in pairs.** If a text contains a comma, put the whole text in double quotes, or it is read as a list: `reports_click_here_link = "Cliquez ici,"`. If a text contains a double quote, wrap it in single quotes instead.
* **Each label only once.** The same label name twice in a section is an error.
* **`graphs_windDir_ordinals` must keep its quoting.** It is not plain text. It's a small piece of JavaScript that maps compass degrees to the letters on the wind direction chart. Change only the letters inside the double quotes, and keep the single quotes around the whole thing:

  ```
  graphs_windDir_ordinals = '{ 0: "N", 90: "E", 180: "S", 270: "O", 360: "N" }'
  ```

To check a file before you restart weewx, run this (with your file's name). It prints `ok`, or the line with the problem:

```
python3 -c "import configobj; configobj.ConfigObj('xx.conf', encoding='utf-8', file_error=True); print('ok')"
```

If you installed weewx with `pip`, use the Python in weewx's own environment instead of `python3`, for example `~/weewx-venv/bin/python3`.

If the site stops updating after you add a language, look in the weewx log (`sudo journalctl -u weewx`) for an error that names the file.

## Share your translation

New and improved translations are welcome.

1. Fork [poblabs/weewx-belchertown](https://github.com/poblabs/weewx-belchertown) on GitHub.
2. Add or change only the file in `skins/Belchertown/lang`. Keep other changes out of the same pull request.
3. Put your name in a comment at the top of the file, so you get credit.
4. Open a pull request that says which language it is and which pages you checked.

If you'd rather not use GitHub, attach the file to a new [issue](https://github.com/poblabs/weewx-belchertown/issues) instead.

## Units

Temperature, wind, rain and pressure units are not part of the language. They follow your weewx settings: see [Use metric units](customize.md#use-metric-units). Visitors can also switch between US and metric units with the [units button](customize.md#units-button-f-or-c).

## Getting help

Ask in the skin's [Questions and help](https://github.com/poblabs/weewx-belchertown/discussions/categories/q-a) discussions. For a bug in the skin or a mistake in a language file, open an [issue](https://github.com/poblabs/weewx-belchertown/issues/new/choose).
