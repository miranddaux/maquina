#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  exec python3 INSTALAR-SKILL.py "$@"
elif command -v python >/dev/null 2>&1; then
  exec python INSTALAR-SKILL.py "$@"
else
  printf '%s\n' 'Instale Python 3.12 ou superior: https://www.python.org/downloads/' >&2
  exit 1
fi
