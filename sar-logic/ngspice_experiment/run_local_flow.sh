#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NGSPICE="${NGSPICE_BIN:-}"
PYTHON_BIN="${PYTHON_BIN:-$SCRIPT_DIR/../open_source_flow/.venv/bin/python}"

if [[ -z "$NGSPICE" ]]; then
  if command -v ngspice >/dev/null 2>&1; then
    NGSPICE="$(command -v ngspice)"
  elif [[ -x "$SCRIPT_DIR/local_tools/ngspice_pkg/usr/bin/ngspice" ]]; then
    NGSPICE="$SCRIPT_DIR/local_tools/ngspice_pkg/usr/bin/ngspice"
  else
    echo "ngspice not found. Install it or set NGSPICE_BIN." >&2
    exit 1
  fi
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

"$NGSPICE" -b "$SCRIPT_DIR/ngspice_behavioral_sar.cir"
"$PYTHON_BIN" "$SCRIPT_DIR/analyze_ngspice.py"
