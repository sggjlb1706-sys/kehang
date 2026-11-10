# 课航：独立材料与交付工具预核

核对日期：2026-11-10。主核对者 `/root/kehang_independent`，工具子核对者 `/root/kehang_independent/docs_check`，均未参与本次改名实现、文字/PDF制作或交付工具编写。仅新增本报告及 `records/brand/independent/` 中的独立验证记录，没有修改产品、测试、既有材料、旧报告、回执或D盘版本。

**结论：本次固定材料与交付工具预核通过，原初稿材料P2已闭合，未发现新增阻塞，可以进入新D目录的实际交付。** 新D副本、完整交付SHA、ZIP实物和D副本启动尚须创建后独立核对，本预核不提前认证。

## 固定输入与一致性

- 材料HEAD：`7f60881d89d371f64b1e02c759c48bd079304b0f`。
- 产品HEAD：`1eadacb6eee7ab4fc013ca586b863e36d6ef8559`；81项冻结来源SHA与产品原候选完全相同。
- 产品清单：`records/review/kehang-candidate.json`，SHA256 `C7E498D16997F5E6343383823C21A9527DB07BC7E4217AA33A7EFFF007A78E9B`。
- 新技术PDF：`output/pdf/课航_技术文档.pdf`，10页，SHA256 `32B3718005CC2AD215EB556B855C9F60E6737681801B81BE28D6062230693451`。
- 产品独立报告：`kehang-independent-product.md`，SHA256 `6800235A0113F51F49445E88A13584F44CAFC9E6BDDDD8FCDE9C6E329980B491`。其中产品兼容通过与初稿材料P2的不同范围继续保留。

独立核新PDF实物与材料HEAD对应Git blob、构建记录及81项源摘要；12份现行文本（根8份、命名/视频/提交/新Prompt索引）当前字节均与该固定材料HEAD一致。原历史正文、原版权与旧功能证据没有被替换成新名称或新时间线。

## 原材料P2的独立复核闭合

原发现只覆盖 `1eadacb` 初稿：新视频/提交清单在当前语境中混用旧2c5ade2产品、旧PDF QA及旧17条Prompt索引。原子报告 `records/brand/independent/docs-check.md` 和主产品报告保持原件，不回改原结论。

本次逐行复核固定7f60881的修正：

1. 新视频脚本首段已重写，明确当前正式名、课航README目录/8782、当前PDF与HEAD以新回执固定；下方原功能开发/三项修复只是可回顾的真实历史，不冒充本轮改名的新Bug或新PDF已验收。
2. 新提交清单Git行明确fc14fc7及36个继承提交、当前HEAD由课航回执固定；验证行明确本轮115单测与9组品牌/兼容、13任务及旧包/报告相同，原52组属于原功能基线。技术PDF行指向课航新文件、`records/brand/pdf`和新回执。
3. 新Prompt行及 `docs/课航Prompt与验证索引.md` 已转向 `records/brand/prompts/index.json`，明确32条可见消息、命名讨论/“可以”/“继续”的实际来源行；旧17条导出保留为历史，不承担本次命名确认的证明。

上述原P2已闭合；没有借助一般性顶部免责声明继续保留错误的当前行。正式视频、真实API/DSH任务、来宾/设备、三条完整链和正式提交仍明确缺少，不因改名升为完成。

## 新PDF全文与逐页视觉核验

主核对者完整读取10页正文与元数据，逐张查看全部10张最终PNG。封面/页脚为课航，副标题为计算机课程学习与实训助手，产品HEAD为1eadacb，分支及完整克隆基线fc14fc7对应。字体、表格、图示与页码清楚，未见裁切、重叠、缺字或黑块。

使用现有Poppler独立重新渲染10页，输出在 `records/brand/independent/pdf/`；逐页PNG SHA与主执行最终10PNG完全相同。另以PyMuPDF检查全部文字span边界，无页外文字，提取文本无替代字符；这与目视互补，不用文本提取替代视觉核验。

第3/4页明确Notebook/JDK/SQLite数据为原功能版真实报告，本轮保持兼容；第8页明确当前115项与9组品牌/兼容检查，原52组和3项构造回归属于旧固定功能版，不声称当前81源已重跑原52组。第9页用课航新版首页桌面/390px图，图注仍为桌面模拟。第10页为新 `D:\传智杯\versions\kehang-20261110`、8782、新课程库和正确runtime ZIP；Python反引号续行可复制，不要求运行ps1或修改策略。

功能正文保持当前实际范围：环境检测只是课程流程的一环；AI仍解释既有证据、网页本人记录不认证登录；DSH具体版本与桌面/CLI依赖分开，尚无真实任务。Educates模板实际适配及Apache原作者/LICENSE/NOTICE、DSH审查留档和其他候选采用方式均未因改名抹去或夸大。

## 当前命名Prompt的真实性

独立从本轮指定原始会话只读取已冻结的完整行前缀8,946,342字节，重算SHA256为 `176FF908110BACBF7D467D742D0F8958A1CBCA0C022783E389FA116CF674EFF2`。用已读导出函数重新提取，与现导出32条消息逐对象全等，包括原文摘要、来源行号、时间、脱敏和遗漏信息；JSON及可读MD实物SHA均与index相符。

实际计数：6用户、26助手，共32条可见，2条脱敏。用户源行1402为“产品名字我觉得应该改改了，AI实验环境管家有点太局限了”，1463为“可以”，1538为“继续”；原文保留末尾换行，索引的引用以可读文字呈现，未改写为具体代码Bug反馈。独立检查脚本首次对引用语义漏考虑末尾LF而触发断言，核明源/导出全对象已严格相同后，仅对三个语义引用使用strip；原消息严格全等验证未放宽，也未修改任何导出内容。

该留档是当前会话可见文字前缀，不包含系统/开发者、工具或隐藏推理，不因增加文件或消息条数认证三条完整核心链。新视频仍是6分40秒/1080p、其中2分10秒真实AI协作的录制脚本，没有替代本人录屏/讲解或正式MP4。

## 新交付工具与C盘实跑

工具子核对完整读取 `tools/build_kehang_pdf.py`、`freeze_brand.py`、`deliver_kehang.py`、`kehang_smoke.py`、`.gitignore` 及调用的旧辅助函数，并与已审旧工具对照。完整子报告 `records/brand/independent/material-tools-review.md`，SHA256 `371AAF4F21BA2AB32CF109B8F3AD24511FDEB1096707F2EB5CE77827C39DF51F`。

- 新目录/ZIP明确指定，任一个已存在就拒绝覆盖；不删除或重置原版本。新增上一fc14fc7正式D版1783项清单及旧ZIP保护；子核对实际执行该保护函数，清单SHA `41212ECC93DBC48C1CB5535AA34695E609003BCB15DD9A18D7AEE2CB83E22727`、ZIP SHA `4C929E654F99E36A768A5CBFF7332F487334CEF503381B32E800B7AB3E3208EB`及已列1783项均匹配。未读取新增个人课程库。
- 交付先要求当前Git干净、基线为祖先、81源与产品闭合HEAD一致；完整clone核HEAD/branch/全部可达历史/fsck、tree/index和每份工作树blob及C/D内容；运行时只复制已有固定SHA ZIP。
- 清单包含跟踪文件和runtime，明确排除自身/自身hash、Git内部及事后回执；ZIP在回执前生成，包含全Git历史，全部条目CRC及内容SHA与D实物逐项核对。新回执不回塞ZIP/清单，避免自引用。所有旧版本保护函数仍在交付前后检查，当前预核不代替将来的实际D执行。
- 子核对从C实际运行 `D:\ANACONDA\python.exe -B -m tools.kehang_smoke`：以8782端口、新临时课程库和新repo runtime启动Python CLI，13任务工具下载/快照/runtime/CRC及POST缺失JDK报告共14项通过。只停止自己持有Popen句柄的服务；新临时库随后清理；无执行策略修改、API/DSH运行。
- 子核对另自行监听8782后运行烟测：非零退出、无成功JSON、原监听仍开；最后仅关闭审查者自己的listener。端口冲突未停止任何既有服务。

## 原始验证与边界

`materials-check.py` / `materials-checks.json` 记录主核对的固定HEAD、81源、PDF/10页重新渲染、span边界和32条Prompt重新提取。`material-tools-smoke.json`、`material-tools-port-guard.json`、`material-tools-checks.json`、`material-tools-brand-baseline.json`及子报告记录实际工具执行与旧fc14实物保护。均为本轮新增审查记录，旧发现/旧证据保持原件。

本预核没有修改D、安装软件/依赖、调用外部模型或DSH、启动VM、读取凭据/个人库、改执行策略或发布上传。尚未生成的课航D副本及ZIP不能由本结论推为已交付；正式创建后还须独立核全部文件/历史、1783旧版保护、完整新清单/ZIP内容CRC、runtime和新D Python启动。完成这些实物核对及回执附入后，才闭合本轮本机交付，外部条件和本人提交仍另列。
