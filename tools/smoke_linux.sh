#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
export PATH="$root/.tools/bin:$PATH"
exec python3 "$root/tools/check_godot.py" "$@"
