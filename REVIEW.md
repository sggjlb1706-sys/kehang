# R1 Node.js/npm 扩展轮独立审查（2026-11-08）

最终状态：本轮独立初审无阻塞，1项P3工具README目标示例经实际提交49720ae修正后，独立delta确认闭合，无新增阻塞。本轮范围通过；以下原首轮审查仅为历史，不作为本轮通过凭证。整套赛事材料和官方资格仍未完成。

初审适用HEAD `cde0d4496c8ccda64933ae157073d406df9e6a27`；307项候选SHA清单 `node-candidate.json` 的SHA为 `1B5358D806A95D8FD408DBB197C8FD4EFE6E08710DF95B61B0C52D836FF21E3A`。独立初审全文 `records/review/node-independent-original.md`，SHA `F1D0B0F7E9BDE807A5FA6992E7DB2787B5E510AC6812C0061CCB624BB92F8242`。报告原文保留，不将非阻塞P3改写为不存在。

独立delta全文 `records/review/node-independent-delta.md`，SHA `AB1C5EDB9E7273BB40F4B033B784705C51BFD840F1E7A11D5465F0F174C7CAE1`，适用HEAD `ca948128c70638d4c858247e0b281f4977c2ceb1`。347项候选清单 `node-delta-candidate.json` 的SHA为 `372A911663D38C8F150CDB0C653755965BDA57306C8DF401FD04293981F59699`。独立31测试通过，内存工具ZIP核对Node示例正确、Python/模型README原字节一致；最新Node9组和原网页10组源码摘要匹配；原R1 212项和旧814项保护无差异。审查未自行重跑Edge/模型、实体设备或官网抓取，适用范围在原文明确。

此后仅更新结论、交接与交付清单，产品源码必须保持该delta候选摘要。最终Git HEAD及交付字节校验由新版本回执提供，不改写候选、旧报告或原交付。

本轮重点：目标Node与npm关联身份、完整事实与错误通过、固定快照、同任务/同目标/有序复检、跨场景错配拒绝、Python/模型/AI同意回归、隐私、原件保护及Prompt/赛事证据适用范围。产品实现、测试记录、官网留档及逐链对照表均纳入待审清单。独立全文另存records/review/node-independent-original.md；如有修复则另作真实提交并要求复核，不能覆盖原阻塞报告。

## 2026-11-03原首轮独立审查（历史原文）

最终状态：初审1项P2经修复后独立delta确认闭合，本轮R1本机核心路径无阻塞。独立代理未参与本轮实现，只读审查固定HEAD与records/review/candidate.json，范围包括真实Git演进、旧材料保护、采集身份、完整证据/未知、固定课程、同目标比较、界面状态、隐私与AI同意边界、本地推理及验证材料适用性。

初审报告正文已逐字保存在records/review/independent-original.md（不含代理记忆引用元数据）；主执行仅处理有依据的问题，并在此给出对应修复与剩余限制。无权代替赛事方认证资格。

初审原文已归档，适用06be9d324ba6e7003f070c80a22b77472edf2eb4。唯一阻塞为PowerShell将U+2018/2019/201A/201B解释为单引号，原编码仅保护ASCII单引号。

主执行改为双引号字面值，转义反引号、$、ASCII双引号及U+2018—U+201F。新增测试直接提取实际JS编码函数，交Windows PowerShell逐字符往返9组；另在含这些字符的实际工具目录完成下载包与原样生成命令A/B采集，见20261103T013607390941Z。修复不改变检测规则、模型推理或课程要求。


## 修复复核最终结论

独立delta适用代码HEAD 4330c70678e8951c1a5fc8d1b429b600f8afd54c，正文在records/review/independent-delta.md，SHA-256 861A5F93B668B34B20FA11D1FE570EB7DC480DDCB7EA85D7A7EAC45F10C453BA。初审报告正文SHA-256 714010C30309D3F2DFCB34A1444DECABFFD49E6E599106D2DEBD3334F852963A。本轮R1无阻塞，正式材料与官方资格不在通过范围。

收尾仅补充审查归档、矩阵、来源索引、状态和SHA，不改变产品代码；最终Git HEAD由交付回执记录。全部完整原始开发证据保留C盘工作副本，D盘交付省略重复解压运行时。

交付发现的15个初始Git对象换行归一化差异已用新增提交记录原始工作字节，未重写历史、修改产品工作字节或改变审查适用源码SHA。首次复制因字节状态不一致主动停止，恢复前验证整个既有交付副本仍与上一固定清单相同；实际差异记录见git-byte-roundtrip.json。
