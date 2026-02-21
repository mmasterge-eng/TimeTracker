#!/usr/bin/env python3
"""
Time Tracker - Core backend for project time tracking
Manages projects, time sessions, and analytics with local SQLite storage
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys
import argparse
import csv
from typing import Optional, List, Dict, Tuple

# Configuration
DB_DIR = Path.home() / ".timetracker"
DB_PATH = DB_DIR / "projects.db"
CONFIG_PATH = DB_DIR / "config.json"


class TimeTrackerDB:
    """Manages database connection and schema"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.init_db()

    def init_db(self):
        """Initialize database connection and create tables if needed"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Create tables
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_cursor(self):
        """Get database cursor"""
        return self.conn.cursor()


class Project:
    """Project model and operations"""

    def __init__(self, db: TimeTrackerDB):
        self.db = db

    def create(self, name: str, summary: str = "") -> int:
        """Create a new project"""
        cursor = self.db.get_cursor()
        try:
            cursor.execute(
                "INSERT INTO projects (name, summary) VALUES (?, ?)",
                (name, summary)
            )
            self.db.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Project '{name}' already exists")

    def list_all(self) -> List[Dict]:
        """Get all projects"""
        cursor = self.db.get_cursor()
        cursor.execute("SELECT id, name, summary, created_at FROM projects ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, project_id: int) -> Optional[Dict]:
        """Get project by ID"""
        cursor = self.db.get_cursor()
        cursor.execute("SELECT id, name, summary, created_at FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_name(self, name: str) -> Optional[Dict]:
        """Get project by name"""
        cursor = self.db.get_cursor()
        cursor.execute("SELECT id, name, summary, created_at FROM projects WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete(self, project_id: int) -> bool:
        """Delete a project and its sessions"""
        cursor = self.db.get_cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self.db.conn.commit()
        return cursor.rowcount > 0

    def update(self, project_id: int, name: str = None, summary: str = None) -> bool:
        """Update project details"""
        cursor = self.db.get_cursor()
        updates = []
        values = []

        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if summary is not None:
            updates.append("summary = ?")
            values.append(summary)

        if not updates:
            return False

        values.append(project_id)
        query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        self.db.conn.commit()
        return cursor.rowcount > 0


class Session:
    """Time session model and operations"""

    def __init__(self, db: TimeTrackerDB):
        self.db = db
        self.project = Project(db)

    def start(self, project_id: int) -> int:
        """Start a new session"""
        # Verify project exists
        if not self.project.get_by_id(project_id):
            raise ValueError(f"Project {project_id} not found")

        cursor = self.db.get_cursor()
        cursor.execute(
            "INSERT INTO sessions (project_id, start_time) VALUES (?, ?)",
            (project_id, datetime.now())
        )
        self.db.conn.commit()

        # Save current project to config
        Config.set(self.db, "current_project_id", str(project_id))

        return cursor.lastrowid

    def stop(self, session_id: int = None) -> bool:
        """Stop the current or specified session"""
        cursor = self.db.get_cursor()

        if session_id is None:
            # Stop the most recent active session
            cursor.execute(
                "SELECT id FROM sessions WHERE end_time IS NULL ORDER BY start_time DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if not row:
                return False
            session_id = row[0]

        cursor.execute(
            "UPDATE sessions SET end_time = ? WHERE id = ?",
            (datetime.now(), session_id)
        )
        self.db.conn.commit()
        return cursor.rowcount > 0

    def get_active(self) -> Optional[Dict]:
        """Get the current active session"""
        cursor = self.db.get_cursor()
        cursor.execute(
            "SELECT id, project_id, start_time, end_time FROM sessions WHERE end_time IS NULL ORDER BY start_time DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_elapsed_seconds(self, session_id: int = None) -> int:
        """Get elapsed seconds for a session"""
        if session_id is None:
            active = self.get_active()
            if not active:
                return 0
            session_id = active['id']

        cursor = self.db.get_cursor()
        cursor.execute(
            "SELECT start_time, end_time FROM sessions WHERE id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        if not row:
            return 0

        start = datetime.fromisoformat(row[0])
        end = datetime.fromisoformat(row[1]) if row[1] else datetime.now()
        return int((end - start).total_seconds())

    def get_sessions_for_project(self, project_id: int, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Get sessions for a project within date range"""
        cursor = self.db.get_cursor()

        query = "SELECT id, project_id, start_time, end_time FROM sessions WHERE project_id = ?"
        params = [project_id]

        if start_date:
            query += " AND start_time >= ?"
            params.append(start_date)

        if end_date:
            query += " AND start_time < ?"
            params.append(end_date)

        query += " ORDER BY start_time DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


class TimeAnalytics:
    """Analytics and reporting"""

    def __init__(self, db: TimeTrackerDB):
        self.db = db
        self.session = Session(db)
        self.project = Project(db)

    def get_project_time_today(self, project_id: int) -> int:
        """Get total seconds spent on project today"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        sessions = self.session.get_sessions_for_project(project_id, today, tomorrow)
        total_seconds = 0

        for sess in sessions:
            start = datetime.fromisoformat(sess['start_time'])
            end = datetime.fromisoformat(sess['end_time']) if sess['end_time'] else datetime.now()
            total_seconds += int((end - start).total_seconds())

        return total_seconds

    def get_project_time_week(self, project_id: int) -> int:
        """Get total seconds spent on project this week (Mon-Sun)"""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        sessions = self.session.get_sessions_for_project(project_id, start_of_week)
        total_seconds = 0

        for sess in sessions:
            start = datetime.fromisoformat(sess['start_time'])
            end = datetime.fromisoformat(sess['end_time']) if sess['end_time'] else datetime.now()
            total_seconds += int((end - start).total_seconds())

        return total_seconds

    def get_project_time_total(self, project_id: int) -> int:
        """Get total seconds spent on project (all time)"""
        sessions = self.session.get_sessions_for_project(project_id)
        total_seconds = 0

        for sess in sessions:
            start = datetime.fromisoformat(sess['start_time'])
            end = datetime.fromisoformat(sess['end_time']) if sess['end_time'] else datetime.now()
            total_seconds += int((end - start).total_seconds())

        return total_seconds

    def format_seconds(self, seconds: int) -> str:
        """Format seconds as HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def get_daily_breakdown(self, date: datetime = None) -> Dict:
        """Get time breakdown by project for a specific day"""
        if date is None:
            date = datetime.now()

        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        cursor = self.db.get_cursor()
        cursor.execute("""
            SELECT p.id, p.name, SUM(
                CAST((JULIANDAY(COALESCE(s.end_time, ?)) -
                      JULIANDAY(s.start_time)) * 86400 AS INTEGER)
            ) as total_seconds
            FROM sessions s
            JOIN projects p ON s.project_id = p.id
            WHERE s.start_time >= ? AND s.start_time < ?
            GROUP BY p.id, p.name
            ORDER BY total_seconds DESC
        """, (datetime.now(), day_start, day_end))

        result = {}
        for row in cursor.fetchall():
            result[row[1]] = {
                'project_id': row[0],
                'seconds': row[2] or 0,
                'formatted': self.format_seconds(row[2] or 0)
            }

        return result

    def get_weekly_breakdown(self) -> Dict:
        """Get time breakdown by project for current week"""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        cursor = self.db.get_cursor()
        cursor.execute("""
            SELECT p.id, p.name, SUM(
                CAST((JULIANDAY(COALESCE(s.end_time, ?)) -
                      JULIANDAY(s.start_time)) * 86400 AS INTEGER)
            ) as total_seconds
            FROM sessions s
            JOIN projects p ON s.project_id = p.id
            WHERE s.start_time >= ?
            GROUP BY p.id, p.name
            ORDER BY total_seconds DESC
        """, (datetime.now(), start_of_week))

        result = {}
        for row in cursor.fetchall():
            result[row[1]] = {
                'project_id': row[0],
                'seconds': row[2] or 0,
                'formatted': self.format_seconds(row[2] or 0)
            }

        return result

    def get_total_breakdown(self) -> Dict:
        """Get all-time time breakdown by project"""
        cursor = self.db.get_cursor()
        cursor.execute("""
            SELECT p.id, p.name, SUM(
                CAST((JULIANDAY(COALESCE(s.end_time, ?)) -
                      JULIANDAY(s.start_time)) * 86400 AS INTEGER)
            ) as total_seconds
            FROM sessions s
            JOIN projects p ON s.project_id = p.id
            GROUP BY p.id, p.name
            ORDER BY total_seconds DESC
        """, (datetime.now(),))

        result = {}
        for row in cursor.fetchall():
            result[row[1]] = {
                'project_id': row[0],
                'seconds': row[2] or 0,
                'formatted': self.format_seconds(row[2] or 0)
            }

        return result


class Config:
    """Configuration management"""

    @staticmethod
    def get(db: TimeTrackerDB, key: str, default: str = None) -> Optional[str]:
        """Get config value"""
        cursor = db.get_cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    @staticmethod
    def set(db: TimeTrackerDB, key: str, value: str) -> None:
        """Set config value"""
        cursor = db.get_cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value)
        )
        db.conn.commit()


class TimeTracker:
    """Main controller"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db = TimeTrackerDB(db_path)
        self.project = Project(self.db)
        self.session = Session(self.db)
        self.analytics = TimeAnalytics(self.db)

    def close(self):
        """Close tracker"""
        self.db.close()

    def start_project(self, project_name: str) -> Dict:
        """Start tracking a project"""
        project = self.project.get_by_name(project_name)
        if not project:
            raise ValueError(f"Project '{project_name}' not found")

        # Stop any active session
        self.session.stop()

        # Start new session
        session_id = self.session.start(project['id'])
        return {
            'session_id': session_id,
            'project_id': project['id'],
            'project_name': project['name'],
            'start_time': datetime.now().isoformat()
        }

    def stop_project(self) -> Dict:
        """Stop tracking current project"""
        active = self.session.get_active()
        if not active:
            return {'status': 'no_active_session'}

        project = self.project.get_by_id(active['project_id'])
        self.session.stop(active['id'])

        elapsed = self.session.get_elapsed_seconds(active['id'])
        return {
            'session_id': active['id'],
            'project_name': project['name'],
            'elapsed_seconds': elapsed,
            'elapsed_formatted': self.analytics.format_seconds(elapsed),
            'end_time': datetime.now().isoformat()
        }

    def get_status(self) -> Dict:
        """Get current tracking status"""
        active = self.session.get_active()

        if not active:
            return {
                'status': 'idle',
                'active_project': None,
                'elapsed_seconds': 0
            }

        project = self.project.get_by_id(active['project_id'])
        elapsed = self.session.get_elapsed_seconds(active['id'])

        return {
            'status': 'tracking',
            'active_project': project['name'],
            'active_project_id': project['id'],
            'elapsed_seconds': elapsed,
            'elapsed_formatted': self.analytics.format_seconds(elapsed),
            'session_id': active['id']
        }

    def export_to_csv(self, filepath: Path) -> None:
        """Export all time data to CSV"""
        projects = self.project.list_all()

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Project', 'Total Time (HH:MM:SS)', 'Total Seconds'])

            for proj in projects:
                total_seconds = self.analytics.get_project_time_total(proj['id'])
                formatted = self.analytics.format_seconds(total_seconds)
                writer.writerow([proj['name'], formatted, total_seconds])


# CLI Interface
def main():
    parser = argparse.ArgumentParser(description='Time Tracker - Project time tracking utility')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Project commands
    project_parser = subparsers.add_parser('project', help='Project management')
    project_subparsers = project_parser.add_subparsers(dest='project_cmd')

    add_parser = project_subparsers.add_parser('add', help='Add a new project')
    add_parser.add_argument('name', help='Project name')
    add_parser.add_argument('--summary', default='', help='Project summary')

    list_parser = project_subparsers.add_parser('list', help='List all projects')

    delete_parser = project_subparsers.add_parser('delete', help='Delete a project')
    delete_parser.add_argument('name', help='Project name')

    # Session commands
    subparsers.add_parser('start', help='Start tracking (requires project ID)')
    subparsers.add_parser('stop', help='Stop tracking current project')
    subparsers.add_parser('status', help='Show current tracking status')

    # Report commands
    report_parser = subparsers.add_parser('report', help='View time reports')
    report_subparsers = report_parser.add_subparsers(dest='report_cmd')

    report_subparsers.add_parser('today', help='Daily breakdown')
    report_subparsers.add_parser('week', help='Weekly breakdown')
    report_subparsers.add_parser('total', help='All-time breakdown')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export data to CSV')
    export_parser.add_argument('--output', '-o', default='timetracker_export.csv', help='Output file path')

    args = parser.parse_args()

    tracker = TimeTracker()

    try:
        if args.command == 'project':
            if args.project_cmd == 'add':
                project_id = tracker.project.create(args.name, args.summary)
                print(f"✓ Project '{args.name}' created (ID: {project_id})")
            elif args.project_cmd == 'list':
                projects = tracker.project.list_all()
                if not projects:
                    print("No projects yet.")
                else:
                    print("\nProjects:")
                    for p in projects:
                        total = tracker.analytics.get_project_time_total(p['id'])
                        formatted = tracker.analytics.format_seconds(total)
                        print(f"  [{p['id']}] {p['name']} - {p['summary']}")
                        print(f"       Total: {formatted}")
            elif args.project_cmd == 'delete':
                project = tracker.project.get_by_name(args.name)
                if project:
                    tracker.project.delete(project['id'])
                    print(f"✓ Project '{args.name}' deleted")
                else:
                    print(f"✗ Project '{args.name}' not found")

        elif args.command == 'start':
            status = tracker.get_status()
            if status['status'] == 'tracking':
                print(f"Already tracking {status['active_project']}. Stop first.")
            else:
                projects = tracker.project.list_all()
                if not projects:
                    print("No projects. Create one first.")
                else:
                    print("Select a project:")
                    for p in projects:
                        print(f"  {p['id']}: {p['name']}")

        elif args.command == 'stop':
            result = tracker.stop_project()
            if result['status'] == 'no_active_session':
                print("No active session to stop.")
            else:
                print(f"✓ Stopped {result['project_name']}")
                print(f"  Time: {result['elapsed_formatted']}")

        elif args.command == 'status':
            status = tracker.get_status()
            if status['status'] == 'tracking':
                print(f"Tracking: {status['active_project']}")
                print(f"Elapsed: {status['elapsed_formatted']}")
            else:
                print("Not tracking anything")

        elif args.command == 'report':
            if args.report_cmd == 'today':
                breakdown = tracker.analytics.get_daily_breakdown()
                print("\nToday's Time:")
                if breakdown:
                    for name, data in breakdown.items():
                        print(f"  {name}: {data['formatted']}")
                else:
                    print("  No time tracked today")
            elif args.report_cmd == 'week':
                breakdown = tracker.analytics.get_weekly_breakdown()
                print("\nThis Week's Time:")
                if breakdown:
                    for name, data in breakdown.items():
                        print(f"  {name}: {data['formatted']}")
                else:
                    print("  No time tracked this week")
            elif args.report_cmd == 'total':
                breakdown = tracker.analytics.get_total_breakdown()
                print("\nAll-Time Totals:")
                if breakdown:
                    for name, data in breakdown.items():
                        print(f"  {name}: {data['formatted']}")
                else:
                    print("  No time tracked")

        elif args.command == 'export':
            tracker.export_to_csv(Path(args.output))
            print(f"✓ Exported to {args.output}")

        else:
            parser.print_help()

    finally:
        tracker.close()


if __name__ == '__main__':
    main()
