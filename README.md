# AI实验环境管家：正式参赛版真实重建
2026-11-03从最小骨架开始真实重建。旧M0—M4与2026-11-01版本保留，本仓库不伪装旧Git历史。首次提交无完整应用；产品代码按实际模块开发提交。

本轮R1支持Windows上的Python基础课程和固定Qwen2.5-0.5B本地任务：自主目标/教师课程码共享规则，三种指导模式，独立检测工具、同目标复检、脱敏导出、可选证据AI解释。未完成事项见下文。

## 10分钟内启动网页

服务端使用已有Python3.10或更高版本，网页与规则引擎仅使用标准库，无需安装Web依赖。在本机PowerShell：

```powershell
Set-Location -LiteralPath 'D:\传智杯\versions\competition-rebuild-20261103'
& .\Start-Web.ps1 -Python 'D:\ANACONDA\python.exe' -Port 8772
```

打开 http://127.0.0.1:8772/ 。Ctrl+C结束。换电脑时须把上述Python路径改为已有工具Python；没有服务端Python时无法启动本网页。此10分钟指已有工具Python时启动并查看规则，不包含从零安装课程环境、下载模型或完整部署所需时间。

交付副本的vendor目录放置既有官方Python3.13.17嵌入运行时ZIP，Start-Web会显式启用独立工具下载；Git不提交该二进制，来源与SHA见docs/reuse.json。没有vendor时提供Python工具包，页面要求已有工具Python，不冒充独立可运行。

## 学生操作

1. 选Python或固定本地模型目标，或输入教师课程码；核对任务要求。
2. 查看新手/标准/快捷指导，下载并完整解压检测工具。工具包里的task.json与当前任务固定对应。
3. 填工具目录、课程解释器完整路径；本地模型任务还填写模型目录。生成命令并由本人在目标电脑手动运行。
4. 导入report-A.json。处理差异后，保持同一任务、解释器和模型目录，选择B再次采集并导入。
5. 分享前查看自动基础脱敏后的内容，可继续编辑。交流副本不能替代原始检测报告。

没有课程Python时，可用包内runtime生成完整缺失/未知报告；工具运行时不能作为课程Python。工具不会安装依赖或更改PATH。不存在路径的本机测试不等于真实无Python设备测试。

## 教师操作

展开“我是教师”，选择场景、填写名称和Python范围后发布。每次发布生成新课程码与不可变快照；Python场景可填写requests最低版本。本地模型场景固定torch/transformers和指定权重。

课程码/链接目前仅供本机打开。同一localhost链接不能用于另一台电脑；未实现受控局域网或公网分享，旧M4跨设备证据不套用到本版。

## 本地模型任务

唯一模型是Qwen/Qwen2.5-0.5B-Instruct，revision与权重SHA写入固定任务及docs/reuse.json。既有权重位于D:\传智杯\artifacts\local-model\Qwen2.5-0.5B-Instruct；不随仓库复制，代码不会联网下载。

目标环境需有torch>=2.2、transformers>=4.45。自行依据官方说明准备；本轮实际环境是Python3.11.16、torch2.14.0+cu126、transformers4.57.1和RTX4060，不承诺所有满足最低版本的组合均兼容。先预检查，再勾选执行固定离线推理；固定问题输出2且EOS正常才算通过。CPU路径可用但本轮未实际验证。4GiB提示仅为本演示操作建议，性能与兼容性需实际运行确认。

## 可选AI解释与环境变量

默认不配置、也不发送请求。.env.example列出CAMPUSLAB_AI_URL、CAMPUSLAB_AI_MODEL、CAMPUSLAB_AI_KEY；程序只读取启动进程环境，不自动加载.env，不读取旧进程密钥。

本人安全设置单一接口后重启服务，页面显示目的地和固定系统说明，生成可编辑脱敏预览；核对并勾选后才发送一次。密钥只在服务端进程内，不进入网页或日志。接口采用Chat Completions JSON协议；25秒超时、不自动重试、不跟随重定向。任何失败均保留规则结果。建议命令始终由本人选择执行。

本轮只做本机假服务协议测试，未发送收费模型请求；固定Qwen离线课程推理不等于AI报错诊断已实测成功。

## 验证与限制

```powershell
& 'D:\ANACONDA\python.exe' -B -m unittest discover -s tests
node --check web/app.js
& 'D:\ANACONDA\python.exe' -B -m tests.browser_rebuild
& 'D:\ANACONDA\python.exe' -B -m tools.verify_legacy
```

浏览器检查需要开发机既有Playwright与Microsoft Edge，以及脚本明确引用的既有嵌入运行时；应用运行不依赖这些开发检查工具。实际版本、结果与证据位置见HANDOFF.md及docs/实现与证据说明.md。

尚缺本版本真实无Python设备、第二设备和实体手机、新手独立安装体验、真实AI诊断；正式视频/PDF/仓库评审访问、至少三条完整核心Prompt链的逐项审核与赛事资格也未完成。Node.js、任意自然语言目标映射和其他模型未实现。旧材料SHA及历史失败完整保留，不能因重建而宣布整体参赛合规通过。
