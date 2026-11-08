# R1 Node.js/npm 扩展轮交接（2026-11-08）

当前状态：实现与本机验证已完成，独立审查待完成；本轮尚未记录通过。整套赛事作品与资格未通过。

新工作目录：`C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-r1-node-20261108`。计划交付目录：`D:\传智杯\versions\competition-r1-node-20261108`。分支：`codex/r1-node-20261108`；继承正式R1完整历史，原HEAD `eee876053eebfb7d82e2ad6a9b45272f0075b1fe`。最终HEAD在新版本交付回执记录，不将原交付回执当作本轮回执。

本轮新增Node.js/npm固定演示课程：自主与教师默认快照一致、显式选择Node、同目录npm CLI由所选Node执行、完整事实四状态、手动采集/修复和同任务同目标有序复检。三模式只改文字，Python/固定Qwen及AI同意机制保留。课程范围来自演示配置，不代表学校真实课程。

验证：原23项+Node7项共30单测通过；Node浏览器9组、Python/模型网页回归10组通过。Node24.21.0/npm11.19.0真实A/B四项通过、stable-pass；Python真实A/B四项通过。当前Qwen真实复测输出2/EOS、7项通过，verified，指定RTX4060环境。模型首次导入超时未知原件保留，后续计时5.14秒后另采才通过；根因未确认，不称已修复。AI仅本机协议模拟，无真实收费请求。

证据入口：`records/node/verification-summary.json`；Node最终 `records/browser/20261108T090411006997Z-node/results.json`；Python回归 `records/browser/20261108T090348975120Z/results.json`；当前模型 `records/node/model-regression-retry/comparison.json`。所有失败记录保留、构造报告与自动化范围各自标注。390px通过是浏览器模拟，不是实体手机。

来源保护：原R1交付清单205项一致，原目录212项非Git字节未改；旧材料814项保护一致；8组旧Prompt来源验证通过。复用原产品及历史范围见PROVENANCE和docs/reuse.json；本轮提交按实际时间产生，不回填旧历史。

赛事：官网2026-11-08当前正文仍同时列省赛11月18日与指导反馈预计2027年1月底的冲突，按较早2026-11-18准备；来源/抓取日期在 `docs/赛事要求核查-20261108.md`。`docs/Prompt链逐项核查.md`定位旧3候选、R1各模块及本轮Node真实提问/建议/实现/测试/提交；不能确认至少3条完整链，不虚构用户Bug反馈。旧无Git、赛事方未答复状态保留。

启动（交付后）：PowerShell进入新交付目录，运行 `& .\Start-Web.ps1 -Python 'D:\ANACONDA\python.exe' -Port 8772`，打开 `http://127.0.0.1:8772/`，Ctrl+C结束。服务器需已有Python>=3.10；检测包自带既有官方嵌入运行时（vendor），不需安装Web依赖。更换电脑必须改为其已有Python路径。Node及模型仍需本人已有课程环境。

剩余：正式5—8分钟1080p MP4（含至少2分钟AI过程）、<=30页技术PDF、评审可访问GitHub/Gitee、三条完整链及官方资格确认；新代码真实无Python设备、第二电脑/实体手机、新手独立安装、真实AI报错诊断及CPU推理未验证。未发布/推送/发邮件/安装/改系统网络。交付后停止，不自动推进。

## 2026-11-03原首轮交接（历史原文）

最终状态：独立初审及修复delta完成，原P2已关闭，本轮R1本机核心路径无阻塞。23项单元测试（0.856秒/OK）、复杂路径Edge10组通过，旧814项保护一致。正式参赛材料与外部验证仍未完成；详见docs/验收矩阵.md及records/review/final-status.json。

第二轮送审：独立初审发现弯引号路径转义P2阻塞，原文已存records/review/independent-original.md。已仅修正路径字面值编码，并在包含U+2018—U+201F、ASCII单引号、$及反引号的真实工具目录重跑Edge下载采集，10组通过，记录records/browser/20261103T013607390941Z/results.json；旧162项候选清单保留，不覆盖。同一独立代理delta确认P2闭合，无新增阻塞；正文见records/review/independent-delta.md。

2026-11-03用户选择方案2。本轮在独立仓库实际重建，旧M4根目录和2026-11-01版本保持。交付目标目录D:\传智杯\versions\competition-rebuild-20261103；开发与完整运行记录在C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-rebuild-20261103。

## 本轮实际完成

从文档与空包首提交开始，实现统一规则/Python采集、教师固定快照/网页、固定本地Qwen任务、三模式新手流程、独立工具下载、同目标复检、脱敏导出与可选AI单次接口。旧业务模块未批量导入；既有产品设计、Prompt导出工具、官方运行时和模型的来源明确列于PROVENANCE与reuse.json。

## 验证依据

- 第一轮送审22项unittest：records/iteration-4/unit-tests-final.txt，1.115秒，OK，退出0；包含本机假AI协议测试，无真实收费模型请求。
- Node语法检查通过。
- 第一轮送审Edge：records/browser/20261103T012753583646Z/results.json，10组通过、浏览器错误0、http(s)外部请求0；3条采集命令退出0，1条工具runtime目标拒绝退出非0。Edge内部下载页资源单独计数，不算外网请求。
- Python：records/iteration-1与上述Edge下载工具A/B，D盘已装解释器两次通过，稳定复检；不存在路径是构造测试，非干净设备。
- Qwen：records/iteration-3，既有环境预检查后用新代码实际本地推理；输出2、正常EOS，7项通过。初检缺推理证据，复检补齐，outcome=verified，非修复。实际Python3.11.16/torch2.14.0+cu126/transformers4.57.1/RTX4060。
- 原型保护：tools.verify_legacy，814文件一致；550个阶段原件以SHA索引保留在D盘，不复制成Git开发史。旧三份217条可见对话导出已复制，原始会话保留本地。
- 所有失败记录保留。SQLite关闭、课程链接自动提交等实际问题及测试脚本问题分开说明，见docs/实现与证据说明.md。

## 启动

在交付目录执行Start-Web.ps1 -Python 'D:\ANACONDA\python.exe' -Port 8772，浏览器打开http://127.0.0.1:8772/；Ctrl+C退出。独立工具运行时ZIP在vendor目录显式启用，Git仅记录来源SHA，不提交二进制。模型原件仍在旧artifacts目录，没有下载或安装新模型/依赖。

## 审查与停止

本轮先冻结162项候选接受独立整体初审；主执行修复唯一P2后，192项候选接受独立delta。已确认本轮无阻塞，原清单与两份报告正文保留。最终结论写入REVIEW及records/review/final-status.json。

R1本机核心路径与整套参赛作品分别记录。新代码真实无Python设备、第二设备/实体手机、新手本人安装、真实AI报错诊断未测；完整自然语言需求、Node.js和其他模型未实现。完整三链需逐项审核；正式5—8分钟1080p视频含2分钟AI过程、技术PDF<=30页、托管访问和官方资格尚未完成。旧失败不因本轮模拟被关闭。

不自动公开仓库、不发送邮件、不覆盖旧包、不进入下一阶段。用户可先试用R1，再决定剩余工作。

## 交付字节核对

首次D盘复制校验发现，最初引入.gitattributes之前的15个Git对象保存了归一化换行，而工作文件和D盘副本字节完全相同。已核对15项仅有换行表示差异，并强制重新入索引，保留原始字节后另作真实提交，不重写旧提交。产品11项源码工作字节及原型原件没有改动；记录见records/review/git-byte-roundtrip.json。交付中断发生在创建回执和入口前；恢复前逐项核对已复制文件未被改动。
