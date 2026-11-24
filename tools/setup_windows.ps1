param([switch]$Templates)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
$bin = "$root/.tools/bin"
$cache = "$root/.tools/downloads"
New-Item -ItemType Directory -Force $bin, $cache | Out-Null
function Get-VerifiedArchive($name, $hash) {
    $file = Join-Path $cache $name
    if (!(Test-Path $file) -or (Get-FileHash $file).Hash -ne $hash) {
        $tmp = [IO.Path]::GetTempFileName()
        try {
            Invoke-WebRequest "https://github.com/godotengine/godot-builds/releases/download/4.7.2-stable/$name" -OutFile $tmp
            if ((Get-FileHash $tmp).Hash -ne $hash) { throw "SHA256 mismatch: $name" }
            Move-Item -Force $tmp $file
        } finally { if (Test-Path $tmp) { Remove-Item $tmp } }
    }
    return $file
}
$archive = Get-VerifiedArchive "Godot_v4.7.2-stable_win64.exe.zip" "731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953"
Expand-Archive $archive -DestinationPath $bin -Force
if ($Templates) {
    $archive = Get-VerifiedArchive "Godot_v4.7.2-stable_export_templates.tpz" "f298490b8d44d934be425a5a65a51bf15f422428b229a06a6e11d9ffea248011"
    $dest = "$env:APPDATA/Godot/export_templates/4.7.2.stable"
    New-Item -ItemType Directory -Force $dest | Out-Null
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead($archive)
    try {
        foreach ($entry in $zip.Entries) {
            if ($entry.FullName -match '^templates/(windows_(release|debug)_x86_64(_console)?\.exe|version\.txt)$') {
                [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, (Join-Path $dest $entry.Name), $true)
            }
        }
    } finally { $zip.Dispose() }
}
Push-Location "$root/rust"
try {
    rustup toolchain install 1.94.0 --profile minimal --component rustfmt,clippy
    if ($LASTEXITCODE) { throw "Rust installation failed" }
    cargo fetch --locked
    if ($LASTEXITCODE) { throw "cargo fetch failed" }
} finally { Pop-Location }
