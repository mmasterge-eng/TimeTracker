#!/usr/bin/env python3
"""
Test script to verify time tracking functionality
"""

import sys
import time
import sqlite3
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from timetracker import TimeTracker

def test_time_tracking():
    """Test the complete time tracking workflow"""

    print("="*50)
    print("Testing Time Tracker")
    print("="*50)

    # Initialize tracker
    tracker = TimeTracker()

    # Test 1: Check status (should be idle)
    print("\n1. Initial status check...")
    status = tracker.get_status()
    print(f"   Status: {status['status']}")
    assert status['status'] == 'idle', "Should start idle"
    print("   ✓ Passed")

    # Test 2: Start tracking Website Redesign
    print("\n2. Starting to track 'Website Redesign'...")
    result = tracker.start_project("Website Redesign")
    print(f"   Project: {result['project_name']}")
    print(f"   Session ID: {result['session_id']}")
    status = tracker.get_status()
    assert status['status'] == 'tracking', "Should be tracking"
    assert status['active_project'] == "Website Redesign"
    print("   ✓ Passed")

    # Test 3: Simulate work (wait a few seconds)
    print("\n3. Simulating work... (3 seconds)")
    time.sleep(3)
    status = tracker.get_status()
    print(f"   Elapsed: {status['elapsed_formatted']} ({status['elapsed_seconds']} sec)")
    assert status['elapsed_seconds'] >= 3, "Should have elapsed time"
    print("   ✓ Passed")

    # Test 4: Stop tracking
    print("\n4. Stopping tracking...")
    result = tracker.stop_project()
    print(f"   Project: {result['project_name']}")
    print(f"   Total time: {result['elapsed_formatted']}")
    status = tracker.get_status()
    assert status['status'] == 'idle', "Should be idle after stopping"
    print("   ✓ Passed")

    # Test 5: Check project total
    print("\n5. Checking project totals...")
    project = tracker.project.get_by_name("Website Redesign")
    total = tracker.analytics.get_project_time_total(project['id'])
    print(f"   Website Redesign total: {tracker.analytics.format_seconds(total)}")
    assert total > 0, "Project should have tracked time"
    print("   ✓ Passed")

    # Test 6: Start and stop another project
    print("\n6. Tracking second project...")
    result = tracker.start_project("API Development")
    print(f"   Started: {result['project_name']}")
    time.sleep(2)
    result = tracker.stop_project()
    print(f"   Stopped: {result['project_name']} - {result['elapsed_formatted']}")
    print("   ✓ Passed")

    # Test 7: Daily breakdown
    print("\n7. Today's breakdown:")
    breakdown = tracker.analytics.get_daily_breakdown()
    for name, data in breakdown.items():
        print(f"   {name}: {data['formatted']}")
    assert len(breakdown) >= 2, "Should have multiple projects tracked"
    print("   ✓ Passed")

    # Test 8: All-time totals
    print("\n8. All-time totals:")
    breakdown = tracker.analytics.get_total_breakdown()
    for name, data in breakdown.items():
        print(f"   {name}: {data['formatted']}")
    print("   ✓ Passed")

    # Test 9: CSV export
    print("\n9. Testing CSV export...")
    export_path = Path("/sessions/eloquent-beautiful-hamilton/mnt/time tracker/test_export.csv")
    tracker.export_to_csv(export_path)
    assert export_path.exists(), "CSV file should be created"
    with open(export_path, 'r') as f:
        content = f.read()
        print(f"   Export file created:")
        for line in content.split('\n')[:5]:
            if line:
                print(f"   {line}")
    print("   ✓ Passed")

    # Cleanup
    tracker.close()

    print("\n" + "="*50)
    print("✓ All tests passed!")
    print("="*50)


if __name__ == '__main__':
    try:
        test_time_tracking()
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
