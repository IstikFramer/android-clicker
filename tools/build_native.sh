#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root/rust"
mode=${1:-debug}
case "$mode" in
  debug) flags=() ;;
  release) flags=(--release) ;;
  *) echo "Usage: $0 [debug|release]" >&2; exit 2 ;;
esac
cargo build --locked -p space_die_ext "${flags[@]}"
target=$(cargo metadata --locked --no-deps --format-version 1 | python3 -c 'import json,sys; print(json.load(sys.stdin)["target_directory"])')
install -Dm755 "$target/$mode/libspace_die_ext.so" "$root/godot/native/bin/linux/$mode/libspace_die_ext.so"

# Preload gdext during engine startup, including the very first editor import.
cache="$root/godot/.godot"
mkdir -p "$cache"
if [[ ! -e "$cache/extension_list.cfg" ]]; then
    echo 'res://native/space_die.gdextension' > "$cache/extension_list.cfg"
fi
