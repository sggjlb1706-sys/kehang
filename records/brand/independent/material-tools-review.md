# 课航材料与交付工具：独立只读预核

核对日期：2026-11-10。固定材料HEAD `7f60881d89d371f64b1e02c759c48bd079304b0f`，固定产品HEAD `1eadacb6eee7ab4fc013ca586b863e36d6ef8559`。审查者未参与改名、产品、材料或工具实现，仅新增本报告和本目录的新验证记录；不修改此前 `docs-check.md`、工具、产品、测试或已有材料。

完整读取 `tools/build_kehang_pdf.py`、`freeze_brand.py`、`deliver_kehang.py`、`kehang_smoke.py`、`.gitignore`，核对其调用的旧版 `check_product`、摘要辅助函数与换行规则。重新计算候选清单81项源文件SHA，全部匹配。工具当前文件SHA保存在 `material-tools-checks.json`。

## 实际执行结果

1. 从当前C仓库实际运行 `D:\ANACONDA\python.exe -B -m tools.kehang_smoke`，原始JSON保存在 `material-tools-smoke.json`。该脚本以Python模块启动课航服务，8782端口、新临时课程库、当前C仓库的既有官方runtime ZIP。首页正确包含课航完整名称，13类实际下载包逐一核task快照、runtime、CRC，Notebook含固定CSV；另POST明确缺失JDK目标的真实报告，分析保持未通过。共14项成功，`service_stopped=true`；只终止其保存的自有Popen进程，临时库在停止该进程后清理。
2. 用本审查进程自行创建8782监听，再运行相同烟测：以非零返回码1退出，没有成功JSON，已有监听仍可连接。随后仅关闭审查者持有的监听。原始结果 `material-tools-port-guard.json`。该构造负例证明已有端口不被抢占或结束，不代表另一设备验证。
3. 实际调用已读的 `brand_baseline_protection()`，只按前版既定清单读取文件，确认旧D版1783项SHA、旧HEAD `fc14fc752a83709df496b386e4ce950b01996afe`及旧ZIP SHA全部相符。旧清单本身SHA为 `41212ECC93DBC48C1CB5535AA34695E609003BCB15DD9A18D7AEE2CB83E22727`，旧ZIP SHA为 `4C929E654F99E36A768A5CBFF7332F487334CEF503381B32E800B7AB3E3208EB`；结果见 `material-tools-brand-baseline.json`。未遍历或读取旧目录新增的个人课程库，没有旧版写入。

上述均无安装、执行策略修改、外部模型请求、DSH启动或VM操作。本审查未执行实际新D版克隆/打包，也未将C仓库烟测写成新D交付已经通过。

## 固定代码核对

- 新D目录和ZIP为明确的新路径；存在任一个即拒绝覆盖。没有旧版删除、移动、reset或数据回填。`--execute`显式门槛、干净Git、已审产品闭合HEAD和81来源字节在实际交付前检查。
- `--no-local --no-hardlinks`完整克隆，精确单次safe.directory，不改全局Git配置。随后核新HEAD、全可达历史集合、fsck、完整tree与index，并重算每份工作树Git blob及C/D字节；不是只看提交数或抽查产品。
- 独立runtime ZIP先核固定SHA，再复制和校验。clone只带跟踪文件；个人课程库、env、private、解压运行时及下载测试ZIP不随复制。Notebook固定CSV为已跟踪演示资产，仍随课程工具提供。
- 旧课程版和Node/R1/历史只核此前保护名单；新增fc14品牌基线再核1783清单和旧ZIP，交付前后重复比较。历史已知private source-map仅按既定保护名单作摘要，不解析或复制；个人课程库排除。本次子审只实际运行前述fc14品牌基线检查，没有把仅读代码的其他历史保护写成已执行。
- 清单精确收录跟踪文件加runtime ZIP；自身、自身hash、Git内部、事后回执及仓库外报告排除。ZIP先于回执创建，包含该时刻完整仓库和Git历史；全部条目核CRC及内容SHA与实物比对，包含Git内部。事后回执不递归进入清单或ZIP，不造成摘要自引用。
- 新D副本将调用同一已读的 `kehang_smoke`，实际Python直启8782、13包及报告入口后，才记交付成功；当前预核仅证明C运行和代码路径。`.gitignore`新增课航回执名正确保持其事后生成、ignored状态。
- `freeze_brand`核当前9组品牌记录源SHA匹配、固定产品HEAD每份源字节，候选文件以独占创建保留原冻结。13任务摘要兼容由该浏览器记录及独立产品核对提供；旧52组不被当作当前品牌源SHA通过。
- 新PDF构建器先核产品HEAD和81来源、独立产品报告及闭合状态，写新课航PDF/新QA目录，不覆盖旧PDF或审查记录。页数限制1至30页；构建记录先标视觉待核，主执行/主审须另看全部页面。首封、页脚、元数据、路径/端口使用新名，原真实报告与当前9组品牌验证分别说明；其新PDF实物和文字P2修正闭合由主审负责。

## 结论与范围

固定工具代码、81来源字节、当前C版实际Python烟测、端口占用保护及旧fc14版1783清单/ZIP保护核对通过，未发现新增工具阻塞。可以进入新目录的实际交付。

新D副本/最终HEAD与完整历史、最终交付清单及自身摘要、ZIP全部实物内容/CRC、D副本实际启动、前后原件保护仍须在创建后独立核验。本报告不认证该尚未执行的步骤，也不代替主审对课航PDF、Prompt、视频与修正文档的核对，不提升真实API/DSH任务、来宾设备、本人MP4、三链、远程访问或正式提交的未取得状态。
