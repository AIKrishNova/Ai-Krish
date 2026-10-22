#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$HOME/Applications/AI Krish.app"

echo "Creating AI Krish macOS app bundle at: $APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Copy Icon
if [ -f "$PROJECT_DIR/assets/AppIcon.icns" ]; then
    cp "$PROJECT_DIR/assets/AppIcon.icns" "$APP_DIR/Contents/Resources/AppIcon.icns"
fi

# Create Launcher
cat > "$APP_DIR/Contents/MacOS/AI Krish" << 'EOF'
#!/bin/bash
PROJECT_DIR="$HOME/Desktop/Ai-Krish"
cd "$PROJECT_DIR"
PYTHON_BIN="$HOME/.ai-krish/venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi
exec "$PYTHON_BIN" -m assistant.ui --debug
EOF
chmod +x "$APP_DIR/Contents/MacOS/AI Krish"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDisplayName</key>
	<string>AI Krish</string>
	<key>CFBundleExecutable</key>
	<string>AI Krish</string>
	<key>CFBundleIconFile</key>
	<string>AppIcon</string>
	<key>CFBundleIdentifier</key>
	<string>com.aikrishnova.krish</string>
	<key>CFBundleName</key>
	<string>AI Krish</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleVersion</key>
	<string>1.0</string>
	<key>LSUIElement</key>
	<true/>
	<key>NSMicrophoneUsageDescription</key>
	<string>AI Krish needs microphone access for voice commands.</string>
</dict>
</plist>
EOF

echo "AI Krish.app bundle created successfully."
