# 课航品牌轮：独立产品与兼容性审查

核对日期：2026-11-10。主审 `/root/kehang_independent`，文字子审 `/root/kehang_independent/docs_check`，均未参与此次品牌变更实现。仅新增本报告和 `records/brand/independent/` 中的独立验证记录，没有修改产品、测试、工具、已有材料/证据、旧版或系统设置。

**产品与兼容性结论：在下列固定 HEAD/SHA 范围内未发现产品阻塞，可以继续当前品牌材料制作。** 当前初稿文字材料另发现一项 P2，原记录已归档，须在材料阶段修正后独立复核；本产品结论不提前覆盖新PDF、最终副本、清单、ZIP或正式提交。

## 固定对象

- 仓库：`C:\Users\DELL\Documents\ChatGPT\传智杯\work\kehang-20261110`。
- 分支：`codex/kehang-brand-20261110`；固定产品 HEAD：`1eadacb6eee7ab4fc013ca586b863e36d6ef8559`。
- 功能/交付基线：`fc14fc752a83709df496b386e4ce950b01996afe`，保留原正式名和全部历史。
- 冻结清单：`records/review/kehang-candidate.json`，SHA256 `C7E498D16997F5E6343383823C21A9527DB07BC7E4217AA33A7EFFF007A78E9B`，81项来源文件。
- 本轮正式名：课航——计算机课程学习与实训助手；页面简称：课航。

## 实际读取与窄改动核对

独立核清单原字节SHA、全部81项文件的实际SHA及对应固定HEAD Git blob，全部一致。完整阅读相对fc14fc7的产品diff和相关调用链：本次仅6个产品文件、17行增加/17行删除，均为可见名称、介绍、示例工具目录或下载文件名。未发生换行批量转换、规则/接口改写或固定程序更改。

六文件为 `web/index.html`、`web/app.js`、`campuslab/web.py`、`portable.py`、`teaching.py`、`guest_probe.py`。页面title/页眉/副标题/介绍及KEHANG标识一致；分享/教师包/离线指导文件名为Kehang系列；HTTP附件名仍ASCII，避免把中文直接写入Latin-1响应头。工具README、服务启动打印和必要技术提示使用新名。离线指导标题/页眉含新名并保留课程标题/任务摘要及转义。

内部 `campuslab` 模块命名空间、`campuslab-course`包kind、AI配置变量、工具runtime marker、DSH工作区kind、Notebook标记/固定内核名、Java `CampusLabFixed`类及源码摘要保持原样；不会因营销名称改变课程task_id。Educates适配模块中的历史作者/改动日期、Apache LICENSE/NOTICE、原模板、审查留档和历史品牌字节未被改写。

8份根文档新增当前说明后，其fc14fc7原正文均仍为逐字节完整后缀；独立脚本和文字子审分别核对，结果一致。现行顶部的名称、新工作/交付路径、8782端口及独立课程库路径一致；旧ROOT正文有明确历史标记。

## 独立实际执行与兼容证据

1. 独立运行 `D:\ANACONDA\python.exe -B -m unittest discover -s tests`：115项全部通过，原输出 `records/brand/independent/unit.txt`。未将主执行115项再加总成更多项。
2. 运行独立脚本 `records/brand/independent/check.py`，原结果 `checks.json`：81项SHA/固定blob一致；13类任务工厂输出与旧C正式源工厂逐对象完全相等，含全部摘要和要求，而非只比较任务名。
3. 对原Notebook、Java、SQLite、DeepSeek API、网页、DSH桌面及CLI共7组真实/明确未调用的旧A/B重新用当前rules比较，并导入各自旧教师包：3个数据/编程任务保持stable-pass；API、网页和DSH仍为incomplete；所有旧包kind/内容/摘要与当前导出相同。实际重算结果逐项在 `checks.json`，不冒称重新启动了这些课程环境或真实模型/Agent。
4. 使用自己创建的新临时库与loopback AppServer，实际请求13类工具下载及13类离线指导，共26个端点检查：工具ZIP CRC、快照、runtime与README新名均正确；所有工具附件名Kehang-tool.zip，指导附件Kehang-guide.html，指导正文含课航及相同task_id。只停止本次自有服务，临时库随后清理。
5. 核主执行品牌浏览器9组归档 `records/brand/browser/20261110T053806Z/results.json`：status=passed、全部最终产品源SHA匹配本候选；页面错误及外部HTTP(S)请求均0。该脚本覆盖13UI选择、下载工具实际产生缺失目标报告、旧JDK报告、旧kind教师包跨实例导入、离线HTML、分享文件名、同意边界、键盘与390px。此处是独立读取脚本及归档SHA核对，本审查没有把原52组当当前源码已重跑。
6. 独立目视该归档的桌面和390px首页PNG：名称/介绍正确，表单与文字可读，未见水平溢出或品牌遮挡。390px是桌面浏览器模拟，不声称实体手机或第二设备实测。

## 初稿材料发现（P2，待后续材料复核）

固定1eadacb的 `docs/课航视频录制脚本.md:7` 在当前新名下仍称旧产品2c5ade2已审、新版PDF10页且QA通过；此时课航PDF尚未生成。`docs/课航提交准备清单.md:12`、`:16` 的本版Git/验证行仍混用旧2c5和115+52结论，`:15`所谓本轮新Prompt索引仍指旧17条reuse-ai导出，无法佐证本次命名与“可以”的确认。顶部对旧版作一般声明不能使这些当前行准确。

影响是评审可能把旧产品/旧PDF和旧Prompt当作课航当前材料。应在具体行内明确旧功能基线，并把当前品牌HEAD/PDF QA/命名Prompt指向新记录/新回执；尚未生成时不能写完成。完整原发现与位置在 `records/brand/independent/docs-check.md`，SHA256 `2BC9155B0C9FA68D3340AB6A3E327A69A5CEEB13673A2C86D4AC2F66DF29E86E`，原文件保留。主执行者已反馈正在修正这两份纯材料文档并新增本轮Prompt索引；本报告不以该反馈代替独立复核，也不把当前未提交修正当成原候选已通过。

此项属于材料锚点与证据归属问题，不涉及上述6个产品文件的品牌显示或13类课程兼容；产品候选可以用于构建课航PDF，最终材料/交付仍须在修正后核定。

## 适用限制

没有安装软件/依赖、执行收费或其他外部模型请求、运行DSH、启动VM、读取私人课程库/凭据、改执行策略或发布/上传。独立运行的只有测试、已审本机HTTP工具/指导路线和明确的旧报告复算。真实API单次同意与调用、DSH本人Agent任务、Linux来宾/Hadoop集群、实体设备、正式视频、三条完整Prompt链认证和外部提交继续保持原缺口。

本产品审查仅覆盖固定产品HEAD和81来源SHA；后续新PDF及逐页QA、当前文本/Prompt、交付工具、新D完整历史/工作树/清单/ZIP/启动和旧版保护需要独立材料与最终实物核对。当前工作区可新增这些材料，但不能据此扩大本报告原结论。
