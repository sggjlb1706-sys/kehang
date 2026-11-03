param([string]$Python = 'D:\ANACONDA\python.exe', [int]$Port = 8772)
$ErrorActionPreference = 'Stop'
if (!(Test-Path -LiteralPath $Python -PathType Leaf)) { throw '请通过 -Python 指定已有的工具 Python 完整路径' }
Set-Location -LiteralPath $PSScriptRoot
$taskRuntimeZip = Join-Path $PSScriptRoot 'vendor\python-3.13.17-embed-amd64.zip'
if (Test-Path -LiteralPath $taskRuntimeZip -PathType Leaf) {
    & $Python -B -m campuslab.web --port $Port --runtime-zip $taskRuntimeZip
} else {
    & $Python -B -m campuslab.web --port $Port
}
