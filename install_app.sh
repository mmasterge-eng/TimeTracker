#!/bin/bash
# Time Tracker - macOS App Installer
# Handles Python version detection, Homebrew install, and rumps setup

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_SRC="$SCRIPT_DIR/TimeTracker.app"
APP_DEST="/Applications/Time Tracker.app"

echo "🕐 Time Tracker App Installer"
echo "────────────────────────────"
echo

# ──────────────────────────────────────────────
# Step 1: Find a working Python 3.10+
# ──────────────────────────────────────────────
echo "1. Finding Python 3.10+..."

find_good_python() {
    for py in \
        /opt/homebrew/bin/python3 \
        /usr/local/bin/python3 \
        /opt/homebrew/bin/python3.13 \
        /opt/homebrew/bin/python3.12 \
        /opt/homebrew/bin/python3.11 \
        /opt/homebrew/bin/python3.10 \
        /usr/local/bin/python3.13 \
        /usr/local/bin/python3.12 \
        /usr/local/bin/python3.11 \
        /usr/local/bin/python3.10; do
        if [ -x "$py" ]; then
            version=$("$py" -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
            major=$("$py" -c "import sys; print(sys.version_info.major)" 2>/dev/null)
            if [ "$major" -eq 3 ] && [ "$version" -ge 10 ] 2>/dev/null; then
                echo "$py"
                return 0
            fi
        fi
    done
    return 1
}

PYTHON=$(find_good_python)

if [ -z "$PYTHON" ]; then
    echo "   ⚠ Python 3.10+ not found. The Xcode Python (3.9) is too old for rumps."
    echo

    # Check if Homebrew is installed
    if command -v brew &>/dev/null; then
        echo "   Homebrew found! Installing Python 3.13..."
        brew install python3
        PYTHON=$(find_good_python)
    else
        echo "   Homebrew not found. Installing Homebrew first..."
        echo "   (This may take a few minutes...)"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add brew to path for Apple Silicon
        if [ -f /opt/homebrew/bin/brew ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi

        echo "   Installing Python 3.13..."
        brew install python3
        PYTHON=$(find_good_python)
    fi
fi

if [ -z "$PYTHON" ]; then
    echo
    echo "❌ Could not find or install Python 3.10+."
    echo "   Please install Python from https://www.python.org/downloads/"
    echo "   Then re-run this installer."
    exit 1
fi

PYVER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "   ✓ Using Python $PYVER at $PYTHON"

# ──────────────────────────────────────────────
# Step 2: Install rumps
# ──────────────────────────────────────────────
echo
echo "2. Installing rumps (menu bar library)..."

if "$PYTHON" -c "import rumps" 2>/dev/null; then
    echo "   ✓ rumps already installed"
else
    # Try pip install with various flags depending on Python version
    if "$PYTHON" -m pip install rumps --quiet 2>/dev/null; then
        echo "   ✓ rumps installed"
    elif "$PYTHON" -m pip install rumps --user --quiet 2>/dev/null; then
        echo "   ✓ rumps installed (user)"
    else
        echo "   ❌ Could not install rumps."
        echo "   Try manually: $PYTHON -m pip install rumps"
        exit 1
    fi
fi

# Verify it actually works
if ! "$PYTHON" -c "import rumps" 2>/dev/null; then
    echo "   ❌ rumps installed but cannot be imported. Something went wrong."
    exit 1
fi
echo "   ✓ rumps verified"

# ──────────────────────────────────────────────
# Step 3: Build .icns icon
# ──────────────────────────────────────────────
echo
echo "3. Building app icon..."
ICONSET="$SCRIPT_DIR/TimeTracker.iconset"
RESOURCES="$APP_SRC/Contents/Resources"

if [ -d "$ICONSET" ]; then
    iconutil -c icns "$ICONSET" -o "$RESOURCES/AppIcon.icns" 2>/dev/null && \
        rm -f "$RESOURCES/AppIcon.png" && \
        echo "   ✓ AppIcon.icns created" || \
        echo "   ⚠ Using PNG fallback icon (app will still work)"
else
    echo "   ⚠ Iconset not found, using fallback"
fi

# ──────────────────────────────────────────────
# Step 4: Patch the launcher to use the right Python
# ──────────────────────────────────────────────
echo
echo "4. Configuring app to use Python at $PYTHON..."

LAUNCHER="$APP_SRC/Contents/MacOS/TimeTracker"
cat > "$LAUNCHER" << LAUNCHER_EOF
#!/bin/bash
# Time Tracker - macOS App Launcher (auto-configured by install_app.sh)

BUNDLE_DIR="\$(cd "\$(dirname "\$0")/../.." && pwd)"
RESOURCES_DIR="\$BUNDLE_DIR/Contents/Resources"

# Use the Python that was verified during installation
PYTHON="$PYTHON"

# Fallback: search common locations if the above path is gone
if [ ! -x "\$PYTHON" ]; then
    for py in /opt/homebrew/bin/python3 /usr/local/bin/python3; do
        if [ -x "\$py" ]; then
            PYTHON="\$py"
            break
        fi
    done
fi

if [ -z "\$PYTHON" ] || [ ! -x "\$PYTHON" ]; then
    osascript -e 'display alert "Time Tracker Error" message "Python 3.10+ not found. Please run install_app.sh again." as critical'
    exit 1
fi

# Install rumps if missing
if ! "\$PYTHON" -c "import rumps" 2>/dev/null; then
    osascript -e 'display notification "Installing Time Tracker dependencies..." with title "Time Tracker"'
    "\$PYTHON" -m pip install rumps --quiet 2>/dev/null || \
    "\$PYTHON" -m pip install rumps --user --quiet 2>/dev/null
fi

# Kill any existing instance
pkill -f "timetracker_menu.py" 2>/dev/null
sleep 0.5

# Launch menu bar app
exec "\$PYTHON" "\$RESOURCES_DIR/timetracker_menu.py"
LAUNCHER_EOF

chmod +x "$LAUNCHER"
echo "   ✓ Launcher configured"

# ──────────────────────────────────────────────
# Step 5: Copy app to /Applications
# ──────────────────────────────────────────────
echo
echo "5. Installing to /Applications..."

if [ -d "$APP_DEST" ]; then
    rm -rf "$APP_DEST"
fi

cp -r "$APP_SRC" "$APP_DEST"
chmod +x "$APP_DEST/Contents/MacOS/TimeTracker"
echo "   ✓ Installed: /Applications/Time Tracker.app"

# ──────────────────────────────────────────────
# Step 6: Clear quarantine so macOS won't block it
# ──────────────────────────────────────────────
echo
echo "6. Clearing macOS security quarantine..."
xattr -rd com.apple.quarantine "$APP_DEST" 2>/dev/null || true
echo "   ✓ Done"

# ──────────────────────────────────────────────
# Step 7: Set up data directory
# ──────────────────────────────────────────────
mkdir -p ~/.timetracker

# ──────────────────────────────────────────────
# Done!
# ──────────────────────────────────────────────
echo
echo "────────────────────────────────────────"
echo "✅ Time Tracker installed successfully!"
echo "────────────────────────────────────────"
echo
echo "Launching now..."
open "$APP_DEST"
echo
echo "Look for ⏱️ 00:00:00 in your menu bar (top right of screen)."
echo
echo "To add Time Tracker to your Dock:"
echo "  1. Open Finder → Go → Applications"
echo "  2. Find 'Time Tracker'"
echo "  3. Drag it down to your Dock"
echo
echo "Happy tracking! 🕐"
