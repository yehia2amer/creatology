$ErrorActionPreference = 'Stop'
$candidates = @(
    (Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
)
$managed = Join-Path $env:APPDATA 'uv/python'
if (Test-Path -LiteralPath $managed) { $candidates += Get-ChildItem -LiteralPath $managed -Directory -Filter 'cpython-3.12*' | ForEach-Object { Join-Path $_.FullName 'python.exe' } }
$global:MigrationPython = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $global:MigrationPython) { $global:MigrationPython = '3.12' }
