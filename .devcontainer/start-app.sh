#!/usr/bin/env bash
# Startet die App im Hintergrund. Wird bei jedem Start des Codespace automatisch ausgeführt.
cd "$(dirname "$0")/.."
pkill -f "python app.py" 2>/dev/null || true
NO_BROWSER=1 setsid nohup python app.py > /tmp/tiktok-app.log 2>&1 < /dev/null &
echo "✅ App gestartet auf Port 8765 (Protokoll: /tmp/tiktok-app.log)"
