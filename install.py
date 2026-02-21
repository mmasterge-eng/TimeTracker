#!/usr/bin/env python3
"""
Time Tracker Installation Script
Sets up the application, dependencies, and LaunchAgent for menu bar integration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, description=""):
    """Run a shell command"""
    if description:
        print(f"  {description}...", end=" ", flush=True)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if description:
            print("✓")
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        if description:
            print("✗")
        return False, "", str(e)


def main():
    print("🕐 Time Tracker Installation\n")

    # Get paths
    script_dir = Path(__file__).parent.resolve()
    home = Path.home()
    tracker_dir = home / ".timetracker"
    bin_dir = home / ".local" / "bin"

    # Create directories
    print("Setting up directories...")
    tracker_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    print("  ✓ Created ~/.timetracker/")
    print("  ✓ Created ~/.local/bin/")

    # Install Python dependencies
    print("\nInstalling Python dependencies...")
    success, _, _ = run_command(
        f"{sys.executable} -m pip install -r '{script_dir}/requirements.txt' --break-system-packages",
        "Installing rumps"
    )
    if not success:
        print("  ⚠ Could not install dependencies (continuing anyway)")

    # Copy scripts to bin directory
    print("\nInstalling scripts...")
    for script in ['timetracker.py', 'timetracker_menu.py']:
        src = script_dir / script
        dst = bin_dir / script
        if src.exists():
            shutil.copy2(src, dst)
            os.chmod(dst, 0o755)
            print(f"  ✓ Installed {script}")

    # Create LaunchAgent for menu bar app
    print("\nSetting up menu bar app...")

    launchagents_dir = home / "Library" / "LaunchAgents"
    launchagents_dir.mkdir(parents=True, exist_ok=True)

    plist_path = launchagents_dir / "com.timetracker.menu.plist"
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.timetracker.menu</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{bin_dir / 'timetracker_menu.py'}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>{tracker_dir / 'menu.log'}</string>
    <key>StandardErrorPath</key>
    <string>{tracker_dir / 'menu_error.log'}</string>
</dict>
</plist>
"""

    with open(plist_path, 'w') as f:
        f.write(plist_content)

    print(f"  ✓ Created LaunchAgent at ~/Library/LaunchAgents/com.timetracker.menu.plist")

    # Load LaunchAgent
    success, _, _ = run_command(
        f"launchctl load '{plist_path}'",
        "Loading LaunchAgent"
    )
    if success:
        print("  ✓ LaunchAgent loaded (will start on login)")
    else:
        print("  ⚠ Could not load LaunchAgent (you can load it manually)")

    # Initialization message
    print("\n" + "="*50)
    print("✓ Installation complete!")
    print("="*50)

    print("\nQuick Start:")
    print(f"  1. Add a project:")
    print(f"     python3 '{bin_dir / 'timetracker.py'}' project add 'MyProject' --summary 'Description'")
    print(f"\n  2. Start menu bar app:")
    print(f"     python3 '{bin_dir / 'timetracker_menu.py'}'")
    print(f"\n  3. Or use the LaunchAgent (starts on login):")
    print(f"     launchctl load ~/Library/LaunchAgents/com.timetracker.menu.plist")

    print("\nCLI Commands:")
    print(f"  Project Management:")
    print(f"    - project add <name> --summary <text>  - Create project")
    print(f"    - project list                          - List all projects")
    print(f"    - project delete <name>                 - Delete project")
    print(f"\n  Tracking:")
    print(f"    - status                                - Show current status")
    print(f"    - stop                                  - Stop tracking")
    print(f"\n  Reports:")
    print(f"    - report today                          - Today's breakdown")
    print(f"    - report week                           - This week's breakdown")
    print(f"    - report total                          - All-time totals")
    print(f"    - export -o <file.csv>                  - Export to CSV")

    print(f"\nData Location: {tracker_dir}")
    print(f"Database: {tracker_dir / 'projects.db'}")


if __name__ == '__main__':
    main()
