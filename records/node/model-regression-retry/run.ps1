$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$taskRepository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
Set-Location -LiteralPath $taskRepository
$taskSpec = Join-Path $PSScriptRoot 'task.json'
$taskModelPython = 'C:\Users\DELL\Documents\ChatGPT\传智杯\work\model-venv\Scripts\python.exe'
$taskModelDirectory = 'D:\传智杯\artifacts\local-model\Qwen2.5-0.5B-Instruct'
& 'D:\ANACONDA\python.exe' -B -m campuslab.collect --task $taskSpec --target $taskModelPython --model-dir $taskModelDirectory --output (Join-Path $PSScriptRoot 'before.json')
if ($LASTEXITCODE -ne 0) { throw 'Model precheck failed' }
& 'D:\ANACONDA\python.exe' -B -m campuslab.collect --task $taskSpec --target $taskModelPython --model-dir $taskModelDirectory --infer --output (Join-Path $PSScriptRoot 'after.json')
if ($LASTEXITCODE -ne 0) { throw 'Model inference collection failed' }
