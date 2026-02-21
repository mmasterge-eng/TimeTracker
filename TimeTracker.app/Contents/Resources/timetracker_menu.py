#!/usr/bin/env python3
"""
Time Tracker Menu Bar - macOS menu bar utility for time tracking
Displays elapsed time and provides quick controls from the macOS menu bar
"""

import rumps
import threading
import time
from datetime import datetime
from pathlib import Path
import sys
import json

# Import the TimeTracker classes
from timetracker import TimeTracker, TimeTrackerDB, DB_PATH, CONFIG_PATH

# Global tracker instance
tracker = None
app = None


class TimeTrackerApp(rumps.App):
    """macOS menu bar application for time tracking"""

    def __init__(self):
        super(TimeTrackerApp, self).__init__(
            "Time Tracker",
            title="⏱️ 00:00:00",
            quit_button=None
        )

        self.tracker = TimeTracker()
        self.update_thread = None
        self.running = True
        self.last_status = None

        # Build initial menu
        self.update_menu()

        # Start update thread
        self.start_update_thread()

    def start_update_thread(self):
        """Start background thread to update timer"""
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

    def _update_loop(self):
        """Background loop that updates the timer"""
        while self.running:
            try:
                status = self.tracker.get_status()

                if status['status'] == 'tracking':
                    elapsed = status['elapsed_seconds']
                    hours = elapsed // 3600
                    minutes = (elapsed % 3600) // 60
                    seconds = elapsed % 60
                    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                    # Update menu bar title
                    self.title = f"⏱️ {time_str}"
                    self.last_status = status

                time.sleep(1)

            except Exception as e:
                print(f"Error in update loop: {e}")
                time.sleep(1)

    def update_menu(self):
        """Update the menu items"""
        self.menu.clear()

        status = self.tracker.get_status()

        # Current project info
        if status['status'] == 'tracking':
            project_item = rumps.MenuItem(
                f"Project: {status['active_project']}",
                callback=None
            )
            self.menu.add(project_item)
            self.menu.add(None)  # Separator

            # Start/Stop button
            stop_item = rumps.MenuItem("⏹ Stop Tracking", callback=self.stop_tracking)
            self.menu.add(stop_item)
        else:
            idle_item = rumps.MenuItem("Idle - No project tracking", callback=None)
            self.menu.add(idle_item)
            self.menu.add(None)  # Separator

            # Project selection menu
            projects = self.tracker.project.list_all()
            if projects:
                start_menu = rumps.MenuItem("Start Tracking")
                for item in self._build_project_menu(projects):
                    start_menu.add(item)
                self.menu.add(start_menu)
            else:
                no_projects = rumps.MenuItem("No projects yet", callback=None)
                self.menu.add(no_projects)

            self.menu.add(None)  # Separator

        # Reports submenu
        reports_menu = rumps.MenuItem("Reports")
        for item in self._build_reports_menu():
            if item is None:
                reports_menu.add(rumps.separator)
            else:
                reports_menu.add(item)
        self.menu.add(reports_menu)

        # Management
        self.menu.add(None)  # Separator
        self.menu.add(rumps.MenuItem("New Project", callback=self.new_project))
        self.menu.add(rumps.MenuItem("Manage Projects", callback=self.manage_projects))

        # Quit
        self.menu.add(None)  # Separator
        self.menu.add(rumps.MenuItem("Quit", callback=self.quit_app))

    def _build_project_menu(self, projects):
        """Build submenu for project selection"""
        menu_items = []
        for project in projects:
            total = self.tracker.analytics.get_project_time_total(project['id'])
            formatted = self.tracker.analytics.format_seconds(total)
            title = f"{project['name']} ({formatted})"
            item = rumps.MenuItem(title, callback=lambda sender, pid=project['id']: self.start_project(pid))
            menu_items.append(item)
        return menu_items

    def _build_reports_menu(self):
        """Build submenu for reports"""
        menu_items = [
            rumps.MenuItem("Today", callback=self.report_today),
            rumps.MenuItem("This Week", callback=self.report_week),
            rumps.MenuItem("All Time", callback=self.report_total),
            None,  # Separator
            rumps.MenuItem("Export to CSV", callback=self.export_csv),
        ]
        return menu_items

    def stop_tracking(self, sender):
        """Stop tracking current project"""
        result = self.tracker.stop_project()
        self.title = "⏱️ 00:00:00"
        self.update_menu()

        rumps.notification(
            "Time Tracking Stopped",
            f"{result['project_name']} - {result['elapsed_formatted']}",
            ""
        )

    def start_project(self, project_id):
        """Start tracking a project"""
        project = self.tracker.project.get_by_id(project_id)
        try:
            result = self.tracker.start_project(project['name'])
            self.update_menu()
            rumps.notification(
                "Started Tracking",
                f"{project['name']}",
                ""
            )
        except Exception as e:
            rumps.alert(title="Error", message=f"Could not start tracking: {str(e)}")

    def new_project(self, sender):
        """Create new project dialog"""
        response = rumps.Window(
            message="Project name:",
            title="New Project",
            default_text="",
            ok="Create",
            cancel="Cancel"
        ).run()

        if response.clicked:
            name = response.text
            if name:
                # Get summary
                summary_response = rumps.Window(
                    message="Project summary (optional):",
                    title="New Project",
                    default_text="",
                    ok="Create",
                    cancel="Skip"
                ).run()

                summary = summary_response.text if summary_response.clicked else ""

                try:
                    project_id = self.tracker.project.create(name, summary)
                    self.update_menu()
                    rumps.notification(
                        "Project Created",
                        f"'{name}' created successfully",
                        ""
                    )
                except ValueError as e:
                    rumps.alert(title="Error", message=str(e))
                except Exception as e:
                    rumps.alert(title="Error", message=f"Could not create project: {str(e)}")

    def manage_projects(self, sender):
        """Open project management"""
        projects = self.tracker.project.list_all()

        if not projects:
            rumps.alert(title="Projects", message="No projects yet. Create one in the menu.")
            return

        project_names = [p['name'] for p in projects]
        response = rumps.Window(
            message="Select a project to delete:",
            title="Manage Projects",
            default_text=project_names[0],
            ok="Delete",
            cancel="Cancel"
        ).run()

        if response.clicked and response.text:
            project = self.tracker.project.get_by_name(response.text)
            if project:
                # Confirm deletion
                confirm = rumps.alert(
                    title="Confirm Delete",
                    message=f"Delete '{response.text}'?",
                    ok="Delete",
                    cancel="Cancel"
                )
                if confirm == 0:  # Clicked Delete
                    self.tracker.project.delete(project['id'])
                    self.update_menu()
                    rumps.notification(
                        "Project Deleted",
                        f"'{response.text}' has been deleted",
                        ""
                    )

    def report_today(self, sender):
        """Show today's time breakdown"""
        breakdown = self.tracker.analytics.get_daily_breakdown()

        if not breakdown:
            message = "No time tracked today"
        else:
            lines = []
            total = 0
            for name, data in breakdown.items():
                lines.append(f"{name}: {data['formatted']}")
                total += data['seconds']

            message = "\n".join(lines)
            message += f"\n\nTotal: {self.tracker.analytics.format_seconds(total)}"

        rumps.alert(title="Today's Time", message=message)

    def report_week(self, sender):
        """Show this week's time breakdown"""
        breakdown = self.tracker.analytics.get_weekly_breakdown()

        if not breakdown:
            message = "No time tracked this week"
        else:
            lines = []
            total = 0
            for name, data in breakdown.items():
                lines.append(f"{name}: {data['formatted']}")
                total += data['seconds']

            message = "\n".join(lines)
            message += f"\n\nTotal: {self.tracker.analytics.format_seconds(total)}"

        rumps.alert(title="This Week's Time", message=message)

    def report_total(self, sender):
        """Show all-time time breakdown"""
        breakdown = self.tracker.analytics.get_total_breakdown()

        if not breakdown:
            message = "No time tracked yet"
        else:
            lines = []
            total = 0
            for name, data in breakdown.items():
                lines.append(f"{name}: {data['formatted']}")
                total += data['seconds']

            message = "\n".join(lines)
            message += f"\n\nTotal: {self.tracker.analytics.format_seconds(total)}"

        rumps.alert(title="All-Time Totals", message=message)

    def export_csv(self, sender):
        """Export data to CSV"""
        try:
            export_path = Path.home() / "Desktop" / f"timetracker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.tracker.export_to_csv(export_path)
            rumps.notification(
                "Export Complete",
                f"Data exported to:\n{export_path.name}",
                ""
            )
        except Exception as e:
            rumps.alert(title="Export Error", message=f"Could not export: {str(e)}")

    def quit_app(self, sender):
        """Quit application"""
        self.running = False
        if self.tracker:
            self.tracker.close()
        rumps.quit_application()


def main():
    """Main entry point"""
    global app

    try:
        app = TimeTrackerApp()
        app.run()
    except Exception as e:
        print(f"Error starting Time Tracker: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
