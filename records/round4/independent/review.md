# 第四轮独立只读审查

审查者：未参与实现的 `/root/round4_review`；日期：2026-11-15。固定候选 `ed215e43471c880f99d4f4cd5dd707cbdf6bd173`，基线 `e1feb899b08e7b26b5d9a56bd11bc23225f01bb7`。独立单测、浏览器、代码与指南审查完成；范围内未发现可复现的 P0 / P1 / P2 阻断问题。此结论不代替本人体验反馈。

## 亲自执行

- `D:/ANACONDA/python.exe -B -m unittest discover -s tests -p test_*.py`：183 项通过。输出 unit-tests.txt；测试文件内容没有修改。
- 本目录 browser-check.py：7 组独立浏览器检查通过，browser-log.txt、browser-result.json。检查 8 项真实课程和教师选择、5 个分类筛选、6 份工具指南与目录、三档视口、5 个旧课程码 URL、迟到指南请求与迟到课程请求、工具聊天草稿隔离/恢复、未配置时仅预览不能发送，以及 8 门课程准备路径。
- 6 指南 × 1912×948 / 1366×768 / 390×844，共 18 张新截图；期间零 pageerror、零浏览器外部请求、零检查 job。新工具阅读路径没有请求课程 plan、collector、工具包、analysis 或 compare。实际目视重点看过 DSH 桌面宽屏、DSH CLI 笔记本、API 笔记本、本地 Qwen 窄屏、网页工具宽屏、课航 AI 连接窄屏：正文、目录、代码与背景层次可读，没有横向溢出或被课程进度挤占。
- 9 段指南代码仅语法校验：2 段 Python AST、7 段 PowerShell Parser 均通过，python-syntax.json、powershell-syntax.json。不执行代码、不下载依赖/模型、不读取真实 Key。
- app.js、learning.js、extensions.js 均经 `node --check`；按仓库 `* -text` 与既有 CRLF，使用 `git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff e1feb89 ed215e4 --check` 通过。默认 git whitespace 会把 CRLF 的 CR 误报为尾空白，未为消除误报重排产品文件。
- 结束时11项产品/测试文件与固定候选逐字节一致，fixed-product-hashes.json。测试临时 review.sqlite 已移到 data/temp/round4-independent.sqlite，没有把测试数据库作为产品交付证据。

独立浏览器首跑有一次脚本错误：窄屏主动打开聊天后，脚本直接点击被面板覆盖的“全部拓展工具”，等待30秒超时。失败日志 browser-first-harness-failure.txt 与结果原件保留。补上正常的 Escape 收起操作后同脚本通过；该问题由独立执行者发现并归为脚本遗漏，不是用户历史程序 Bug，也没有要求修改产品。

## 代码与内容审查

5 项旧工具路线均在课程列表、课程下拉、教师下拉、AI 支持课程目录移出；Python、Node、Java、Notebook、SQLite、PyTorch CPU/GPU、VM/Linux 仍为课程。新增拓展区含 6 份指南，课航 AI 连接来自原连接帮助；网页指南保留原 Qwen/豆包参考，不增加供应商或 Agent 框架。历史规则/采集器/报告保留，网页载入旧课程码或包经 chooseTask 转入对应指南，不继续课程检测/报告。

核对异步边界：chooseTask 新增 navigationEpoch 校验防止迟到课程响应覆盖工具页；指南加载也受 navigationEpoch 保护。工具聊天 scope 由 guide id 隔离，preview 的服务端上下文拒绝课程/报告混入。发送仍要求先预览、单次 consent、原目的地，票据及规则判定未被本轮修改。首页/选课/工具页的默认收起与课程宽屏展开沿用原规则。

独立浏览核查了[DSH 官方入口](https://www.deepseek.com/harness/)、[官方 Web UI 指南](https://deepseek-harness.github.io/deepseek-harness/en/guide/quickstart)、[DeepSeek Chat Completions 字段](https://api-docs.deepseek.com/api/create-chat-completion/)和[Qwen 模型卡](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)。所述模型/工作区选择、API thinking.type=disabled 与小模型加载方法和资料相符；安装器逐屏、桌面/Web菜单差异、网页登录后与 Qwen/豆包能力已明确未核实，未伪装实测。

## 证据复核与限制

复核主控 records/round4/verification 的19组对比度数值及其浏览器计算代码：文字/按钮/焦点/输入边界使用相应阈值，状态仍带文字。本人未独立重算全部颜色，也未把CSS解析或无溢出当作真人审美反馈。

复核主控新 Python A/B 原件及 compare stable-pass、11组浏览器记录（含本机协议夹具）；没有冒称独立重跑真实 Python、Notebook实训成果、教师重算或真实模型。此审查的183项单测与7组浏览器为亲跑，其余明确为复核。

未安装工具、读取真实凭据、发付费API、启动Agent任务或本地推理；未测试实体手机、独立新手、真实账号登录、全部桌面安装器版本或所有外部服务。主控随后补充的交付文档/截图不是本候选代码审查的前提；若产品源码改变需另行增量复核。没有发布/上传/正式提交，也不宣称三条完整Prompt链或本人满意。
