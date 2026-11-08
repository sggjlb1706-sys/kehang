# AI实验环境管家：R1 Node.js/npm 扩展版
2026-11-08在正式R1完整Git历史上继续开发，原版本原字节保留。新增Windows Node.js/npm示例课程；本轮验证、Prompt链核查及材料缺口见HANDOFF、REVIEW和docs/验收矩阵.md。以下首轮来源说明继续有效。
2026-11-03从最小骨架开始真实重建。旧M0—M4与2026-11-01版本保留，本仓库不伪装旧Git历史。首次提交无完整应用；产品代码按实际模块开发提交。

当前支持Windows上的Python基础课程、Node.js/npm示例课程和固定Qwen2.5-0.5B本地任务：自主目标/教师课程码共享规则，三种指导模式，独立检测工具、同目标复检、脱敏导出、可选证据AI解释。未完成事项见下文。

## 10分钟内启动网页

服务端使用已有Python3.10或更高版本，网页与规则引擎仅使用标准库，无需安装Web依赖。在本机PowerShell：

```powershell
Set-Location -LiteralPath 'D:\传智杯\versions\competition-r1-node-20261108'
& .\Start-Web.ps1 -Python 'D:\ANACONDA\python.exe' -Port 8772
```

打开 http://127.0.0.1:8772/ 。Ctrl+C结束。换电脑时须把上述Python路径改为已有工具Python；没有服务端Python时无法启动本网页。此10分钟指已有工具Python时启动并查看规则，不包含从零安装课程环境、下载模型或完整部署所需时间。

交付副本的vendor目录放置既有官方Python3.13.17嵌入运行时ZIP，Start-Web会显式启用独立工具下载；Git不提交该二进制，来源与SHA见docs/reuse.json。没有vendor时提供Python工具包，页面要求已有工具Python，不冒充独立可运行。

## 学生操作

1. 选Python、Node.js/npm或固定本地模型目标，或输入教师课程码；核对任务要求。
2. 查看新手/标准/快捷指导，下载并完整解压检测工具。工具包里的task.json与当前任务固定对应。
3. 填工具目录和课程Python或Node.js完整路径；本地模型任务还填写模型目录。生成命令并由本人在目标电脑手动运行。
4. 导入report-A.json。处理差异后，保持同一任务、解释器和模型目录，选择B再次采集并导入。
5. 分享前查看自动基础脱敏后的内容，可继续编辑。交流副本不能替代原始检测报告。

没有课程Python时，可用包内runtime生成完整缺失/未知报告；工具运行时不能作为课程Python。工具不会安装依赖或更改PATH。不存在路径的本机测试不等于真实无Python设备测试。

## 教师操作

展开“我是教师”，选择场景、填写名称和Python范围后发布。每次发布生成新课程码与不可变快照；Python场景可填写requests最低版本。本地模型场景固定torch/transformers和指定权重。

Node场景采用固定演示范围，隐藏Python选项：Windows、Node.js>=22.0且<25.0、npm>=10.0且<12.0。默认名称与自主入口一致时，两者是同一个任务摘要；更名会形成不同快照，不能混用报告。这些范围来自本项目演示配置，不代表真实学校课程，也不是全部组合兼容承诺。

## Node.js/npm 操作

明确选择课程使用的node.exe完整路径，例如本轮实测的`D:\Program Files\nodejs\node.exe`，不能只写`node`。工具只采集，不查PATH后替你选择。npm固定为所选Node目录的`node_modules\npm\bin\npm-cli.js`，直接由该Node执行`--version`；系统PATH里其他npm、npm.cmd和npm.ps1不算本任务证据。若所用版本管理器使用链接或npm安装在其他前缀，本固定示例可能拒绝该身份或报告缺失；选择实际程序及配套目录，不借其他环境凑通过。

下载并完整解压工具；用包内Python runtime或已有工具Python执行网页生成命令，工具Python不是课程Node。报告记录Node实际路径/版本、npm CLI及运行Node身份/版本/错误、固定数组映射及断言程序结果、时区时间和实际子命令。只有四项事实完整且符合才通过。初检A与复检B须同一快照、同一node.exe路径且B时间更晚；改变目标时重新开始A。安装和修复由本人决定，网页不会执行命令。

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
& 'D:\ANACONDA\python.exe' -B -m tests.browser_node
& 'D:\ANACONDA\python.exe' -B -m tools.verify_legacy
```

浏览器检查需要开发机既有Playwright与Microsoft Edge，以及脚本明确引用的既有嵌入运行时；应用运行不依赖这些开发检查工具。实际版本、结果与证据位置见HANDOFF.md及docs/实现与证据说明.md。

尚缺本版本真实无Python设备、第二设备和实体手机、新手独立安装体验、真实AI诊断；正式视频/PDF/仓库评审访问、至少三条完整核心Prompt链及赛事资格也未完成。Prompt链已逐项核查，发现的缺口见docs/Prompt链逐项核查.md；不等于确认三链齐全。任意自然语言目标映射和其他模型未实现。官网2026-11-08核对有时间冲突，按较早的2026-11-18准备，原文来源见docs/赛事要求核查-20261108.md。旧材料SHA及历史失败完整保留，不能宣布整体参赛合规通过。
