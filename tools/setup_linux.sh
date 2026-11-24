#!/usr/bin/env bash
# Standard Linux x86_64 development host. Optional templates target Windows x64.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root/rust"
[[ $(uname -sm) == "Linux x86_64" ]] || { echo "Requires Linux x86_64" >&2; exit 2; }
case "${1:-}" in ""|--templates) ;; *) echo "Usage: $0 [--templates]" >&2; exit 2 ;; esac
version=4.7.2-stable
base=https://github.com/godotengine/godot-builds/releases/download/$version
cache="$root/.tools/downloads"
bin="$root/.tools/bin"
mkdir -p "$cache" "$bin"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
download() {
    local name=$1 sha=$2
    if [[ ! -f "$cache/$name" ]] || ! echo "$sha  $cache/$name" | sha256sum --check --status; then
        curl --fail --location --retry 3 "$base/$name" -o "$tmp/$name"
        echo "$sha  $tmp/$name" | sha256sum -c -
        mv "$tmp/$name" "$cache/$name"
    fi
}
editor="Godot_v${version}_linux.x86_64"
editor_sha=8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e
system_editor=$(command -v godot || true)
if [[ ! -f "$bin/godot" ]] || ! echo "$editor_sha  $bin/godot" | sha256sum --check --status; then
    if [[ -f "$system_editor" ]] && echo "$editor_sha  $system_editor" | sha256sum --check --status; then
        install -m755 "$system_editor" "$bin/godot"
    else
        download "$editor.zip" cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4
        unzip -p "$cache/$editor.zip" "$editor" > "$tmp/godot"
        echo "$editor_sha  $tmp/godot" | sha256sum -c -
        install -m755 "$tmp/godot" "$bin/godot"
    fi
fi
if [[ ${1:-} == --templates ]]; then
    name=Godot_v${version}_export_templates.tpz
    download "$name" f298490b8d44d934be425a5a65a51bf15f422428b229a06a6e11d9ffea248011
    templates="${XDG_DATA_HOME:-$HOME/.local/share}/godot/export_templates/4.7.2.stable"
    mkdir -p "$templates"
    unzip -jo "$cache/$name" 'templates/windows_*_x86_64*.exe' 'templates/version.txt' -d "$templates"
fi
export PATH="${CARGO_HOME:-$HOME/.cargo}/bin:$PATH"
if ! command -v rustup >/dev/null; then
    host=https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu
    curl -fsSL --retry 3 "$host/rustup-init" -o "$tmp/rustup-init"
    curl -fsSL --retry 3 "$host/rustup-init.sha256" -o "$tmp/rustup-init.sha256"
    (cd "$tmp" && sha256sum -c rustup-init.sha256)
    chmod +x "$tmp/rustup-init"
    "$tmp/rustup-init" -y --no-modify-path --profile minimal --default-toolchain none
fi
rustup toolchain install 1.94.0 --profile minimal --component rustfmt,clippy
cargo fetch --locked
"$bin/godot" --version
rustc --version
cargo --version
