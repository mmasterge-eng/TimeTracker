# Quick Start Guide - Time Tracker

## Installation (2 minutes)

```bash
cd /path/to/timetracker
python3 install.py
```

This installs everything and sets up the menu bar app to launch on login.

## First Time Setup

### 1. Create Your Projects

From the menu bar app:
1. Look for "⏱️ HH:MM:SS" in your macOS menu bar (top right)
2. Click it and select "New Project"
3. Enter your project name (e.g., "Website Redesign")
4. Add an optional summary (e.g., "Client project")
5. Repeat for each project you want to track

**Or use the CLI:**
```bash
python3 ~/.local/bin/timetracker.py project add "Website Redesign" --summary "Client project"
python3 ~/.local/bin/timetracker.py project add "API Development" --summary "Backend API"
```

### 2. Start Tracking

From the menu bar:
1. Click "⏱️ HH:MM:SS" in the menu bar
2. Select "Start Tracking"
3. Choose your project from the list
4. Watch the timer count up!

### 3. Stop & Switch

- Click the menu bar item again and select "⏹ Stop Tracking"
- To switch projects, just stop and start tracking a different one

## Daily Workflow

### Morning
1. Click menu bar → "Start Tracking" → Select your first project
2. Menu bar shows elapsed time in real-time

### Throughout the Day
- Click menu bar icon → "Start Tracking" to switch projects
- Time automatically logs to the previous project

### End of Day
- Click menu bar → "⏹ Stop Tracking"
- Check today's summary in Reports → "Today"

## View Your Time

### Quick Check
Click menu bar → Reports → Choose:
- **Today** - How much time on each project today?
- **This Week** - Weekly totals
- **All Time** - Project totals since you started

### Export for Reporting
Click menu bar → Reports → "Export to CSV"

Creates a file on your Desktop with all your project times.

## Common Tasks

### List All Projects
```bash
python3 ~/.local/bin/timetracker.py project list
```

### Get Today's Report
```bash
python3 ~/.local/bin/timetracker.py report today
```

### Get This Week's Report
```bash
python3 ~/.local/bin/timetracker.py report week
```

### Export Data
```bash
python3 ~/.local/bin/timetracker.py export -o my_report.csv
```

### Delete a Project
From menu bar: "Manage Projects" → Select project → Delete

## Tips for Success

1. **Always use the menu bar** - It's the fastest way to start/stop
2. **Review daily** - Check "Today" before closing your laptop
3. **Export weekly** - Keep CSV exports for records/invoicing
4. **Project naming** - Use clear names for easy identification
5. **Weekly check** - Sunday evening, review "This Week" totals

## Keyboard Shortcuts

Unfortunately, the current version doesn't have keyboard shortcuts, but you can:
- Click the menu bar item very quickly (gets faster with practice!)
- Bind the app in macOS System Preferences if needed

## Troubleshooting

### Menu bar app not showing
1. Check System Preferences → General → "Allow in the menu bar"
2. Restart the app: `launchctl unload ~/Library/LaunchAgents/com.timetracker.menu.plist && sleep 2 && launchctl load ~/Library/LaunchAgents/com.timetracker.menu.plist`

### Lost data?
Your data is in `~/.timetracker/projects.db`. It persists across restarts.

### Want to start fresh?
```bash
rm ~/.timetracker/projects.db
```
The database will recreate on next launch.

## Next Steps

1. ✅ Install the app
2. ✅ Create 3-5 projects
3. ✅ Track a few work sessions
4. ✅ Check your daily/weekly reports
5. ✅ Export to CSV to verify

You're ready to go! Start tracking your time 🕐

---

For detailed documentation, see [README.md](README.md)
