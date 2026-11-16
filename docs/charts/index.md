# Charts

Every chart on your site comes from one file, `graphs.conf`, in the Belchertown skin folder. It says which charts appear, what they show and over what time range. The skin ships with chart groups to start from (the home page, today, this week, this month, this year); if you don't have a `graphs.conf` yet, the skin uses `graphs.conf.example`.

There are three ways to get the charts you want:

* **[The chart builder](chart-builder.md)**: a page on your own site where you pick what to plot and watch it draw from your data, then copy the text into `graphs.conf`. The easiest way to start.
* **[The chart gallery](gallery.md)**: every kind of chart the skin can draw, with a picture and the text that made it, ready to paste.
* **[The graphs.conf reference](graphs-conf.md)**: how the file is organized and every setting it takes, with time ranges, grouping by month and year, and axis labels.

Charts can also go on [your own pages](custom-pages.md): the About page, a home page block, or a chart of numbers you keep yourself.

A change to `graphs.conf` shows up at the next report. There's no need to restart weewx; run `weectl report run` to see it right away.

## Highcharts or ECharts

The skin can draw its charts with either of two chart libraries. You choose one for the whole site; `graphs.conf` is the same for both.

| | Highcharts | Apache ECharts |
| --- | --- | --- |
| **License** | Free for personal and school websites only. A business, non-profit, club or government website needs a paid [Highcharts license](https://shop.highcharts.com/). | Free for any website ([Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)). |
| **Setting** | `chart_library = highcharts` (the default) | `chart_library = echarts` |
| **Every chart in graphs.conf** | Yes | Yes: lines, areas, columns, wind rose, Hays chart, temperature ranges, gauges and air quality |
| **Tooltips, dark mode, °F/°C button** | Yes | Yes |
| **Zoom** | Drag across a chart (computer), pinch (phone). | Drag across a chart, or click it to zoom in on that spot (computer); pinch (phone). |
| **Look** | The classic Belchertown charts | The same colors and layout with a few [modern touches](#whats-different-with-echarts) |
| **Download a picture** | PNG, JPEG, SVG, PDF and print | PNG |
| **Your own chart code** | `Highcharts.chart()` and [`draw_chart()`](custom-pages.md#a-chart-you-write-yourself) | Only [`draw_chart()`](custom-pages.md#a-chart-you-write-yourself) |

To see every chart side by side in both, open the [chart gallery](gallery.md) and switch between the tabs.

### Switching to ECharts

Add this to `weewx.conf`, then restart weewx (`sudo systemctl restart weewx`). The charts change at the next report:

```
[StdReport]
    [[Belchertown]]
        [[[Extras]]]
            chart_library = echarts
```

To switch back, change it to `highcharts` or remove the line, and restart weewx again.

### What's different with ECharts

* **Look:** the same colors and layout, with a few modern touches. The outside temperature line takes the skin's temperature colors, blue when cold and red when hot (add `temperature_colors = false` under the line in `graphs.conf` to keep its own color). Today's high and low and the top gust are marked on the day charts. A "Now" line shows on charts that run to midnight. Charts that cover months get a strip underneath for sliding through them. Lines draw in when the page opens, pointing at a legend item fades the other lines, columns have rounded tops, the grid is lighter, and the time shows on the bottom axis as you move across a chart.
* **Zoom:** on a computer, drag across a chart, or click a spot to zoom in on it. On a phone or tablet, pinch. "Reset zoom" appears in the corner while you're zoomed in, and a double click resets too.
* **Download:** `exporting = true` gives a button that saves the chart as a picture (PNG). Highcharts also offers JPEG, SVG, PDF and printing.
* **Highcharts options added by hand:** `graphs.conf` passes any Highcharts setting on a line straight to Highcharts. With ECharts the common ones carry over: `color`, `zIndex`, `lineWidth`, `marker`, `visible`, `dashStyle`, `step`, `zones` and `stacking`. Others are ignored.
* **type = bar** draws upright columns, the same as `column`. In Highcharts it draws sideways bars.
* **Stacked columns** stack in the opposite order: Highcharts puts the first observation on top, ECharts at the bottom.
* **Your own pages:** charts from `graphs.conf` on your own pages work with both. Code that calls `Highcharts.chart()` itself stops working, because Highcharts isn't loaded; change it to `draw_chart()` ([how](custom-pages.md#a-chart-you-write-yourself)).
* **Credits:** the "Highcharts.com" credit under each chart goes away. Your own `credits` text in `graphs.conf` is still shown.

Found a chart that looks wrong with ECharts? Please [open an issue](https://github.com/poblabs/weewx-belchertown/issues/new/choose) with its part of `graphs.conf`.
