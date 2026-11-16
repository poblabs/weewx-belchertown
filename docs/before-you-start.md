# Before you start

This page is for anyone who hasn't done this before. It covers what you need, how to type commands on the computer that runs weewx, and how to change a settings file. If you've installed a weewx extension before, skip to [Install](install.md).

## What you need

* **weewx 5.0 or newer, already running and saving data from your station.** Belchertown is a website theme for weewx; it doesn't talk to your station itself. If you don't have weewx yet, follow the [weewx documentation](https://weewx.com/docs/) (its "Quick start" guides cover each kind of computer) first. To check your version, type `weectl --version` (see [Typing commands](#typing-commands) below). It should say 5.0 or higher.
* **A web server** on the same computer, so other people (and your own phone) can open the site. weewx itself only writes the web pages to a folder; the web server is what shows them. If you can already see weewx's standard "Seasons" pages in a browser, you have one. If not, on a Raspberry Pi or other Debian or Ubuntu computer, this installs one:

    ```
    sudo apt install nginx
    ```

    Then open `http://` followed by the computer's name or address in a browser on the same network, for example `http://raspberrypi.local`. A "Welcome to nginx" page means it's working.

* **About 15 minutes.** Nothing you do here changes your weather data. The worst case is a website that doesn't look right yet, and everything can be undone.

## Typing commands

Installing and setting up the skin is done by typing commands on the computer that runs weewx. You type a line, press Enter, and the computer answers.

=== "On the Raspberry Pi itself"

    With a screen and keyboard on the Pi, open the **Terminal** from the menu (the black icon with `>_` in the top bar).

=== "From a Windows computer"

    Open **PowerShell** from the Start menu, then connect to the weewx computer with `ssh` followed by your user name, `@`, and the computer's name or address:

    ```
    ssh pi@raspberrypi.local
    ```

    Type `yes` the first time it asks about the computer's fingerprint, then your password. (The password doesn't show as you type; that's normal.)

=== "From a Mac"

    Open **Terminal** (in Applications → Utilities), then connect the same way:

    ```
    ssh pi@raspberrypi.local
    ```

In this guide, every gray box is something to type (or copy and paste). **Copy one box at a time**, paste it, and press Enter. The copy button appears at the right of each box when you point at it.

A few things that help:

* **`sudo`** at the start of a command runs it as the administrator. It may ask for your password the first time.
* **Pasting into a terminal:** right-click (Windows), Command + V (Mac), or Ctrl + Shift + V (Raspberry Pi).
* **Stopping something** that keeps running: press Ctrl + C. **Leaving a screen** that shows `(END)` or a long list: press `q`.

## Which kind of weewx you have

weewx can be installed two ways, and its files are in different places for each. Find out which you have by typing:

```
ls /etc/weewx/weewx.conf ~/weewx-data/weewx.conf
```

One of the two lines answers with the file name; the other says "No such file or directory".

| If this one exists | You have a | weewx.conf | Belchertown files | weewx's website folder |
| --- | --- | --- | --- | --- |
| `/etc/weewx/weewx.conf` | **package** install (`apt`, `yum`, `dnf`) | `/etc/weewx/weewx.conf` | `/etc/weewx/skins/Belchertown` | `/var/www/html/weewx` |
| `~/weewx-data/weewx.conf` | **pip** install | `~/weewx-data/weewx.conf` | `~/weewx-data/skins/Belchertown` | `~/weewx-data/public_html` |

Remember which one you have; the rest of the guide refers to this table.

!!! note "pip install: turn on weewx's Python first"
    On a pip install, `weectl` only works after you turn on the Python environment weewx was installed into. With the standard steps from the weewx guide, that's:

    ```
    source ~/weewx-venv/bin/activate
    ```

    Do this each time you open a new terminal. On a package install, `weectl` always works.

## Changing a settings file

Most settings live in `weewx.conf`, a plain text file. The simplest way to change it is **nano**, a text editor that runs in the terminal. For a package install:

```
sudo nano /etc/weewx/weewx.conf
```

For a pip install:

```
nano ~/weewx-data/weewx.conf
```

In nano:

* Move around with the **arrow keys**. Type to add text, Backspace to delete.
* **Find** something: Ctrl + W, type what you're looking for (for example `[[Belchertown]]`), press Enter.
* **Save**: Ctrl + O, then Enter.
* **Leave**: Ctrl + X.

!!! warning "Spaces matter in weewx.conf"
    Sections are marked with square brackets, and more brackets mean deeper inside: `[StdReport]` contains `[[Belchertown]]`, which contains `[[[Extras]]]`. Keep each setting under the right heading and line it up with its neighbors, using spaces, not tabs. Text in quotes (`"like this"`) is safest for anything with spaces or punctuation.

**After changing `weewx.conf`, restart weewx** so it reads the file again:

```
sudo systemctl restart weewx
```

Then check that it's running:

```
sudo systemctl status weewx
```

Look for `active (running)` in green. Press `q` to leave. If it says `failed`, the last few lines usually say why, often a typo in `weewx.conf`. The [weewx log](troubleshooting.md#debug-mode) has the full story.

!!! tip "Keep a copy before you change anything"
    One command saves a dated copy of `weewx.conf` next to the original (package install shown; for pip, use `~/weewx-data/weewx.conf` in both places and leave out `sudo`):

    ```
    sudo cp /etc/weewx/weewx.conf /etc/weewx/weewx.conf.$(date +%Y%m%d)
    ```

    If something goes wrong, copy it back the other way and restart weewx.

## Words you'll see

| Word | What it means |
| --- | --- |
| **weewx** | The free program that collects readings from your weather station, saves them, and builds web pages from them. |
| **Skin** | A design for those web pages. weewx comes with "Seasons"; Belchertown is another one. You can run both. |
| **Extension** | An add-on for weewx. Belchertown is installed as one, with `weectl extension install`. |
| **weewx.conf** | weewx's main settings file. Belchertown's settings go in its `[[Belchertown]]` section. |
| **Archive period** | How often weewx saves a record, usually every 5 minutes. The website is rebuilt after each one. |
| **Report** | One run of building the website. "At the next report" means within one archive period. |
| **HTML_ROOT** | The folder weewx writes a skin's web pages into. Your web server shows what's in it. |
| **graphs.conf** | The file that lists your charts. See [Charts](charts/index.md). |
| **MQTT** | A small messaging system that makes the home page update every few seconds. Optional; see [Live updates](live-updates.md). |

Ready? Go to [Install](install.md).
