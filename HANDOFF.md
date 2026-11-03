# 正式重建版 R1 交接

第二轮送审：独立初审发现弯引号路径转义P2阻塞，原文已存records/review/independent-original.md。已仅修正路径字面值编码，并在包含U+2018—U+201F、ASCII单引号、$及反引号的真实工具目录重跑Edge下载采集，10组通过，记录records/browser/20261103T013607390941Z/results.json；旧162项候选清单保留，不覆盖。该结果待同一独立代理delta确认后才可记录无阻塞。

2026-11-03用户选择方案2。本轮在独立仓库实际重建，旧M4根目录和2026-11-01版本保持。计划交付目录D:\传智杯\versions\competition-rebuild-20261103；开发与完整运行记录在C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-rebuild-20261103。

## 本轮实际完成

从文档与空包首提交开始，实现统一规则/Python采集、教师固定快照/网页、固定本地Qwen任务、三模式新手流程、独立工具下载、同目标复检、脱敏导出与可选AI单次接口。旧业务模块未批量导入；既有产品设计、Prompt导出工具、官方运行时和模型的来源明确列于PROVENANCE与reuse.json。

## 验证依据

- 22项unittest：records/iteration-4/unit-tests-final.txt，1.115秒，OK，退出0；包含本机假AI协议测试，无真实收费模型请求。
- Node语法检查通过。
- 最终Edge：records/browser/20261103T012753583646Z/results.json，10组通过、浏览器错误0、http(s)外部请求0；3条采集命令退出0，1条工具runtime目标拒绝退出非0。Edge内部下载页资源单独计数，不算外网请求。
- Python：records/iteration-1与上述Edge下载工具A/B，D盘已装解释器两次通过，稳定复检；不存在路径是构造测试，非干净设备。
- Qwen：records/iteration-3，既有环境预检查后用新代码实际本地推理；输出2、正常EOS，7项通过。初检缺推理证据，复检补齐，outcome=verified，非修复。实际Python3.11.16/torch2.14.0+cu126/transformers4.57.1/RTX4060。
- 原型保护：tools.verify_legacy，814文件一致；550个阶段原件以SHA索引保留在D盘，不复制成Git开发史。旧三份217条可见对话导出已复制，原始会话保留本地。
- 所有失败记录保留。SQLite关闭、课程链接自动提交等实际问题及测试脚本问题分开说明，见docs/实现与证据说明.md。

## 启动

在交付目录执行Start-Web.ps1 -Python 'D:\ANACONDA\python.exe' -Port 8772，浏览器打开http://127.0.0.1:8772/；Ctrl+C退出。独立工具运行时ZIP在vendor目录显式启用，Git仅记录来源SHA，不提交二进制。模型原件仍在旧artifacts目录，没有下载或安装新模型/依赖。

## 审查与停止

实现与当前证据先冻结，独立只读代理审查后由主执行处理有依据的阻塞。此处是送审状态，最终结论写入REVIEW及records/review/final-status.json。未有独立结论前不声称终审通过。

R1本机核心路径与整套参赛作品分别记录。新代码真实无Python设备、第二设备/实体手机、新手本人安装、真实AI报错诊断未测；完整自然语言需求、Node.js和其他模型未实现。完整三链需逐项审核；正式5—8分钟1080p视频含2分钟AI过程、技术PDF<=30页、托管访问和官方资格尚未完成。旧失败不因本轮模拟被关闭。

不自动公开仓库、不发送邮件、不覆盖旧包、不进入下一阶段。用户可先试用R1，再决定剩余工作。
