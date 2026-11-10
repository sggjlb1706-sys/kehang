# 开源适配与AI课程版验收和证据

核对日期：2026-11-10。已审产品HEAD `2c5ade24c512a6b15c7111f808192f480627c4fb`；清单 `records/review/reuse-ai-final-candidate.json`，SHA256 `BD242703233272836DC99B6B819339EA30CC26CD9F404F7FB48E6FC0B6DFC615`。独立delta确认初审2P2+1P3全部闭合、无新增产品阻塞。本页索引与REVIEW/独立全文共同说明范围，原候选和首次失败保留。

## 修复后测试与网页范围

`records/reuse-ai/review-fixes-green.txt`记录115项单测通过，覆盖旧任务、新固定输入/完整事实、错配/同目标比较、API同意/协议、DSH摘要、教学动作和命令编码，新增独立发现的三条回归。初审112项输出 `unit-final-pre-review-2.txt`及先失败 `review-remaining-red.txt`保留。构造报告/mock响应只证明代码路径。

| 最终集中浏览器记录 | 组数 | 主要范围 |
|---|---:|---|
| records/browser/20261110T003103731709Z/results.json | 10 | 原Python/模型网页、双入口、下载命令、未知/拒绝与过期响应 |
| records/browser/20261110T003116207099Z-node/results.json | 9 | 原Node/npm同源A/B、教师任务、错配/不完整、模式及390px |
| records/browser/20261110T003104245789Z-courses/results.json | 9 | GPU真实显式运算、VM软件与来宾未知、硬件、教师包/离线HTML |
| records/reuse-ai/browser-data/20261110T003103340935Z/results.json | 18 | Notebook/JDK/SQLite实际下载/原样命令A/B、教师跨库、模式/键盘/390px/状态清理 |
| records/reuse-ai/browser-ai/20261110T003136119642Z/results.json | 6 | API预览/未调用A/B、网页学习记录、DSH双路缺失/未知、包/指导/分享 |

五套合计52组，全部为修复后重新运行，执行方核对源SHA匹配新候选；页面错误和外部HTTP(S)请求均为0。额外重跑 `records/courses/review-ui/20261110T003123Z/results.json`三项构造UI回归通过：换目标清旧建议、延迟教师发布不能替换新任务、无效初检清旧差异指导。它们不是学生真实环境修复。

新数据/AI/DSH命令以PowerShell `-Command`执行，未覆盖或修改执行策略。旧浏览器脚本的进程级`-ExecutionPolicy Bypass`不等于全局策略变更；正式交付另以README的Python模块直启核验。以上均不构成干净无Python设备实测。

## 原始运行与负例

| 场景 | 当前可定位证据 | 结论和边界 |
|---|---|---|
| Notebook | records/reuse-ai/notebook/20261109T082430131236Z/及final-shared-verification.json | 所选Python/kernel.json真内核；NumPy/Pandas、数组42、分组A30/B12、三行和清理；十项A/B stable-pass |
| Java | records/reuse-ai/java/20261109T082430131236Z/及final-shared-verification.json | Zulu21的java/javac21.0.1、各自SHA/home、临时编译运行42，六项A/B stable-pass；规则初审反例/修复另列 |
| SQLite | records/reuse-ai/sqlite/20261109T082430131236Z/及final-shared-verification.json | 最终含database_mode快照；SQLite3.50.2只读固定分组，前后SHA相同，五项A/B stable-pass |
| Qwen | records/courses/model/20261110T003151Z/ | 修复后正确model-venv重新真实推理；A未知，B本地离线输出2/EOS、七项通过，verified。20261109T082014Z错选PyTorch环境缺transformers保留，不跨目标称修复 |
| PyTorch/VM | 上表课程浏览器目录及原始A/B | GPU固定运算为本机实际证据；VMware软件可核对，实例/来宾未知，未创建或启动VM |
| API | browser-ai目录deepseek-api-A/B.json及tests/test_ai_course.py | 实际采集Python/标准库及固定请求，run=not_called。认证、余额、模型/协议、限流、超时、网络/运行失败等为协议测试，真实调用0 |
| DSH | records/reuse-ai/dsh/real-metadata/和browser-ai双路线A/B | 明确Node24.21.0满足CLI引擎、明确包缺失；桌面候选缺失，无外部Node项。无真实DSH、模型、授权或工具回合 |
| AI网页记录 | browser-ai的constructed-self-record.json和constructed-web-report.json | 明确构造夹具；正确数字只完成学习记录/成果，web:login仍unknown、整体不通过；未替本人登录或做网页练习 |

Notebook真实Pandas缺失负例在 `records/reuse-ai/notebook/pandas-missing-real-20261109T081140879259Z/`：专用构造kernelspec指向已有PyTorch解释器，真内核Pandas缺失、运算不通过；未注册或修改系统内核。缺失目标、错内核、不同JDK/home、变更数据库/WAL等分别见模块README和tests，构造不冒充真实学生故障。

首次模块缺失、测试/验证脚本语法错误、旧目录断言过时和折叠面板导致自动化超时均保留。当前通过记录只替换其验收适用范围，不覆盖原文件；开发验证或独立发现不改写为用户Bug反馈。

## 复用、审查与未取得条件

Educates固定 `d7e018f0cee382a595d2c9ecc6c938da099eb67e` 的两份教学模板移植为teaching模块和页面lesson。原件、LICENSE/NOTICE、SHA及适配说明在 `docs/third-party/educates/`；封闭测试拒绝未知检查、shell、args和非法冷却值。页面从已分析报告取教学检查，重采按钮仅设置B和聚焦本人采集命令。其他候选为仅参考/暂不采用，DSH为独立接缝，不混称整平台集成。

初审2P2+1P3为JDK缺版本命令退出证据仍通过、API缺SSL时丢身份/缺依赖分型、Java运行超时误归编译阶段。三项在2c5ade2真实修复，先失败/后通过保留；独立delta全部闭合、无新增阻塞，全文 `records/review/reuse-ai-independent-delta.md`（SHA256 `C89174C113B480FFA3CB02255BCAF1D443C4B43115B7BE393933AACED10BBB9A`）。独立核对80源/165证据零差、实跑115单测及三项修复；52网页/3UI为归档源SHA核对，Qwen为新报告复算，没有冒称复核者重跑全部浏览器或重新加载模型。初审原文保留，产品delta不自动覆盖PDF/Prompt/交付。

新版PDF10页、本机逐页视觉QA通过，摘要 `F5D02D598C6A800017D733B451D8E1DF3E63D1D380F96E3B0C437FE120441C49`；记录在 `records/reuse-ai/pdf/technical-pdf-build.json`及 `visual-qa.json`。8781的Python直启、13种工具ZIP/报告入口本机预烟测已通过；最终副本、ZIP/完整SHA/启动及独立材料/交付结论，以新回执和仓库外独立核对报告为准。旧版保护778课程/361Node/212R1/814legacy再次字节一致；用户课程库不复制，先前审计额外hash的偏差按原报告保留。

390px为本机Edge模拟；两个本机数据库只证明跨实例一致性；离线指导的外部官方链接仍需联网。原始报告含本机路径/设备身份，仅供本人本机审阅。正式MP4、三条完整Prompt链认证、评审远程访问、真实API/DSH任务、Linux来宾/集群、实体手机/第二设备和实际上传回执均未完成。最终产品版本及材料/交付核对以新回执为准。
