# 课航一键本机检测独立产品审查

审查时间：2026-11-12T04:40:39.121180+00:00。审查者未参与本轮实现；只读检查源仓库，在仓库外通过 git archive 创建固定候选副本运行验证，仅将报告及副本证据写入仓库外目录。

固定候选：`acd59a0723e4d52cd66a9715fc5e1bc15ada9947`。基线：`3b595f476c89a8390396cb3a78beb3fb27aca50d`。本结论只覆盖该候选，不能提前作为后续修正版或最终目录/ZIP的验收。

## 结论

范围内未发现 P0/P1 阻断，**0 阻断成立**；发现 **1 项 P2 非阻断界面问题**，不能表述为“零问题”。首页一键主路径、固定检查边界、真实结果回传与同目标复检在本次独立复跑通过。

### P2：从其他课程进入 Python 时仍默认露出整套手动工具

位置：`web/app.js:394-397`，直接原因是第397行只在非本机入口时展开，没有在进入本机入口时默认收起。

复现：新页面 → “我想选择其他课程” → Python 基础 → 确定任务 → “准备好了，去检测”。`local-start`、下载工具与 JSON 导入同时可见，`manual-collection.open=true`。此时没有运行检测。首页直接“检测本机 Python”路径会收起手动入口，因此不构成主要功能或执行安全阻断；次入口仍带来用户已反馈的选择负担。建议本机入口默认收起，保留本人主动展开；同时验证迟到配置不会覆盖本人手动选择。已通知主代理，固定候选中此项未修复。证据：`independent-evidence-acd59a0/manual-route-expanded.json` 和同名PNG。

## 实际复跑

| 项目 | 结果 | 证据 |
|---|---|---|
| Windows Python unittest | 153/153，通过，无跳过 | `independent-evidence-acd59a0/unit-tests.log` |
| `tools.verify_local_check` | 7/7组通过，页面错误0，外部请求0 | `independent-evidence-acd59a0/local-check/result.json` |
| `tools.verify_guided_ui` | 13/13组通过，页面错误0，外部请求0 | `independent-evidence-acd59a0/guided/result.json` |
| 未改短的15秒失联租约 | 15.202秒取消，0报告 | `independent-evidence-acd59a0/independent-additional.json` |
| 产品字节 | product.json的48/48项匹配固定归档 | `independent-product-result.json`的product_index |
| 包内官方运行时 | SHA256匹配DEPENDENCIES | `9E35319BFFEDAB8B36AD44D8F377CB4F1733BCEC257A0B6D04D94F01486DDB38` |

解释器：`D:\ANACONDA\python.exe`，版本 `3.13.9`。归档运行位置：`C:\Users\DELL\AppData\Local\Temp\kehang-independent-acd59a0-a33e5415cb3a4243bf6abe2336ca4be6\candidate`。新鲜A/B目标：`D:\ANACONDA\python.exe`；A时间 `2026-11-12T04:36:57.412766+00:00`，B时间 `2026-11-12T04:36:58.747157+00:00`；任务与目标一致，原A保留，`stable-pass`，四项规则均通过。原始A/B和比较保存在 `independent-evidence-acd59a0/local-check/real/`。

## 代码核查

- `local_check.py:71-101`：只有start接收任务与严格true同意后创建作业；仅Python基础，目标/命令/脚本/PID不接受网页传入。复检目标从服务旧作业解析，任务摘要一致，保留原始A。最多8候选、8历史、一个活动作业。
- `web.py:23-30,53-65,93-95,184-191`：只监听127.0.0.1，Host/Origin及实例随机令牌约束，查询与取消也须令牌；取消仅接受服务作业id。HTTP与单测中的错误来源、缺令牌、未知执行接口及额外PID均拒绝。
- `owned_process.py:29-56`及`local_runner.py:5-9`：创建私有Windows Job，配置关闭清理，包装器收到握手前不能启动目标；加入Job失败会结束包装器；取消/超时/finally关闭Job，仅处理本次自有进程。实际Windows单测清理自有子进程并保留另一测试进程。
- `local_check.py:116-125,135-188`：无心跳15秒取消；runner异常、报告缺失、目标冲突、无候选保持失败/未知。固定报告重新调用原analyze，复检调用原compare；删除原目标不会换成其他候选。
- `web/app.js:293-386`：任务身份和页面位置约束迟到响应，离开检测取消；多个环境各保留拥有它的作业id，不串复检；无候选不推定未安装或通过；AI入口仅触发现有脱敏预览，未勾同意不能发送。
- `git diff`基线至候选显示campuslab仅新增local_check/local_runner/owned_process及修改web；原rules/collect/probe、其他课程与AI判定未改。13类课程选择及原实训/教师流程已通过兼容脚本。

## 代码SHA256

| 文件 | SHA256 |
|---|---|
| `campuslab/local_check.py` | `69322D5740E1FD647D9D07A25955FD817DA36AE85FDBA4C5DFB22FE92677E544` |
| `campuslab/owned_process.py` | `39D6690C6232DB2CB6ABA4BC495C3FC97718AE9511950608AF00D58E50D69675` |
| `campuslab/local_runner.py` | `84C6CB4336EDD53497DF455DC8120336BB3882FB12626272DBFBE96F7F79A395` |
| `campuslab/web.py` | `271AFD2947F16D00AC22C20D12CB5C557F66BD1B9C3545133CE81F72D055DAF5` |
| `web/app.js` | `9C45705FE6550E9D774606E75334F87C41B0B22E457108C1026A238017FC8EB4` |
| `web/index.html` | `080901EC33D2043F1BD7B4C5210C40BD96119A7BF06F8B101BC07B170D98BC87` |
| `web/style.css` | `7493AB2FDB87831BCAD095099AC38EBFD7274A92FEDBD761215514F2A367721B` |
| `campuslab/rules.py` | `41F95844C39CB3BB74F5B222033AB5E46AB8E8B56877A521E0C22D53CE767603` |
| `campuslab/collect.py` | `A8F4567C39AD58F993C46546BAFEEA8E51CF51134820FA4C9679A9967090BF3A` |

全部48项文件SHA见 `independent-product-result.json`。

## 证据边界

新鲜A/B为本机代理操作，不能称为独立新手试用或外部设备验证。多环境、无候选、延迟与租约为构造场景；13组兼容脚本使用的旧实训A/B为归档再分析。本轮没有模型实际调用、安装、自动修复或外部部署，不能据此补齐这些产品或参赛证据。最终目录、ZIP及启动入口尚待交付实物核验；继承截图、旧PDF/视频保持其原版本语境。

## 追加失败复检与取消复核

在相同固定候选的外部副本增加3组构造UI检查，全部通过：Good环境复检发生OSError后，页面清除原报告/分析并禁用复检、AI和保存；切换到Old环境仍使用其原服务作业和目标复检，并保留版本不符合；取消Old的进行中复检后清除当前报告/选择，不将旧报告混作取消结果。证据：`independent-evidence-acd59a0/failed-recheck-cancel.json`。这些为构造场景，不是新增真实环境验收。
