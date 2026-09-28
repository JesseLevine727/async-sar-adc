#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IVERILOG="${IVERILOG_BIN:-}"
VVP="${VVP_BIN:-}"

if [[ -z "$IVERILOG" ]]; then
  if command -v iverilog >/dev/null 2>&1; then
    IVERILOG="$(command -v iverilog)"
    VVP="$(command -v vvp)"
  elif [[ -x "$SCRIPT_DIR/local_tools/iverilog_pkg/usr/bin/iverilog" ]]; then
    IVERILOG="$SCRIPT_DIR/local_tools/iverilog_pkg/usr/bin/iverilog"
    VVP="$SCRIPT_DIR/local_tools/iverilog_pkg/usr/bin/vvp"
  else
    echo "iverilog not found. Install it or set IVERILOG_BIN." >&2
    exit 1
  fi
fi

"$IVERILOG" -g2012 -o "$SCRIPT_DIR/async_sar_tb" \
  "$SCRIPT_DIR/tb_async_sar.sv" \
  "$SCRIPT_DIR/sar_logic_async.sv" \
  "$SCRIPT_DIR/strongarm_comp_model.sv"

"$VVP" "$SCRIPT_DIR/async_sar_tb"
python3 "$SCRIPT_DIR/analyze_enob.py"
