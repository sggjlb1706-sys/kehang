$ErrorActionPreference = 'Stop'
$taskToolRoot = "C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-reuse-ai-20261109\records\runtime\20261109T082117703550Z\dsh-desktop O'Brien `‘引`’ `$literal ``tick"
$taskTarget = "C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-reuse-ai-20261109\records\runtime\20261109T082117703550Z\dsh-desktop O'Brien `‘引`’ `$literal ``tick\missing\DeepSeek Harness.exe"
if (!(Test-Path -LiteralPath $taskToolRoot -PathType Container)) { throw '工具目录不存在，请完整解压' }
$taskSnapshot = Join-Path $taskToolRoot "task.json"
if (!(Test-Path -LiteralPath $taskSnapshot -PathType Leaf)) { throw '缺少task.json，请完整解压本任务工具' }
if ((Get-Content -LiteralPath $taskSnapshot -Raw -Encoding UTF8 | ConvertFrom-Json).id -ne "36ce7be3fc355db2f2a6682da64823e53ea214d11c85ec8cbab60c5041da3581") { throw '工具任务与网页任务不一致，请重新下载' }
$taskRunner = Join-Path $taskToolRoot "runtime\python.exe"
if (!(Test-Path -LiteralPath $taskRunner -PathType Leaf)) { throw '工具Python不存在' }
Set-Location -LiteralPath $taskToolRoot
& $taskRunner -B -m campuslab.collect --task $taskSnapshot --target $taskTarget --output (Join-Path $taskToolRoot "report-B.json") --workspace "C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-reuse-ai-20261109\records\runtime\20261109T082117703550Z\dsh-desktop O'Brien `‘引`’ `$literal ``tick\practice" --provider "deepseek" --model "deepseek-flash"
if ($LASTEXITCODE -ne 0) { throw '采集未完成；请查看错误，不要把旧报告当作本次结果' }