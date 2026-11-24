param([ValidateSet("debug","release")][string]$Mode = "debug")
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Push-Location "$root/rust"
try {
    $flags = @()
    if ($Mode -eq "release") { $flags += "--release" }
    cargo build --locked -p space_die_ext @flags
    if ($LASTEXITCODE) { throw "cargo build failed" }
    $json = cargo metadata --locked --no-deps --format-version 1
    if ($LASTEXITCODE) { throw "cargo metadata failed" }
    $target = ($json | ConvertFrom-Json).target_directory
    $out = "$root/godot/native/bin/windows/$Mode"
    New-Item -ItemType Directory -Force $out | Out-Null
    Copy-Item "$target/$Mode/space_die_ext.dll" $out -Force
    $cache = "$root/godot/.godot"
    New-Item -ItemType Directory -Force $cache | Out-Null
    if (!(Test-Path "$cache/extension_list.cfg")) {
        Set-Content "$cache/extension_list.cfg" "res://native/space_die.gdextension" -Encoding ascii
    }
} finally { Pop-Location }
