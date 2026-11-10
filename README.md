# AI 实验环境管家 · 开源适配与 AI / Agent 课程版

本轮从正式课程交付 `e0aca9ca04f350c5db0e3d6f197307260eee6276` 完整克隆到独立分支 `codex/reuse-ai-courses-20261109`。沿用双入口、不可变任务、显式目标、四状态、本人手动采集、同组件复检和脱敏分享。原正式版、课程库、旧PDF/ZIP及真实Git历史保留；本轮结果和外部条件以当前HANDOFF及交付回执为准，下方旧课程版说明属于历史。

## 不修改执行策略，直接启动新交付版

使用电脑上已有Python>=3.10，在PowerShell运行：

```powershell
Set-Location -LiteralPath 'D:\传智杯\versions\competition-reuse-ai-20261109'
& 'D:\ANACONDA\python.exe' -B -m campuslab.web --port 8781 --database '.\data\reuse-ai-courses.sqlite' --runtime-zip '.\vendor\python-3.13.17-embed-amd64.zip'
```

打开 `http://127.0.0.1:8781/`，Ctrl+C停止本人启动的服务。换电脑时只需把工具Python路径改为该电脑已有解释器。该入口无需运行`.ps1`或修改执行策略；服务和规则只用标准库。使用新独立课程库，不占用旧版课程数据；端口若已被占用，应选择空闲端口并保持旧服务运行。最终实际启动与下载包核验见新交付回执。

既有官方嵌入Python ZIP随私密本机审阅包提供给检测工具，SHA256为`9E35319BFFEDAB8B36AD44D8F377CB4F1733BCEC257A0B6D04D94F01486DDB38`。工具运行时不代表课程Python、Jupyter内核或Node；没有自动安装新软件、下载模型或启动VM。10分钟启动目标以已有工具Python和完整交付包为条件，不包含从零准备全部课程环境。

## 本轮新增的实际流程

| 课程 | 固定验证与身份 | 本机/外部条件边界 |
|---|---|---|
| Notebook数据分析 | 本人明确选课程Python和kernel.json；实际启动内核，核对sys.executable、NumPy/Pandas、固定数据计算及临时内核清理 | 本轮真实内核/固定计算和负例见records/reuse-ai/notebook；不能用普通Python调用代替内核 |
| AI网页/客户端使用 | DeepSeek固定课堂练习、本人操作记录与成果核对；其他代表工具提供有来源的指导 | 登录和模型连接仍为本人操作；勾选或提交文字不冒充自动验证 |
| DeepSeek API编程 | 指定课程Python、官方目的地/协议/模型、可编辑发送预览、终端安全输入密钥及本人单次同意、固定响应核对 | 协议和失败路径有测试；真实外部调用须本人有效配置与单次同意，未调用未知，模拟不计实测 |
| DSH桌面 | 指定exe、静态PE版本/摘要、自带Electron路线、专用练习/模型/权限/必要工具摘要/产物 | 外部Node不作为桌面缺失条件；当前标准候选路径缺失不等于全机未安装 |
| DSH CLI/Web | 指定Node、package.json和lib/bin.js，核对DSH0.2.2-rc.1与Node>=24.9.0；不执行DSH检测入口 | 所选Node本机满足引擎、明确包路径缺失；未取得真实DSH任务，不冒称成功 |
| Java/JDK | 明确JDK目录，java/javac各自路径/摘要/home/版本；固定源码在专用临时目录编译运行 | 本机Zulu21固定课程实测；不代表Hadoop服务端或Linux来宾通过 |
| SQLite单机SQL | 明确文件身份，只读打开，固定SELECT和固定演示数据；不接受任意SQL | 本机固定课程实测；不把SQLite结果扩为MySQL/PostgreSQL支持 |

原Python、Node、固定Qwen、PyTorch CPU/GPU、VM/Linux仍保留固定任务与报告兼容。每条新任务共用自主/教师入口、课程包、离线指导、原始报告、差异行动与有序复检。教学步骤已阅读、本人声明或AI回复都不能覆盖规则事实。Hadoop及MCP仅保留[逐组件来源路线](docs/Hadoop与框架组合路线-20261109.md)，无集群/服务器实测时保持缺口。

## 开源二次开发与许可

本轮实际**适配修改Educates的两份教学动作模板**：固定提交`d7e018f0cee382a595d2c9ecc6c938da099eb67e`，将固定检查名称、标题、说明及冷却字段移植到`campuslab/teaching.py`，页面保留教学动作的标题/正文/状态结构；原来启动examiner脚本的分派改为导入报告的确定性检查和本人同目标重采。它不能接受shell/args/autostart或自动执行安装。Apache-2.0原LICENSE、NOTICE和原作者声明随包保留。

DSH是单独学习工具：本项目自行实现其静态元数据和必要任务证据接缝，保存官方MIT源码/文档审查材料，未把整个框架、运行时、凭据或插件复制为本产品。Pinokio仅参考准备思路；Labtainers、TLJH、Open WebUI与Dify未采用产品代码。其中Open WebUI/Dify具有各自附加条款，未按普通宽松许可证改品牌或分发。

精确上游路径/版本、采用方式、原字节SHA和修改映射见[开源选型与二次开发](docs/开源选型与二次开发-20261109.md)、[THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)、[reuse.json](docs/reuse.json)及`docs/third-party/*/manifest.json`。参考思路、审查留档和接口对接均与源码适配分别标注，不计为同一种复用。

当前开发/原始设备证据用于本人本机审阅；正式公开/上传前另核对隐私、MP4与Prompt/远程仓库/设备缺口。本人录屏、登录、真实Agent授权、百度网盘上传和提交回执不会由代理生成成功声明。硬截止仍为2026-11-18 15:00北京时间。

## 继承README（2026-11-08历史，仅供来源核对）

# AI 实验环境管家 · 课程能力补全版

服务计算机/大数据课程的环境准备与故障处理：从学习目标或教师任务进入，明确选择目标环境，取得只读证据，按差异手动处理，再核对同一任务、同一组件身份的复检。规则决定通过、缺失、不符合、未知；AI只解释已有证据。

继承正式Node交付 `42d86482fa1540b35fcdda6bbdf15d888f6b8cd1` 的完整真实Git历史；原R1、Node版、原型及旧材料保留原字节。本轮实际提交不回填旧历史。来源见PROVENANCE，实测与未测边界见HANDOFF、docs/验收矩阵.md和records/courses。

## 已有工具 Python 时，10分钟内启动网页

应用只用Python标准库，需要已有Python>=3.10；不安装Web依赖。在PowerShell中：

```powershell
Set-Location -LiteralPath 'D:\传智杯\versions\competition-courses-20261108'
& .\Start-Web.ps1 -Python 'D:\ANACONDA\python.exe' -Port 8772
```

浏览器打开 http://127.0.0.1:8772/ ，Ctrl+C停止。换电脑要改为该电脑已有工具Python的完整路径。10分钟是启动网页的条件性目标，不包含安装课程软件、下载权重或从零准备全部环境。

交付vendor复用既有官方Python3.13.17嵌入ZIP（来源/SHA见docs/reuse.json）。检测工具可自带独立runtime；工具运行时与课程Python分开，不作为课程已安装证据。没有vendor时必须填已有工具Python；Git不提交该第三方二进制。

## 课程与实际支持

| 课程 | 固定验收 | 真实设备边界 |
|---|---|---|
| Python基础 | 指定Python、版本、requests、固定导入 | 本机真实A/B；不是无Python实体设备 |
| Node.js/npm | 指定Node22至25以下、同目录npm10至12以下、固定运行 | 本机Node24/npm11；不从PATH借npm |
| PyTorch CPU | 指定Python3.10至3.15以下、torch>=2.2、导入和float32固定矩阵 | 既有Python3.11.16/torch2.14.0+cu126，真实CPU A/B |
| PyTorch GPU | CPU全部要求、CUDA构建、设备可用性、CUDA:0 UUID、显式GPU实算 | 同一本机RTX4060；CPU成功不能替代GPU |
| 虚拟机/Linux | Windows宿主条件、所选VBoxManage7.x或vmrun CLI1.x、具体UUID/.vmx、来宾身份/Linux/固定运行 | VMware软件只读实测，当前0台运行中VM；宿主部分未知、实例/来宾未知，未声称完整实机通过 |
| 固定本地Qwen | 指定Python/依赖、revision/权重SHA、本地离线输出2与EOS | 仅固定Qwen2.5-0.5B-Instruct；不代表任意模型 |

上述版本及程序均为本项目演示配置；高校来源用于课程方向研究，不冒称学校统一要求。Notebook、Java/JDK、数据库、Hadoop、网络/云计算目前只有带来源目录与扩展路线，未提供这些课程的自动检测。详见docs/课程目录与扩展路线.md。

## 从目标到复检

1. 输入一句学习目标或文字报错。系统提出受支持的任务或必要澄清；确认后才生成固定快照。教师入口不会被自然语言或AI改写要求。
2. 下载并完整解压本任务工具。在采集面板填写工具目录与课程程序完整路径，区分工具Python、课程Python/Node、GPU和虚拟机实例。
3. 可先展开硬件预检，生成并手动运行命令，导入hardware.json；报告含时间、来源及未知原因，不依赖课程软件。准备路线不能代替课程验收。
4. 选择新手/标准/快捷指导。本人检查生成的PowerShell命令后运行，导入原始report-A.json。缺失、版本不符、运行失败和未知分别给出行动及验证办法。
5. 自行处理差异后保存较晚的report-B.json。必须同一快照、同一程序和已确认组件身份；更换Python/GPU/VM实例要重新初检。原始文件不覆盖。
6. 脱敏分享先预览编辑；交流副本不能导入为原始复检报告。AI建议、步骤阅读、硬件准备建议均不提高环境状态。

GPU任务必须主动勾选实际运算。CPU任务不显示GPU触发。固定矩阵为float32，期望`[[4,4],[10,8]]`；首次int64 CUDA不支持的真实开发失败保存在records/courses/torch，不改写成学生环境修复。

## 虚拟机和来宾手动取证

明确选VBoxManage.exe或vmrun.exe绝对路径。VirtualBox实例填UUID；VMware填.vmx完整路径，读取该配置的UUID并核对现有运行列表。只用固定只读命令，不安装、不创建、不启动VM，也不改BIOS、系统或网络。vmrun CLI版本不是Workstation产品版本。

在本人已启动的Linux来宾复制工具根目录guest_probe.py，手动执行以下格式；`TASK_SHA`必须换为网页当前任务摘要，`VM_ID`必须换为宿主已选择的同一个UUID或Windows .vmx路径。Linux shell中用单引号包住含反斜杠/空格的实例标识，若本身含单引号请按shell规则编码：

```sh
python3 guest_probe.py --task-id TASK_SHA --vm-id 'VM_ID' --output guest.json
```

通过本人文件传递把guest.json带回宿主，在采集面板填写其路径。来宾需有可读DMI UUID及machine-id摘要、同任务/实例和30分钟内的固定运行证据；复检B需来宾重新采集。拿不到身份或来宾则未知。此JSON是手动取证的一致性校验，不是密码学远程证明，Linux基础验证也不代表其他实验作业通过。

## 教师任务跨实例传递与手机指导

教师选择已实现的固定类型、发布新任务，导出课程包和离线HTML指导。文件由本人传递；学生在另一实例导入课程包会得到同一个任务摘要与验收条件，并生成该实例本机课程码。请通过可信渠道与教师核对摘要：内容SHA不是教师数字签名。

手机浏览器可打开离线HTML指导，电脑执行采集。外部官方文档链接仍需联网。没有真实可访问的网络目标就不生成二维码；localhost课程链接只在原电脑有效。390px桌面模拟通过不当作实体手机或第二设备证据。

## 固定本地模型准备

唯一任务模型`Qwen/Qwen2.5-0.5B-Instruct`，revision `7ae557604adf67be50417f59c2c2f167def9a775`，权重SHA256 `FDF756FA7FCBE7404D5C60E26BFF1A0C8B8AA1F72CED49E7DD0210FE288FB7FE`。既有权重留在`D:\传智杯\artifacts\local-model\Qwen2.5-0.5B-Instruct`，不复制入仓库，不自动下载。

按硬件预检→所选Python中准备torch>=2.2/transformers>=4.45→从指定revision手动准备完整文件并核对权重→填真实目录预检查→主动勾选固定离线推理→解释结果的顺序操作。允许CPU尝试但最终以运行证据为准；4GiB只是演示规划提醒，不是兼容/性能保证。课程强制本地时，云端/API结果不能替代。

## 文字报错与AI单次同意

没有报告也可粘贴文字报错并预览；此时明确列出未确认的目标、依赖和硬件。默认不配置、不发送。`.env.example`列CAMPUSLAB_AI_URL/MODEL/KEY；仅读取启动进程环境，不自动加载.env，不读取旧进程密钥。

本人安全配置合法免费/本地或另行授权的接口后，页面显示目的地、模型及固定系统说明，预览实际发送内容并可编辑；明确勾选后仅发送一次。25秒超时、不跟随重定向、不重试、不执行建议。失败或格式错误保留规则结果。协议模拟和固定Qwen课程推理均不是实际AI报错诊断成功；本轮无真实诊断调用。

## 开发验证与材料

```powershell
& 'D:\ANACONDA\python.exe' -B -m unittest discover -s tests
node --check web/app.js
& 'D:\ANACONDA\python.exe' -B -m tests.browser_rebuild
& 'D:\ANACONDA\python.exe' -B -m tests.browser_node
& 'D:\ANACONDA\python.exe' -B -m tests.browser_courses
& 'D:\ANACONDA\python.exe' -B -m tools.course_baseline
& 'D:\ANACONDA\python.exe' -B -m tools.verify_legacy
```

浏览器开发验证需已有Playwright和Edge，产品不依赖它们。最终HEAD/清单、测试路径、审查和材料状态见HANDOFF。技术PDF、视频脚本和提交清单分别在output/pdf及docs；脚本不是MP4成片。三条完整真实Prompt链、本人AI协作录屏、评审可访问仓库、实体设备补证和实际上传回执仍须如实核对。

截止2026-11-18 15:00北京时间；沿用本人上传百度网盘、提交作品链接/提取码/有效期的预指导方式。代理不自动公开、推送、上传或发送邮件；不等待官方答复，也不认证参赛资格或已实际提交。
