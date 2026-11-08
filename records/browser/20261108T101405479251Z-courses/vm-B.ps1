$ErrorActionPreference = 'Stop'
$taskToolRoot = "C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-courses-20261108\records\runtime\20261108T101405479251Z-courses\vm O'Brien `‘引`’ `$literal ``tick"
$taskTarget = "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"
if (!(Test-Path -LiteralPath $taskToolRoot -PathType Container)) { throw '工具目录不存在，请完整解压' }
$taskSnapshot = Join-Path $taskToolRoot "task.json"
if (!(Test-Path -LiteralPath $taskSnapshot -PathType Leaf)) { throw '缺少task.json，请完整解压本任务工具' }
if ((Get-Content -LiteralPath $taskSnapshot -Raw -Encoding UTF8 | ConvertFrom-Json).id -ne "df51b551eea45c9a3481a6edd97262d43b7084df739c9019cfc4f33c993ad8a6") { throw '工具任务与网页任务不一致，请重新下载' }
$taskRunner = Join-Path $taskToolRoot "runtime\python.exe"
if (!(Test-Path -LiteralPath $taskRunner -PathType Leaf)) { throw '工具Python不存在' }
Set-Location -LiteralPath $taskToolRoot
& $taskRunner -B -m campuslab.collect --task $taskSnapshot --target $taskTarget --output (Join-Path $taskToolRoot "report-B.json")
if ($LASTEXITCODE -ne 0) { throw '采集未完成；请查看错误，不要把旧报告当作本次结果' }