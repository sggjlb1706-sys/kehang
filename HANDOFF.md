# 当前入口：返回选课修复 · 2026-11-17

分支 `codex/kehang-return-selection-20261117`，实际仓库仍为本目录。只修课程结果页完成按钮到选课界面的路由与相应文字，连续实训返回行为保留。本人本次一键检测正常通过，A/B是此前多次验证；不能写成本次本人新做A/B。源反馈与回归见 docs/返回选课修复.md；新候选/包/独立报告及当前入口以工作区 `交付/课航返回选课修复-20261117-01` 为准。以下均为历史交付。

# 当前交接：功能冻结收尾 · 2026-11-16

实际仓库 `D:/传智杯/开发工作区/work/kehang-ai-connect-20261115`，分支 `codex/kehang-ai-connect-20261115`。冻结基线1785ab4，启动修复7d4354e。当前能力是8课程、6指南、连续实训、教师工作台和逐轮预览同意聊天；真实DeepSeek两轮与本人正常体验已在11月15日归档，不能再列为未接通。README 为当前启动入口；最终候选及独立复核以工作区 `交付/课航提交收尾-20261116-01` 为准。当前未发布或正式提交。以下历史端口、目录、数量和未接入结论只对其当时版本有效。

# 第四轮当前入口 · 2026-11-15

独立目录 D:\传智杯\开发工作区\work\kehang-round4-20261115，分支 codex/kehang-round4-20261115，固定产品 ed215e43471c880f99d4f4cd5dd707cbdf6bd173。服务 http://127.0.0.1:8776/；重启在本目录运行 pwsh -NoProfile -File .\Start-Web.ps1。第三轮 e1feb89 保留，未在旧副本开发。

5 条原工具课程迁入 6 份拓展指南，课程保留 8 项。指南无检测/报告/固定练习/复检前置；聊天面板保留逐轮预览授权。教程核查、模拟回复和真实 Python A/B 分别记录。183 单测与11组主控专项通过；独立固定版本审查详见 REVIEW.md。本轮没有真实工具安装、模型调用、Agent执行或正式提交，尚待本人体验与配色反馈。以下为历史交接。

# 第三轮当前入口 · 2026-11-14

当前独立体验版D:\传智杯\开发工作区\work\kehang-round3-20261114，codex/kehang-round3-20261114，固定产品65de1c4。入口http://127.0.0.1:8775/，重启用pwsh -NoProfile -File .\Start-Web.ps1 -Port 8775。以TASK/PLAN最上方第三轮与docs/第三轮验收.md为准，第二轮副本保留。

已完成全页面共享视觉、极简欢迎比例及DSH/API指导状态适配。180单测与针对性回归通过，独立审查跨课声明P2已修复。真实AI仍未配置；未安装/配置模型、未执行Agent/GPU/API发送。本人尚未体验，不代写满意/修后验收/Prompt链。完成本轮后停止，后文为历史交接。

# 第二轮当前入口 · 2026-11-14

本独立体验版目录D:\传智杯\开发工作区\work\kehang-round2-20261114，分支codex/kehang-round2-20261114，固定产品ed34a09。以TASK.md、PLAN.md、PRODUCT.md、DESIGN.md最上方第二轮约定及docs/第二轮验收.md为准；后文为继承旧交接。原仓库a7aba975保持不变。

体验服务http://127.0.0.1:8774/；重启用pwsh -NoProfile -File .\Start-Web.ps1 -Port 8774。首页→开始→选课→配置/检测→问AI。实际AI仍未配置。11类真实网页A/B，6类通过5类保留缺口；DSH CLI缺包，网页课不适用。GPU/推理/API/Agent/Guest未实际运行，不得把受控用例当本人授权实跑。本人尚未反馈本轮体验，不能替写满意或三条Prompt链完成。

# 课程首页与连续对话交接 · 2026-11-14

当前实际开发目录：`D:\传智杯\开发工作区\work\kehang-win11-guides-20261113`，分支`codex/kehang-course-chat-20261114`。产品固定提交0e1be49694cb7e49b10836f95d0addd46ecee423已通过独立只读复核。首页直接选择13课程，Python快捷检测位于本课程准备页并保留教师要求，AI侧栏支持当前步骤与报告的多轮追问，结果工具收拢。入口README，验收docs/课程首页与连续对话验收.md，独立结论REVIEW.md。

本机预览`http://127.0.0.1:8787/`，隐藏服务进程35876，日志和课程库在本仓库data/course-chat-preview.*。当前没有配置AI模型；聊天协议仅以本地夹具验证，接入真实模型需在启动终端设置`.env.example`所列变量后重启。没有调用收费模型、发布公网或重做旧ZIP。旧D盘versions/submission与交付物保留原版本；C盘入口仍为Junction。以下为历史交接。

# Windows 11 全课程图示版交接

当前work/kehang-win11-guides-20261113，分支codex/kehang-win11-guides-20261113，从正式11e52b4完整继承。13类课程、实训及报告图示已接入，纯展示引导，不改变检测或AI范围。验收records/win11-guides/acceptance.json；固定独立结论REVIEW.md，新目录/两ZIP以仓库外“交付/课航Windows11图示-20261113”回执为准。旧预览保留，新预览由新交付说明给出。

以下为历史交接。

# 报告位置图示版交接

当前目录work/kehang-report-guide-20261112，分支codex/kehang-report-guide-20261112，完整承接f398ad5。本轮仅针对报告查找/选择图示和Node路径误选提示，Python一键与其他课程手动方式不变。验收records/report-guide/acceptance.json，当前独立结论REVIEW.md，新实物以仓库外“交付/课航报告图示-20261112”回执为准。旧服务保留，新网页地址以新交付说明为准。

以下为历史交接。

# 课航一键本机检测版交接

当前开发目录work/kehang-local-check-20261112，分支codex/kehang-local-check-20261112，从正式路径引导版3b595f47完整继承。首页一键自动发现/检查Python基础环境，结果直接返回，支持独立环境选择与同目标复检；不自动发AI请求。入口README，验收records/local-check/acceptance.json，独立审查与最终新目录/包以本版REVIEW和仓库外“交付/课航本机检测-20261112”回执为准。旧版本服务不会热更新，需打开新交付预览或重启新目录服务。

以下为继承的历史版本交接，不代替当前验收。

当前目录work/kehang-path-help-20261111，分支codex/kehang-path-help-20261111，从ffdeca59完整继承。新包的Start-Collect.cmd启动路径选择向导；旧解压目录不自动更新，需从新网页重新下载并解压到新目录。验收入口records/path-help/acceptance.json，新审查与交付以当前REVIEW及仓库外“交付/课航路径引导-20261111”回执为准。以下为继承的上一轮说明，只对其标明版本有效。

当前开发目录为work/kehang-guided-20261111，分支codex/kehang-guided-20261111，继承实训版451d7b9全部历史。首页、单项课程四步、连续实训四步和独立教师工作台已实现；新入口以本版README为准。浏览器验收入口records/guided/acceptance.json；产品候选提交及只读审查以本版REVIEW和新交付回执为准。

下一步按钮保持可见；新课程与换目标回到初检A；初检后进入复检导入单份B保留A。教师无需学生报告即可发布/导出单项课程。原API/DSH授权、外部设备和赛事提交缺口未被本轮UI变更自动补齐。继承PDF/MP4对应上一版界面，本轮仅更新可运行UI、截图与文档。

以下为继承实训能力的适用说明，不代替本轮UI验收。

启动与代表任务见 README.md。当前完整包包含 Notebook 与 SQLite 实训资料、可重算的限定成果、包内 Python/Notebook 主动入口和一次选择 A/B。课堂实测证据在 records/practice/lab-run，浏览器完成物在 records/practice/completion-local.json。真实模板结果为总分 42、A 组 2 行 30 分、B 组 1 行 12 分。

DSH 桌面版以 PE 与相邻应用包公开元数据分别核对，软件层本机通过，实际模型、工具授权和 Agent 产物仍待本人操作。两独立实例均在同一台电脑。旧功能实测原件的适用版本见各自记录。

固定产品身份和文件见 records/practice/product.json；独立审查见 REVIEW.md。PDF、视频与复现入口列于 README。最终目录、ZIP、启动核验及摘要以仓库外交付回执为准。旧版交接原文见 git show a7dac52:HANDOFF.md。
