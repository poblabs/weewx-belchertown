---
name: Bug report
about: Something in the skin isn't working
title: ''
labels: 'bug'
assignees: ''

---
Thanks for the report. The questions below come up on almost every issue, so answering them here saves a round trip. Delete any that don't apply.

**What's wrong?**
A sentence or two. If a page is blank or something is missing, say which page.

**Your setup**
- weewx version (`weectl --version`):
- Belchertown version (in the footer of your site, or `weectl extension list`):
- How weewx was installed: package (apt/yum), pip, or git
- Database: SQLite or MySQL/MariaDB
- Link to your website, if it's online (this helps more than anything else):

**What the weewx log says**
Paste the lines that mention `belchertown` from around the time of the problem. On most systems: `sudo journalctl -u weewx -n 300`, or look in `/var/log/syslog`. If there's nothing useful, turn on debug mode (see [Debug mode](https://github.com/poblabs/weewx-belchertown#debug-mode)), wait for the next report and look again.

**If it's something you see in the browser** (a layout problem, a button that does nothing, a chart that doesn't draw)
- Device and browser:
- Press F12, open the "Console" tab, reload the page and paste any red lines here:

**Your settings**
The `[[Belchertown]]` section of your `weewx.conf`, and `graphs.conf` or any `.inc` file if the problem involves them. Remove passwords and API keys first.

**Screenshot**
If you can see the problem, a screenshot helps.
