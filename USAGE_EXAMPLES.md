# Time Tracker - Usage Examples

Complete examples of how to use the Time Tracker application.

## Menu Bar Interface

### Menu Bar Appearance
```
macOS Menu Bar:
┌──────────────────────────────────────────────────┐
│ ... WiFi 📶 ... Volume 🔊 | ⏱️ 02:34:17 ... │
└──────────────────────────────────────────────────┘
                              ↑
                         Click here!
```

## Scenario 1: Daily Workflow

### Morning (Start of Day)

1. **Application Auto-Starts** (from LaunchAgent)
   - Menu bar shows `⏱️ 00:00:00`
   - No projects tracking yet

2. **Start First Project**
   - Click `⏱️ 00:00:00` in menu bar
   - Menu appears:
     ```
     ⏱️ Menu
     ├── Idle - No project tracking
     │
     ├── Start Tracking >
     │   ├── Website Redesign (02:15:43)
     │   ├── API Development (01:30:22)
     │   └── Documentation (00:45:10)
     │
     ├── Reports >
     ├── New Project
     ├── Manage Projects
     └── Quit
     ```
   - Click "Website Redesign"
   - Menu bar updates to show `⏱️ 00:00:00` (starting timer)

### Mid-Morning (30 minutes in)

```
Menu bar shows: ⏱️ 00:30:15

Click menu bar:
┌─────────────────────────────┐
│ ⏱️ Menu                      │
├─────────────────────────────┤
│ Project: Website Redesign   │
│                             │
│ ⏹ Stop Tracking            │
│                             │
│ Reports >                   │
│ New Project                 │
│ Manage Projects             │
│ Quit                        │
└─────────────────────────────┘
```

### Context Switch (Move to Different Project)

1. **Stop Current Project**
   - Click `⏱️ 00:30:15`
   - Click `⏹ Stop Tracking`
   - Get notification: "Time Tracking Stopped - Website Redesign - 00:30:15"
   - Menu bar resets to `⏱️ 00:00:00`

2. **Start New Project**
   - Click `⏱️ 00:00:00`
   - Click "Start Tracking"
   - Select "API Development"
   - Timer starts over from 00:00:00

### End of Day (Check Daily Totals)

1. **Stop Current Tracking**
   - Click menu bar → `⏹ Stop Tracking`

2. **View Today's Breakdown**
   - Click menu bar → "Reports" → "Today"
   - See popup:
     ```
     Today's Time

     Website Redesign: 02:45:30
     API Development: 01:15:20
     Documentation: 00:30:45

     Total: 04:31:35
     ```

## Scenario 2: Creating New Projects

### Using Menu Bar

1. Click `⏱️` in menu bar
2. Click "New Project"
3. Dialog appears:
   ```
   New Project

   Project name: [_________________]
                                 [Create] [Cancel]
   ```
4. Type: "Mobile App Design"
5. Click "Create"
6. Next dialog:
   ```
   New Project

   Project summary (optional): [_________________]
                                                [Create] [Skip]
   ```
7. Type: "iOS and Android UI/UX"
8. Click "Create"
9. Notification: "Project Created - 'Mobile App Design' created successfully"

### Using Command Line

```bash
$ python3 ~/.local/bin/timetracker.py project add "Mobile App Design" --summary "iOS and Android UI/UX"
✓ Project 'Mobile App Design' created (ID: 4)
```

## Scenario 3: Weekly Reporting

### Sunday Evening - Review the Week

1. **Click menu bar**
2. **Select "Reports" → "This Week"**
   ```
   This Week's Time

   Website Redesign: 12:30:45
   API Development: 10:15:20
   Documentation: 05:45:10

   Total: 28:31:15
   ```

3. **Calculate Billable Hours**
   - Total this week: 28.5 hours
   - If billing at $150/hour: $4,275

### Monthly Export for Invoicing

1. **Click menu bar** → "Reports" → "Export to CSV"
2. CSV file created on Desktop: `timetracker_20240221_143022.csv`
3. Open in Excel:
   ```
   Project              | Total Time (HH:MM:SS) | Total Seconds
   ─────────────────────┼──────────────────────┼─────────────
   Website Redesign     | 50:45:30              | 182730
   API Development      | 42:20:15              | 152415
   Documentation        | 18:30:45              | 66645
   Mobile App Design    | 35:15:20              | 126920
   ─────────────────────┴──────────────────────┴─────────────
   TOTAL                | 147:12:10             | 529810
   ```

4. Use for invoicing, time analysis, or project planning

## Scenario 4: Managing Projects

### View All Projects

Menu bar → "Manage Projects"

Dialog shows:
```
Manage Projects

Select a project to delete:

[Website Redesign        ▼]
                                [Delete] [Cancel]
```

Or from CLI:
```bash
$ python3 ~/.local/bin/timetracker.py project list

Projects:
  [1] Website Redesign - Client project - modernize UI
       Total: 50:45:30
  [2] API Development - Backend API for mobile app
       Total: 42:20:15
  [3] Documentation - Writing guides and specs
       Total: 18:30:45
```

### Delete a Project

Menu bar → "Manage Projects" → Select → "Delete" → Confirm

Or from CLI:
```bash
$ python3 ~/.local/bin/timetracker.py project delete "Old Project"
✓ Project 'Old Project' deleted
```

## Scenario 5: Quick Status Check

### From Menu Bar (Fastest)
```
Just click the menu bar and see:
⏱️ 00:15:23  (if currently tracking)
or
⏱️ 00:00:00  (if idle)
```

### From CLI

**Check Current Status:**
```bash
$ python3 ~/.local/bin/timetracker.py status
Tracking: Website Redesign
Elapsed: 00:15:23
```

**Get Today's Breakdown:**
```bash
$ python3 ~/.local/bin/timetracker.py report today

Today's Time:
  Website Redesign: 02:45:30
  API Development: 01:15:20
  Documentation: 00:30:45
```

**Get Weekly Report:**
```bash
$ python3 ~/.local/bin/timetracker.py report week

This Week's Time:
  Website Redesign: 12:30:45
  API Development: 10:15:20
  Documentation: 05:45:10
```

## Scenario 6: Troubleshooting

### App Stopped Tracking

1. Check menu bar - does `⏱️` appear?
   - If yes: Click it, check if in "Tracking" or "Idle" state
   - If no: App may have crashed

2. Restart the app:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.timetracker.menu.plist
   sleep 2
   launchctl load ~/Library/LaunchAgents/com.timetracker.menu.plist
   ```

3. Check logs:
   ```bash
   cat ~/.timetracker/menu_error.log
   ```

### Can't Find a Project

```bash
# List all projects
python3 ~/.local/bin/timetracker.py project list

# If project is missing, recreate it
python3 ~/.local/bin/timetracker.py project add "ProjectName" --summary "Description"
```

### Data Recovery

Your data is in `~/.timetracker/projects.db`. To backup:
```bash
cp ~/.timetracker/projects.db ~/Desktop/backup_timetracker.db
```

## Scenario 7: Multiple Active Projects

### Example Day with 5 Projects

**8:00 AM** - Start "Website Redesign"
```
Menu: ⏱️ 00:00:00 (starts counting)
```

**9:15 AM** - Switch to "API Development"
```
Menu: Stop → Notification shows "Website Redesign - 01:15:30"
⏱️ 00:00:00 (new timer starts)
```

**11:30 AM** - Switch to "Documentation"
```
Menu: Stop → Notification shows "API Development - 02:15:15"
⏱️ 00:00:00 (new timer starts)
```

**1:00 PM** - Lunch break (stop tracking)
```
Menu: Stop → Notification shows "Documentation - 01:30:00"
⏱️ 00:00:00 (idle)
```

**2:00 PM** - Resume "Website Redesign"
```
Menu: Start → Select "Website Redesign"
⏱️ 00:00:00 (new session starts)
```

**End of Day** - View report:
```
Report Today:
  Website Redesign: 03:30:45 (morning + afternoon)
  API Development: 02:15:15
  Documentation: 01:30:00
  Total: 07:15:60
```

## Keyboard Shortcuts

Currently, the menu bar app requires clicking. But you can:

1. **Click menu bar item** - Practice makes this fast!
2. **Set custom macOS shortcuts** (advanced):
   ```
   System Preferences → Keyboard → Shortcuts → Services
   Add custom shortcuts for app launch
   ```

## Performance Notes

- Menu bar timer updates: **Every 1 second**
- Database queries: **< 10ms typically**
- Memory usage: **~50-80 MB**
- CPU: **< 1% when idle, < 5% when tracking**
- Disk I/O: **Only on session start/stop**

## Tips & Tricks

### Speed Up Tracking
- Create projects upfront
- Use short memorable project names
- Keep active projects in your top 3-5

### Maximize Insights
- Review daily at end of day
- Check weekly every Sunday
- Compare weeks to identify patterns

### Professional Use
- Export monthly for invoicing
- Use CSV in Excel for further analysis
- Share reports with team leads

---

**Master the menu bar approach and you'll be tracking time in seconds! 🕐**
