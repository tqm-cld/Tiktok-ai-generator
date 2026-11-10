#!/usr/bin/env bash
# Startet den TikTok-KI-Generator (macOS & Linux).
# Beim ersten Start wird alles Nötige automatisch installiert.
set -e
cd "$(dirname "$0")"

PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    PY="$candidate"; break
  fi
done
if [ -z "$PY" ]; then
  echo "❌ Python 3.10 oder neuer wurde nicht gefunden."
  echo "   Bitte installieren: https://www.python.org/downloads/"
  read -r -p "Drücke Enter zum Schließen …" _
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "📦 Erster Start: richte Programmumgebung ein (dauert 1–3 Minuten) …"
  "$PY" -m venv .venv
fi
source .venv/bin/activate

# Pakete nur neu installieren, wenn requirements.txt sich geändert hat
if [ ! -f .venv/.installed ] || ! cmp -s requirements.txt .venv/.installed; then
  echo "📦 Installiere benötigte Pakete …"
  python -m pip install --upgrade pip >/dev/null
  python -m pip install -r requirements.txt
  cp requirements.txt .venv/.installed
fi

python app.py
