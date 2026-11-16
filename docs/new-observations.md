# Adding a new observation

This page is for a sensor your station reports that weewx doesn't save yet, for example a soil temperature, a second rain gauge or an air quality reading. It shows how to add a place for it in the weewx database, check that readings arrive, and then show it on the Belchertown home page and in charts.

This page covers weewx 5, which Belchertown 3.0 requires. The commands start with `weectl`. Older guides use `wee_database`, which weewx 5 no longer has.

For anything this page doesn't cover, see the weewx documentation on [adding a new type to the database](https://weewx.com/docs/5.0/custom/database/).

## Before you start

You need the name of the reading as weewx receives it from your station (for example `soilTemp1` or `pm2_5`). Your station's driver decides this name. If you're not sure what it is, the weewx log or the driver's documentation will tell you.

Some readings are already in the database and need no change. A weewx 5 database normally has the `wview_extended` layout, which already includes `appTemp`, `windrun`, `cloudbase`, the `soilTemp`, `leafTemp` and `extraTemp` readings, `pm2_5` and many others. If yours is one of those, skip to [Show it on the skin](#show-it-on-the-skin).

## Step 1: Back up your database

A column can be removed again with `weectl database drop-columns`, but a copy of the database is the sure way back if anything goes wrong. Stop weewx, then copy the database file somewhere safe:

```
sudo systemctl stop weewx
```

Where the database is depends on how you installed weewx:

| How weewx was installed | Database file
| ----------------------- | -------------
| Package (`apt`, `yum`, `dnf`) | `/var/lib/weewx/weewx.sdb`
| `pip` | `~/weewx-data/archive/weewx.sdb`

For a package install, this makes a copy next to the original:

```
sudo cp /var/lib/weewx/weewx.sdb /var/lib/weewx/weewx.sdb.backup
```

If your weewx uses MySQL or MariaDB instead, back it up with `mysqldump` the way you normally do.

## Step 2: Add the column

Run `weectl database add-column` with the name of your reading. Tell it where `weewx.conf` is with `--config`:

| How weewx was installed | `weewx.conf` is at
| ----------------------- | ------------------
| Package | `/etc/weewx/weewx.conf`
| `pip` | `~/weewx-data/weewx.conf`

For example, to add `soilTemp5` on a package install:

```
sudo weectl database add-column soilTemp5 --config=/etc/weewx/weewx.conf
```

It asks you to confirm before it changes anything. To see every `weectl database` command and option:

```
weectl database --help
```

If the new column is one weewx can work out from other readings, such as `appTemp` or `windrun`, you can also fill in the past records:

```
sudo weectl database calc-missing --config=/etc/weewx/weewx.conf
```

## Step 3: Restart weewx and check that readings arrive

Start weewx again:

```
sudo systemctl start weewx
```

Wait for the next archive period (usually 5 minutes). Then look at the newest records. If `sqlite3` is installed, this shows the last five values of `soilTemp5` (use your own reading's name and database path):

```
sqlite3 /var/lib/weewx/weewx.sdb "SELECT datetime(dateTime, 'unixepoch', 'localtime'), soilTemp5 FROM archive ORDER BY dateTime DESC LIMIT 5;"
```

If the values are empty, weewx isn't receiving the reading under that name. Check the name your driver uses, and see the weewx documentation.

## Show it on the skin

The skin uses the weewx name of the reading everywhere. Restart weewx after each change below.

### On the home page

The readings listed next to the radar come from the `station_observations` option. Copy the default list into `weewx.conf` and add your reading to it:

```
[StdReport]
    [[Belchertown]]
        [[[Extras]]]
            station_observations = "barometer", "dewpoint", "outHumidity", "rainWithRainRate", "soilTemp5"
```

[All skin options](options.md) has more about this option.

### In a chart

Charts are set in `graphs.conf`. Each reading in a chart is a section with its name in triple brackets. This adds a chart for `soilTemp5` to the home page group:

```
[homepage]
    [[soil]]
        title = Soil Temperature
        [[[soilTemp5]]]
```

The [chart builder](charts/chart-builder.md) on your own site lists every reading in your database that has data from the last 30 days, so you can try the chart there and copy the text it gives you. Its list is refreshed once an hour, so a new reading shows up there an hour or so after its first data. The [charts documentation](charts/graphs-conf.md) explains every chart option.

### Give it a name

The skin shows each reading with a label. Add one under `[[[Labels]]]` → `[[[[Generic]]]]` in the `[[Belchertown]]` section of `weewx.conf`:

```
[StdReport]
    [[Belchertown]]
        [[[Labels]]]
            [[[[Generic]]]]
                soilTemp5 = "Garden Soil"
```

You can also put it in weewx's own `[StdReport]` → `[[Defaults]]` → `[[[Labels]]]` → `[[[[Generic]]]]` section, so every skin uses it.

### Tell weewx its unit

weewx knows the unit of every reading in its standard list. For a reading it doesn't know, such as an ozone (O3) sensor, it doesn't know the unit or how many decimals to show.

Belchertown 3.0 leaves such a reading as it is on charts. Before 3.0 the charts rounded it to a whole number, so a reading of 0.0343 ppm showed as 0 ([issue 935](https://github.com/poblabs/weewx-belchertown/issues/935)).

To give a new reading a unit, you assign it to a weewx unit group (for example `group_temperature` or `group_concentration`). Once it's in a group, it gets the group's unit and decimals. If the group is one the units button handles (temperature, wind, rain, pressure, distance or height), the button converts it too. The display unit of each group is chosen in `weewx.conf` under `[StdReport]` → `[[Defaults]]` → `[[[Units]]]` → `[[[[Groups]]]]`, as shown in [Use metric units](customize.md#use-metric-units). How to put a new reading into a group is described in the weewx documentation on [adding a new type](https://weewx.com/docs/5.0/custom/database/) and on [customizing units](https://weewx.com/docs/5.0/custom/units/).
