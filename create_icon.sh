#!/bin/bash
# Run this on your Mac to convert the iconset to a proper .icns file
# Then copy it into the app bundle

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ICONSET="$SCRIPT_DIR/TimeTracker.iconset"
APP_RESOURCES="$SCRIPT_DIR/TimeTracker.app/Contents/Resources"

echo "Converting iconset to .icns..."
iconutil -c icns "$ICONSET" -o "$APP_RESOURCES/AppIcon.icns"

if [ $? -eq 0 ]; then
    echo "✓ AppIcon.icns created successfully"
    # Remove the PNG fallback
    rm -f "$APP_RESOURCES/AppIcon.png"
else
    echo "⚠ Could not create .icns — using PNG fallback (icon may not show in Dock)"
fi
