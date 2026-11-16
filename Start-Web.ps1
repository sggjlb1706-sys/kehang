param([string]$Python = 'python', [int]$Port = 8776)
$ErrorActionPreference = 'Stop'
$Python = (Get-Command $Python -CommandType Application -ErrorAction Stop).Source
Set-Location -LiteralPath $PSScriptRoot
$taskTemporary = Join-Path $PSScriptRoot 'data\temp'
New-Item -ItemType Directory -Path $taskTemporary -Force | Out-Null
$env:TEMP = $taskTemporary
$env:TMP = $taskTemporary
$taskRuntimeZip = Join-Path $PSScriptRoot 'vendor\python-3.13.17-embed-amd64.zip'
if (Test-Path -LiteralPath $taskRuntimeZip -PathType Leaf) {
    & $Python -B -m campuslab.web --port $Port --runtime-zip $taskRuntimeZip
} else {
    & $Python -B -m campuslab.web --port $Port
}
