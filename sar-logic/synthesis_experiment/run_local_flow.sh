#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$ROOT_DIR/local_tools"
PKG_DIR="$TOOLS_DIR/yosys_pkg"

if command -v yosys >/dev/null 2>&1; then
  YOSYS_BIN="$(command -v yosys)"
elif [[ -x "$PKG_DIR/usr/bin/yosys" ]]; then
  YOSYS_BIN="$PKG_DIR/usr/bin/yosys"
else
  echo "yosys not found. Extract the local package first." >&2
  exit 1
fi

export ABCEXTERNAL="${PKG_DIR}/usr/bin/yosys-abc"

cd "$ROOT_DIR"
"$YOSYS_BIN" -s synth.ys | tee synthesis.log
