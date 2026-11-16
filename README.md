# 课航

课程环境准备、Notebook + SQLite 连续实训与教师工作台。2026-11-16 起功能冻结。

当前课程为 **8 项**：Python、Node.js/npm、Java/JDK、Notebook/数据分析、SQLite、PyTorch CPU、PyTorch GPU、虚拟机/Linux。**6 份拓展指南**：DSH 桌面、DSH CLI/Web、DeepSeek API、AI 网页与客户端、本地模型工具、课航 AI 连接帮助。指南直接阅读，无检测、报告或复检前置。

规则核对报告，AI 仅作解释。聊天按页面开合；每轮先预览脱敏上下文和目的地，再同意发送。连续实训核验限定成果的数值与版本，不能证明原创或学习掌握。

## 10 分钟启动与复现

前提：Windows 10/11、已有 Python 3.10 或以上（含 sqlite3）、PowerShell 7 和现代浏览器。网页服务仅依赖 Python 标准库，无需 pip 安装。完整解压到有 `campuslab`、`web`、`Start-Web.ps1` 的同一目录，勿在 ZIP 内直接运行。

```powershell
Set-Location -LiteralPath '<本次完整解压目录>'
pwsh -NoProfile -File .\Start-Web.ps1 -Python python -Port 18776
```

`python` 须为现有真实解释器；也可将 `-Python` 的值替换为自己的绝对路径。浏览器打开 <http://127.0.0.1:18776/>，按 Ctrl+C 停止。端口占用时选择空闲端口，不结束陌生进程。无需设置全局 Git 信任或修改执行策略。

不使用 PowerShell 的启动方式（同样从解压根目录执行）：

```powershell
python -B -m campuslab.web --port 18776 --database .\data\review.sqlite --runtime-zip .\vendor\python-3.13.17-embed-amd64.zip
```

全新副本首次启动创建本副本的空课程库，不需要开发数据库或后台服务。`vendor` 中的官方嵌入包供下载检测工具使用，不是学生课程环境。源码仓库不追踪该二进制；本轮评审包另行携带固定 SHA 的同一文件，详见 [DEPENDENCIES.md](DEPENDENCIES.md)。

1. 打开首页，开始选课；确认 8 项课程和 6 份拓展指南。选择 Python，准备页运行固定本机检查；复检须保持同一任务和目标，原报告保留。
2. 从首页进入连续实训，按步骤下载、完整解压资料。在已有课程 Jupyter 内核中完成 Notebook，再用课程 Python 运行 SQLite 练习，导出实训成果并在提交页核验。
3. 教师工作台可发布并导出资料；学生在另一个干净实例导入。第二实例须使用另一端口和数据库。教师可核对完成物，数值通过与环境通过分别报告。
4. 打开任一拓展指南，应直接阅读。未配置 AI 时可查看预览，不能发送；课程、检测和实训可独立使用。

10 分钟内完成实训计算还要求**已有** Jupyter、jupyter_client、ipykernel、NumPy、Pandas 和绑定所选 Python 的 kernel.json，具体版本见依赖清单。不承诺新装这些环境、GPU、离线模型或第二台电脑也能在 10 分钟内完成。本轮同机干净目录的实测条件与耗时以交付检查记录为准。

## 可选模型连接

`.env.example` 是空白进程变量模板，**不会自动加载**。没有 Key、没有模型配置也能使用核心课堂流程。需要本人决定是否发送时，在本机隐藏输入 Key：

```powershell
pwsh -NoProfile -File .\tools\Start-ConnectedModel.ps1 -Python python -Port 18777
```

默认目的地 `https://api.deepseek.com/chat/completions`，模型 `deepseek-flash`。接口地址和模型名可按已支持的兼容协议用 `-Url`、`-Model` 指定；远程必须 HTTPS，本机回环服务允许 HTTP。脚本不读取旧进程或文件中的 Key，凭据不写盘；数据和启动回执位于本副本 `data/connected`。源码 Git 副本检查实际导入位置与已提交模块；无 Git 的评审包检查 `SOURCE-MANIFEST.json` 中的模块摘要。该清单用于一致性校验，不是数字签名。

本人仍须逐轮检查发送预览，再点“同意并发送这条”。预览包含当前课程/步骤、可用报告摘要与最近上下文；最多最近 10 轮，票据 10 分钟有效且只能用一次。聊天按课程隔离，刷新清空会话；失败保留问题，不伪造回答，规则结论不被模型改变。不自动重试付费请求、不启用联网工具或 Agent。

**当前真实证据**：2026-11-15，运行产品 `6185471` 经真实 DeepSeek 服务完成两轮短问答及上下文追问，均逐轮预览同意；本人随后反馈“两轮均有正常回答”。记录归档于 `1785ab4`。[修复、时序与边界](docs/AI接入与兼容修复.md)。本轮 `7d4354e` 仅修复启动目录/解释器可迁移性，未改变模型传输或页面；2026-11-16 未追加任何真实模型调用。历史“尚未真实接入”描述不能覆盖这些更晚证据。

## 版本、材料与共享范围

功能冻结基线 `1785ab42b06f0c1bf422027ce508075740675647`；提交收尾启动修复 `7d4354e76e437a73ad03913690776fbb10a7d524`。[问题、证据与改动](docs/提交收尾启动修复.md)。最终候选 HEAD、逐文件 SHA、实际新目录检查与独立复核由本轮交付目录的 `CANDIDATE.json`、`提交材料索引.md`、`独立复核报告.md` 固定；评审运行包的 `SOURCE-MANIFEST.json` 记录相同候选。

当前 PDF/MP4 和 Prompt 原话索引在带日期的独立交付材料目录；旧 `output/pdf`、`output/video` 及阶段验收仅说明其当时版本，不充当当前提交媒体。当前链条核定见 [docs/提交收尾Prompt链核定.md](docs/提交收尾Prompt链核定.md)，不能用普通问答或多个同一流程报错凑出三条核心开发链。

评审运行包不含 `.git`、私人数据库、Key、无关聊天或旧设备报告；**它不替代完整 Git 历史**。原始完整历史另保留本地 bundle，含历史设备路径、可见协作节选、作者元数据及测试库，只供本人核对并授权受限评审访问。不要直接公开整个开发目录，也不要为公开而擅自改写原历史。

采用与许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)、`docs/third-party`；指南资料及核查日期见 [第四轮指南来源](docs/第四轮指南来源.md)。本项目没有新增第三方运行依赖，未替作者选择新的开源许可。未公开仓库、上传、部署或正式提交；没有正式回执就视为未提交。
