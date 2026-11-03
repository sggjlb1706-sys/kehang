# 真实演进与Prompt索引

Git从2026-11-03实际重建开始，不回填旧时间。用户实际选择“2”的原消息已在检查点保存。

```text
debaa462bbe224823a6bfdac9a68cbcc55c4d591	2026-11-03T09:08:28+08:00	chore: start formal rebuild with scope and preserved prototype evidence
55ac4abe34073ebb35d7bb08104f9e5c921d9d87	2026-11-03T09:10:09+08:00	feat: implement explicit-target Python evidence and deterministic retest
15f4c62442725ffb327a309b244dd61fb630df02	2026-11-03T09:12:45+08:00	feat: add immutable course publishing and shared local report workflow
ed0d20200e3ecf33a629debfa297d12964d033cc	2026-11-03T09:15:56+08:00	feat: verify fixed local Qwen task with offline inference evidence
06be9d324ba6e7003f070c80a22b77472edf2eb4	2026-11-03T09:29:00+08:00	feat: complete guided local workflow and preserve real rebuild verification
4330c70678e8951c1a5fc8d1b429b600f8afd54c	2026-11-03T09:37:58+08:00	fix: preserve smart quotes and metacharacters in manual PowerShell paths
```

四个主要实现提交对应Python契约、课程网页、固定本地模型和分层指导；路径修复另有真实提交。检查点01—05是同一会话的递增留档，不按导出文件数量宣称满足正式三链。

逐项来源：docs/prompts各目录index.json记录源前缀与导出SHA；旧三来源217条可见文本在docs/legacy/prompt-exports-20261101。tools.verify_prompts已验证8组前缀与每条可见消息原文摘要。原始会话保留在本人机器，其中两份由应用无损压缩。

源码差异以真实git show为准，整理索引与报告不是原始Prompt。全部导出均排除系统/开发者、工具与隐藏推理，不含图片本体；后续还需按三个核心功能审核正式完整链。
