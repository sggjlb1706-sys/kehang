# 课航——计算机课程学习与实训助手

页面简称：**课航**。介绍：从课程准备到实训验证，帮助你把学习任务跑通。

2026-11-10，用户确认将“AI实验环境管家”更名为本名称。独立完整克隆自 `fc14fc752a83709df496b386e4ce950b01996afe`，分支 `codex/kehang-brand-20261110`；旧正式版、PDF、ZIP、课程库和审查原件保留。此轮只统一可见品牌与现行材料，课程规则、task_id、报告schema、campuslab命名空间及旧教师包兼容。

工作目录：`C:\Users\DELL\Documents\ChatGPT\传智杯\work\kehang-20261110`。新交付目录：`D:\传智杯\versions\kehang-20261110`；新ZIP：`D:\传智杯\submission\课航_课程学习与实训助手_20261110_待补本人视频.zip`。完整历史、SHA、当前验证和独立核对以 `records/review/kehang-delivery-receipt.json` 及本轮仓库外报告为准，不把上一版的固定SHA审查扩大到本次改名。

## 本轮交接
最终HEAD/产品HEAD、完整SHA、ZIP、当前PDF与独立全文以课航版新回执为准；旧基线fc14fc7及其独立报告仍只覆盖旧版。外部条件与正式提交未因此完成。

## 继承文档（历史原字节保留）

# 开源适配与AI / Agent课程版交接

状态核对日期：2026-11-10。下方旧课程版交接为继承历史；当前结果以本节、新验收文档、固定版本独立报告和最终新交付回执为准。

## 当前版本与启动

工作目录：`C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-reuse-ai-20261109`。分支：`codex/reuse-ai-courses-20261109`。基线为正式课程版 `e0aca9ca04f350c5db0e3d6f197307260eee6276`，完整继承真实历史。已审产品HEAD：`2c5ade24c512a6b15c7111f808192f480627c4fb`；冻结清单 `records/review/reuse-ai-final-candidate.json`，SHA256 `BD242703233272836DC99B6B819339EA30CC26CD9F404F7FB48E6FC0B6DFC615`。独立delta确认初审2P2+1P3全部闭合、无新增产品阻塞。原bbee5bc初审/旧候选和发现保留；后续材料/交付HEAD可更晚，执行相关字节仍须一致。

新交付目录为 `D:\传智杯\versions\competition-reuse-ai-20261109`；最终副本、HEAD、完整交付SHA、ZIP、启动及独立材料/交付结论，以 `records/review/reuse-ai-delivery-receipt.json`和仓库外独立核对报告为准。使用已有Python>=3.10直接启动，无需执行`.ps1`或修改执行策略：

```powershell
Set-Location -LiteralPath 'D:\传智杯\versions\competition-reuse-ai-20261109'
& 'D:\ANACONDA\python.exe' -B -m campuslab.web --port 8781 --database '.\data\reuse-ai-courses.sqlite' --runtime-zip '.\vendor\python-3.13.17-embed-amd64.zip'
```

打开 `http://127.0.0.1:8781/`；只停止本人此次启动的进程。端口占用时选择空闲端口，不停止旧服务。新独立课程库不复制用户原课程库。运行时ZIP为既有官方Python3.13.17嵌入包，SHA256 `9E35319BFFEDAB8B36AD44D8F377CB4F1733BCEC257A0B6D04D94F01486DDB38`，仅为采集工具运行时，不算课程环境。

## 已实现与实际证据

- Notebook：明确课程Python及已有kernel.json，真实临时内核中核对解释器、NumPy/Pandas及固定CSV/数组；真实A/B十项稳定通过，错内核、Pandas真实缺失等负例留档，仅清理本次创建的内核。
- Java与SQLite：Zulu21同源java/javac临时编译运行六项稳定通过；SQLite明确单文件、只读固定SELECT及前后SHA一致，五项稳定通过。SQLite不代替MySQL/PostgreSQL；JDK21不代表Hadoop服务端要求已满足。
- AI网页/API：DeepSeek本人练习记录与固定数字成果、自动登录证据分别呈现；API固定官方目的地/模型/请求协议，页面可编辑预览，终端安全输入密钥并确认本次发送。当前没有真实API请求；HTTP/错误分型与同意边界为协议/构造测试。
- DSH桌面/CLI：固定官方版本0.2.2-rc.1，桌面自带Electron不要求外部Node；CLI绑定所选Node>=24.9.0、明确包/入口。工作区、公开模型、权限、必要工具摘要和本机产物分别核对。所选Node满足引擎，但明确包/桌面候选路径缺失；无真实DSH运行、授权或Agent成功证据，不是全机未安装结论。
- Educates：固定上游d7e018f0cee382a595d2c9ecc6c938da099eb67e，两份教学动作模板字段及标题/正文/状态结构已适配至teaching模块和页面；固定报告checks取代上游脚本分派，三秒冷却的动作仅引导本人同目标重采。Apache-2.0、原作者、LICENSE/NOTICE和原件SHA随包保留。
- 共用流程：新场景接入自主/教师固定任务、下载工具、原始报告、分层指导、同组件有序复检、课程包/离线HTML和脱敏分享。原Python、Node、Qwen、PyTorch CPU/GPU和VM/Linux报告兼容保留。Hadoop、MCP等按来源路线及缺少组件列明。

修复后115项单测通过；重跑五套浏览器共52组及另3项构造UI回归通过，源码SHA匹配新产品候选。数据课程18组、AI/DSH6组与原Python10/Node9/课程9组分别留档，实际最终路径见新候选和 `docs/验收与证据-开源AI版.md`。390px是桌面模拟，两本机数据库不是第二设备。Qwen在正确model-venv重新真实离线输出2/EOS，`records/courses/model/20261110T003151Z/`中A缺推理、B七项通过，verified；最初错选PyTorch环境缺transformers保留，不能跨目标说成修复。原初审112项及旧网页记录保持原适用范围。

## 审查、材料及剩余条件

独立产品初审2P2+1P3为JDK退出证据、API缺SSL身份/分型、Java超时阶段归属。原全文 `records/review/reuse-ai-independent-product.md`，SHA256 `4A1CD5943D95CB1E01F511D66A93512E437D5A7D277FA5F84CDC7B8152B726D4`。2c5ade2真实修复及先失败/后通过保留；独立delta `records/review/reuse-ai-independent-delta.md`的SHA256 `C89174C113B480FFA3CB02255BCAF1D443C4B43115B7BE393933AACED10BBB9A`，三项全部闭合、无新增产品阻塞。独立核对80项源/165项证据零差，实际运行115单测；52网页是归档源SHA核对，复核者未重跑全部浏览器或重新加载Qwen。产品delta不覆盖最终材料/交付或实际上传。

新版技术文档 `output/pdf/AI实验环境管家_开源AI_Agent版_技术文档.pdf`共10页、本机逐页视觉QA通过，SHA256 `F5D02D598C6A800017D733B451D8E1DF3E63D1D380F96E3B0C437FE120441C49`；构建/QA见 `records/reuse-ai/pdf/`，旧九页PDF原字节保留。视频脚本目标6分40秒1080p、至少2分10秒真实AI协作，缺本人录屏/讲解和正式MP4。可见Prompt1导出17条（3用户/14助手、1条脱敏），索引 `records/reuse-ai/prompts-final/index.json`；工具/推理等未含，源前缀SHA见索引，三条完整链尚未认证。新ZIP为 `D:\传智杯\submission\开源AI_Agent课程版_20261109_待补本人视频.zip`；实际最终副本、ZIP/完整SHA/启动和独立材料/交付结论，以新回执及仓库外独立核对报告为准。

开发副本Python直启8781、13种下载工具ZIP/报告入口的本机预烟测已通过；这与最终新副本启动核对分别记证。原保护778课程/361Node/212R1/814legacy再次字节一致，用户原课程库不复制，先前独立审计额外hash的边界偏差按补充原文保留。

最少外部条件：本人合法账号/API单次发送同意；明确DSH安装及本人真实Agent授权和工具证据；教师固定Hadoop要求及已有Linux来宾/Java/SSH/集群；需要的第二设备/实体手机补证；本人正式视频、评审可访问仓库、百度网盘上传和提交回执。未取得时准确列缺，不要求本人从头完整重试全部开发流程。新包可能包含原始路径/设备证据，仅供本人本机审阅，公开前另核对隐私。

硬截止为2026-11-18 15:00北京时间；沿用本人上传网盘、核对链接/提取码/有效期、再提交并留回执的流程。没有发布、推送、代登录、收费API请求、系统/网络/执行策略修改或VM启动。可独立收尾工作仍由代理完成；交付完成后停止。

## 继承课程版交接（2026-11-08历史原文）

交付收尾核对日期：2026-11-09。11月8日的真实开发、审查、PDF和版本目录名称保留，不回填Git时间；实际复制时间以新交付回执为准。

新开发目录：`C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-courses-20261108`。新交付目录：`D:\传智杯\versions\competition-courses-20261108`。分支 `codex/courses-20261108`，完整继承正式Node版 `42d86482fa1540b35fcdda6bbdf15d888f6b8cd1` 历史。

固定产品HEAD：`3dddd3314d63496965c2f23ca3a01a43b20167d1`；后续仅材料/交接/交付工具提交，最终仓库HEAD见根Git及`records/review/courses-delivery-receipt.json`，产品文件须与该固定产品HEAD相同。旧版交接原文仍在原D盘版本及Git历史，不拿旧Node结论当本轮通过凭证。

## 本轮功能

- PyTorch CPU/GPU独立固定任务：显式课程Python、框架版本/导入、固定float32矩阵；GPU课程另核对CUDA构建、可用性、CUDA:0 UUID及主动实算。CPU成功不能替代GPU。
- VM/Linux固定任务：只读VirtualBox/VMware CLI、宿主条件、所选UUID/.vmx、实例状态与手动Linux来宾取证分层；没有实例/来宾时未知。不安装、不创建或启动VM，不改BIOS、系统或网络。
- 自然语言目标/报错进入、必要澄清、独立硬件预检、依据来源事实的准备路线、按四状态差异生成绑定目标的分层指导；固定Qwen从准备到离线推理的路线。
- 教师任务包导出/严格导入、独立实例同摘要、离线HTML手机指导；localhost码不当作跨设备分享，内容摘要不当作教师数字签名。
- 无报告文字报错预览、递归脱敏、可编辑消息/目的地/单次同意、AI失败保留规则、手动处理和同目标复检。无真实AI调用成功证据。
- 统一任务→准备/事实→差异/复检工作台，三种指导密度、桌面和390px；原始JSON可展开，模式不改变任务/判断。其他课程有来源目录及扩展验收，未冒称全部支持。

逐项表：`docs/能力对照-20261108.md`、`docs/课程目录与扩展路线.md`、`docs/验收矩阵.md`。

## 验证与真实结果

- `records/courses/unit-review-final.txt`：69项单测通过，包含原31项及新场景/共用流程/独立发现回归；Node语法检查通过。
- 最终Edge：`records/browser/20261108T104745025392Z/results.json` Python/模型网页10组；`20261108T104745480764Z-node/results.json` Node9组；`20261108T104746040882Z-courses/results.json` 新课程9组。三组均页面错误0、外部HTTP(S)请求0，产品源SHA匹配。额外`records/courses/review-ui/20261108T105547Z/results.json`三项构造UI回归通过且全部产品源SHA匹配；不是学生环境修复。先前104712记录的preparation哈希属于临时修复中版本，原件保留，不再当最终全源匹配记录。
- PyTorch真实CPU A/B五项稳定通过；GPU预检A尚无实际运算，B明确触发后九项通过、verified。本机Python3.11.16、torch2.14.0+cu126、CUDA12.6、RTX4060 Laptop，解释器和GPU UUID分别核对。原int64 CUDA失败保留，探测程序改float32形成新快照另采，不编造环境修复。
- VMware真实vmrun1.17.0可读取、当前运行实例0；Windows和软件通过，其余六项未知。同目标A/B incomplete。VirtualBox标准路径缺失。来宾采集/绑定已实现并有构造协议测试，没有真实Linux来宾完整实测。
- 硬件手动预检取得Windows版本、约16GiB物理内存、所选盘容量和RTX4060/驱动显存；每字段含来源和时间。首次CIM权限失败与只读回退/另次提权报告各自保留。预检不依赖torch/权重，不作为课程通过依据。
- Qwen `records/courses/model/20261108T103903Z/`：独立model-venv明确目标，A缺推理、B固定离线输出2/EOS、七项通过、verified。`20261108T103532Z/`首次错选PyTorch环境缺transformers失败原样保留；不同环境不能说成同目标修复。
- 教师包在同一电脑的两个独立本机服务/数据库传递成功，摘要与原始A/B一致；篡改包拒绝；离线HTML及390px无横向溢出。不是第二电脑/实体手机。
- 最终可读视口截图在`records/courses/ui-final/`；记录对应最终产品源码。旧截图与失败记录不覆盖。

## 审查与真实开发记录

初审：固定f8e9a13、654项清单SHA `E68878BA78FD37F062DAB263C15704C145604EBBF15A3564152B6D51D9C87A28`。独立代码发现4项P2和1项P3，全文`records/review/courses-independent-code.md`；独立证据审查未发现新增证据真实性阻塞，全文`courses-independent-evidence.md`。

五项修复：带空格GPU硬约束不再降级、CUDA构建值须有效版本、先递归脱敏再序列化、清理旧目标的修复建议、延迟教师响应门控。真实先失败测试和修复提交分别`12d2a1b`、`3dddd33`。delta对象为747项清单`courses-delta-candidate.json`，SHA `54EA4636E9823E30095C1748457FAB47E8F35027838CCD0F1F6723918989938C`；最终闭合结论以`courses-independent-delta.md`及REVIEW为准。

独立delta最终确认五项全部闭合、无新增阻塞。原文SHA256 `0250AA3293C36F4C87B6A88B732B9F9FA8454580C657E4F25EAF55E234A2D8A7`，69项单测独立通过、747候选重算一致。此后产品不再修改。

本轮真实Prompt索引为`docs/本轮真实Prompt与提交索引.md`。初始可见留档只有2条用户/7条助手；用户“继续完成”不是具体Bug反馈。并行模块17:59:35统一按完成模块入库，提交时间不是各模块首次写入时间。没有回填旧Git或虚构三条完整链。

## 启动、交付与材料

```powershell
Set-Location -LiteralPath 'D:\传智杯\versions\competition-courses-20261108'
& .\Start-Web.ps1 -Python 'D:\ANACONDA\python.exe' -Port 8772
```

打开 `http://127.0.0.1:8772/`，Ctrl+C停止。服务器需要已有Python>=3.10；检测包复用既有vendor嵌入runtime，工具Python不等于课程环境。模型权重/既有模型环境留原位置，不下载、不复制入仓库。

正式技术PDF位置`output/pdf/AI实验环境管家_课程能力版_技术文档.pdf`，生成与逐页核验见`records/courses/pdf/`。视频已提供6分40秒可录脚本、2分10秒真实AI协作镜头方案，尚缺本人素材和正式MP4。提交清单沿用本人上传百度网盘、核对链接/提取码/有效期的预指导流程。

PDF实际9页、363180字节，SHA256 `5C7BD452C51F79441C3AB9117AFA4DDDA52C7CCE1567A7E6F921D865E1E44501`；20项产品源逐字节匹配固定产品HEAD，9页Poppler图像及文本已核验。截图只作矩形局部展示并记录原图/裁切SHA，不修改事实。材料独立复核另归档。

独立材料复核已完成，文档顺序问题已关闭，无新增材料阻塞；全文`records/review/courses-materials-delta.md`，SHA256 `2F3DD17668562B821B12EA418668EF9897A05CB939998B7961E8EB7D4A1520E9`。独立重算PDF/20源码/原图及矩形裁切SHA，逐像素核对裁切、实际查看9页，结论不覆盖未取得的正式视频或实际上传。

新ZIP：`D:\传智杯\submission\课程能力版_20261108_待补本人视频.zip`，为本机审阅包，含完整真实Git历史，不含.env、private映射、课程库、重复解压运行时和测试下载ZIP；正式MP4缺失。以交付回执实际路径/SHA/CRC、复制启动烟测为准，无回执不视为已复制。

原件保护已核对：Node358交付项/361非Git项、原R1 212项、旧814项；交付复制后再次校验。完整Git单列不在非Git清单内。新清单排除自身、清单SHA与生成回执；没有修改旧正式版、原型或已提交材料。

## 未取得条件

真实Linux来宾/实例、第二电脑、实体手机、干净无Python设备、独立新手安装、真实AI诊断、其他GPU/多GPU/CPU专用框架与本地Qwen CPU推理未测；无合法可用接口和单次用户同意时不发送AI请求。Notebook/JDK/数据库/Hadoop等只研究与扩展路线。正式MP4、三条完整真实Prompt链、评审可访问远程仓库、本人上传及回执仍缺。没有公开/推送、发邮件、安装或改系统网络。

硬截止为2026-11-18 15:00北京时间，不等待官方答复。本轮功能/审查结论不认证赛事资格、整套材料或实际提交通过。完成交付后停止。
