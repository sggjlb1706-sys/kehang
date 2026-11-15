param(
    [string]$Url = 'https://api.deepseek.com/chat/completions',
    [string]$Model = 'deepseek-flash',
    [int]$Port = 8777
)

$ErrorActionPreference = 'Stop'
$taskRepo = 'D:\传智杯\开发工作区\work\kehang-ai-connect-20261115'
$taskPython = 'D:\ANACONDA\python.exe'
$taskUri = [Uri]$Url
if (!$taskUri.IsAbsoluteUri -or $taskUri.UserInfo -or $taskUri.Query -or $taskUri.Fragment -or
    !(($taskUri.Scheme -eq 'https') -or ($taskUri.Scheme -eq 'http' -and $taskUri.Host -in @('127.0.0.1', 'localhost')))) {
    throw '请填写无用户名、密码和查询参数的完整HTTPS接口地址；本机服务可使用HTTP。'
}
if ([string]::IsNullOrWhiteSpace($Model)) { throw '模型名不能为空。' }
if (!(Test-Path -LiteralPath $taskPython -PathType Leaf)) { throw '未找到已有工具Python。' }

# Check the port before asking for a secret. Never stop an unrelated service.
$taskProbe = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $Port)
$taskProbe.ExclusiveAddressUse = $true
try { $taskProbe.Start() } finally { $taskProbe.Stop() }
Push-Location -LiteralPath $taskRepo
try {
    $taskModuleJson = & $taskPython -B -c 'import campuslab.diagnosis as m, json; print(json.dumps(m.__file__, ensure_ascii=True))'
    $taskModule = $taskModuleJson | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or [IO.Path]::GetFullPath($taskModule) -ne (Join-Path $taskRepo 'campuslab\diagnosis.py')) {
        throw '模型客户端未从本次修复目录加载。'
    }
    $taskCommit = & git -c "safe.directory=$taskRepo" rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw '无法确认运行提交。' }
    & git -c "safe.directory=$taskRepo" diff --quiet HEAD -- campuslab/diagnosis.py campuslab/chat.py campuslab/web.py
    if ($LASTEXITCODE -ne 0) { throw '运行代码存在未提交修改，请先固定修订版本。' }
    $taskState = 'D:\传智杯\开发工作区\交付\课航AI接入-20261115-01\运行数据'
    New-Item -ItemType Directory -Path $taskState -Force | Out-Null
    $taskDatabase = Join-Path $taskState 'courses.sqlite'
    $taskReceipt = [ordered]@{
        started_at = [DateTimeOffset]::Now.ToString('o')
        repo = $taskRepo
        commit = $taskCommit
        module = $taskModule
        module_sha256 = (Get-FileHash -LiteralPath $taskModule -Algorithm SHA256).Hash.ToLowerInvariant()
        address = "http://127.0.0.1:$Port/"
        destination = $Url.Trim()
        model = $Model.Trim()
        launcher_pid = $PID
        note = 'Launch provenance only; not proof of a completed model answer.'
    }
    $taskReceipt | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskState '启动记录.json') -Encoding utf8
    Write-Host "运行目录：$taskRepo"
    Write-Host "运行提交：$taskCommit"
    Write-Host "模型接口：$Url"
    Write-Host "模型名称：$Model"
    Write-Host '密钥仅用于本次服务进程，不写入文件。不要把密钥发送到聊天。'
    $taskSecret = Read-Host '请在此隐藏输入API Key' -AsSecureString
    try {
        $env:CAMPUSLAB_AI_URL = $Url.Trim()
        $env:CAMPUSLAB_AI_MODEL = $Model.Trim()
        $env:CAMPUSLAB_AI_KEY = [Net.NetworkCredential]::new('', $taskSecret).Password
        $taskRuntime = Join-Path $taskRepo 'vendor\python-3.13.17-embed-amd64.zip'
        Write-Host "启动后访问 http://127.0.0.1:$Port/，本窗口关闭后该体验服务停止。"
        if (Test-Path -LiteralPath $taskRuntime -PathType Leaf) {
            & $taskPython -B -m campuslab.web --port $Port --database $taskDatabase --runtime-zip $taskRuntime
        } else {
            & $taskPython -B -m campuslab.web --port $Port --database $taskDatabase
        }
    } finally {
        Remove-Item Env:CAMPUSLAB_AI_KEY, Env:CAMPUSLAB_AI_URL, Env:CAMPUSLAB_AI_MODEL -ErrorAction SilentlyContinue
        $taskSecret.Dispose()
    }
} finally {
    Pop-Location
}
