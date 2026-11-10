# 独立材料与交付工具预核

核对日：2026-11-10。审查者 `/root/product_review/api_dsh_review` 未参与实现/修复。固定材料HEAD `1896da21f4e4934d1d12a289bd0aaaa6e09d1a48`，产品HEAD `2c5ade24c512a6b15c7111f808192f480627c4fb`。本报告为交付前的工具与C盘烟测预核，**不认证尚未创建的D盘副本、最终清单或ZIP**。

完整读取 `tools/deliver_reuse.py`、`reuse_smoke.py`、`freeze_reuse.py`、`build_reuse_pdf.py`、`.gitignore`、`.gitattributes`，并核对其调用的产品一致性/摘要辅助函数。重新核对冻结清单中80项产品、测试与第三方来源文件的SHA，全部一致。未修改工具、产品、测试、材料或旧记录。

## 实际执行

运行 `D:\ANACONDA\python.exe -B -m tools.reuse_smoke`，原始JSON见 `reuse-ai-materials-tools-smoke.json`。新Python CLI以8781端口启动、使用新临时课程库及当前C目录的既有官方runtime ZIP；13类任务包逐项下载，任务快照、运行时与CRC均通过，Notebook含固定CSV；实际POST报告分析入口保留缺失JDK目标而不假通过。脚本终止了其保存Popen句柄对应的自有服务，结果 `service_stopped=true`，无执行策略修改、API调用或DSH启动。临时课程库在停止自有服务后清理。

另做构造端口占用负例：审查进程自行监听8781，再运行烟测。烟测以WinError10048非零退出，无成功JSON，原监听仍开放，未终止任何其他服务；审查进程随后仅关闭自己持有的监听。结果见 `reuse-ai-materials-tools-port-guard.json`。

## 代码核对结果

- 交付目录和ZIP使用明确的新路径；任何一个已存在即拒绝覆盖。脚本不删除、移动或重置旧版。旧课程版只核其既定清单/HEAD及旧ZIP；Node、R1、旧原型只重核此前已保护的文件，不遍历新增私人数据。历史保护元数据中的已知private source-map仅参与摘要保护，不解析、不复制；新个人课程库不在这些既定清单中。本子审未读取这些源映射文件或任何个人课程库的内容。
- 交付前要求Git干净、基线为祖先、当前80项冻结来源与审查闭合HEAD一致。独立本地clone使用`--no-local --no-hardlinks`和单命令精确safe.directory；核HEAD、分支、全可达提交集合、fsck、tree与index逐项一致，再对每份工作树文件核原件字节及Git blob。
- 运行时只复制本轮既有ZIP，先核固定SHA再核副本。课程库、env、private、提取运行时和测试ZIP不会由clone复制。`.gitattributes`的`* -text`使原始来源不再被换行转换；交付脚本仍逐blob/原件校验，转换错误会阻断。
- 清单包含跟踪文件和独立runtime ZIP。自身、清单自身hash、`.git`内部及事后回执被排除并明示。ZIP在回执产生前创建，包含该时刻完整仓库和Git历史；逐项CRC和全部归档文件的SHA与实物比对，非只核产品子集。回执之后才写源/副本，不递归进入ZIP或清单，避免摘要自引用。
- 烟测按Popen句柄只关闭本次创建服务；8781已占用则在启动前拒绝。交付工具会在新D副本中重复调用该烟测并核真结果，再复核旧版保护。此逻辑已读，D盘实际执行仍须最后核对。
- PDF构建先核产品HEAD/80来源、初审报告和独立delta闭合状态；新文件、PNG和构建记录写新路径，不覆盖历史课程PDF。页数有1至30页限制，生成状态明确为待逐页检查；不能只凭构建完成当成视觉通过。PDF/文本/Prompt/视频的实物一致性由主审另核。

## 结论

在本次固定工具与C盘实际烟测范围内，未发现新增阻塞。可进入新目录的实际交付；最终交付HEAD、完整SHA清单、ZIP原件/CRC/内容、Git状态与历史、旧版保护以及D副本实际启动仍需独立核验。本报告不将该预核扩为最终交付或正式赛事提交成功。
