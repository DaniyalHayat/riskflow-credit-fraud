#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 -m riskflow demo
printf 'Open http://127.0.0.1:8000 in your browser.\n'
python3 -m riskflow serve
