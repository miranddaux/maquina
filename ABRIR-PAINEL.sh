#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  exec python3 tools/launch_panel.py "$@"
elif command -v python >/dev/null 2>&1; then
  exec python tools/launch_panel.py "$@"
else
  printf '%s\n' 'Falta Python 3.12 ou superior. Instale em https://www.python.org/downloads/ e consulte docs/INSTALACAO.md.' >&2
  exit 1
fi
