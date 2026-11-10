# 正式基线：独立补充读取与复算

核对日期：2026-11-09（Asia/Shanghai）。核对者 `independent_auditor` 未参与本轮产品、测试、适配或修复实现。按主执行者要求，本次仅新建此报告，没有修改旧正式版、既有报告或本轮产品代码。本报告补充 `baseline-independent.md`，不能替代将来对新产品固定 HEAD/SHA 的独立审查。

## 固定对象和本次结论

正式基线为 `D:\传智杯\versions\competition-courses-20261108`；实际 HEAD 为 `e0aca9ca04f350c5db0e3d6f197307260eee6276`，分支 `codex/courses-20261108`，Git 工作树干净。独立重算全部交付清单、跟踪 blob、已审产品 blob 及旧版保护，未发现字节差异。现有真实报告与旧规则复算一致，旧 PDF 的实际内容及保存渲染图可以阅读。

本结论只覆盖旧正式基线及所列证据。没有运行新课程、启动内核/VM/服务、真实调用 API、安装依赖或确认新版本交付；不能据此宣告本轮新增功能通过。

## 完整读取范围

完整读取本轮入口提示词、四份范围要求及正式版 AGENTS。入口和较长范围文件的终端输出曾截断，已分段补读相应范围。另完整读取旧 `baseline-independent.md`、三个实测目录 README、旧 PDF 的构建记录和 visual-qa 原文，以及有关原件保护脚本。没有用旧审计结论替代以下独立字节检查。

三个实测目录逐文件完整读入并解码；其中全部 JSON 全量解析。包含任务快照、原始 A/B、分析/比较、汇总、命令/失败日志和证据脚本，而非仅读取 README。

| 目录 | 全部文件 | 字节 | JSON | TXT | README | Python 脚本 |
|---|---:|---:|---:|---:|---:|---:|
| records/courses/torch（含 float32-retest） | 35 | 55,468 | 25 | 8 | 1 | 1 |
| records/courses/vm | 25 | 53,123 | 14 | 9 | 1 | 1 |
| records/courses/preparation | 10 | 9,025 | 2 | 7 | 1 | 0 |
| 合计 | 70 | 117,616 | 41 | 24 | 3 | 2 |

首次模块缺失失败、PyTorch 验证脚本导入路径失败、int64 CUDA 失败、`vmrun -v` 无效参数完整帮助输出、CIM 拒绝访问及需求识别失败均已读取。历史日志中部分中文路径本来已有编码损失；没有改写原字节或把乱码解释为新的产品失败。补充检查首个 Python 输出流采用系统编码而出现终端显示乱码，后续明确 UTF-8 输出；JSON 解析和字节摘要不受该显示问题影响。

## 本次实际 Git/SHA 检查

在既有 `D:\ANACONDA\python.exe -B` 内存脚本中检查，Git 仅使用每次命令精确 `-c safe.directory=D:\传智杯\versions\competition-courses-20261108`，没有写全局配置或改变所有者：

1. `SHA256SUMS-delivery.json` 全文 98,690 字节、778 项逐一重算：缺失 0、SHA 差异 0。清单自身 SHA256 为 `93DC407BE48FFB4D2E8E79A852303B61AE4F578435DB3C06C81CF9BF900BAAC6`，与根 `.sha256` 原文一致。
2. `git ls-files -s -z` 枚举 777 个跟踪文件，独立按 `blob <长度>\0<内容>` 计算 Git blob SHA1，与索引全部一致。
3. `git ls-tree -r --name-only 3dddd3314d63496965c2f23ca3a01a43b20167d1 -- campuslab web Start-Web.ps1` 枚举 20 项产品；逐项 `git show <产品HEAD>:<路径>` 与正式版工作字节比较，差异 0。
4. `git rev-list --all` 为 31 个可达提交。R1 `eee876053eebfb7d82e2ad6a9b45272f0075b1fe`、Node `42d86482fa1540b35fcdda6bbdf15d888f6b8cd1` 和固定产品 `3dddd3314d63496965c2f23ca3a01a43b20167d1` 的 `merge-base --is-ancestor ... HEAD` 均成功。
5. `git fsck --full --no-reflogs` 实际退出 0，stdout/stderr 均空。
6. 按完整读取的保护脚本逻辑，在内存重算既有记录：Node 361 项无差异、无新增；R1 212 项无差异、无新增；旧原型/证据及副本 814 项无差异。没有运行这些脚本可能创建初始收据的分支。

本次没有重新核对旧 ZIP 的所有成员；其 CRC/摘要检查由已读前审计报告覆盖。没有把那部分旧检查写成本代理再次执行。

## 真实报告的独立规则复算

使用旧正式基线自身的 `campuslab.rules.task/compare`，只复算已保存报告，不调用采集器：

| 旧场景和报告 | 本次复算结果 | 范围 |
|---|---|---|
| float32-retest/cpu-A、cpu-B | 两次五项通过，stable-pass | 同一明确解释器，实际固定 CPU 数据来自旧原始报告 |
| float32-retest/gpu-A、gpu-B | A 的 GPU 运算 unknown；B 九项通过，verified | CPU 成功没有代替 GPU；表示补齐运行证据，不是环境修复 |
| vmware-actual-elevated-host、vmware-actual-retest-B | 两次仅 OS/软件 pass，其余六项 unknown；incomplete | 没有实例/来宾/课程完整成功 |
| 两份 preparation/hardware 原始报告 | validate_hardware 均接受完整结构 | 首份 CIM 未取得，第二份 API 回退；均不是课程通过证明 |

完整原始文件中的证据与上表一致：最初 int64 GPU 返回 `NotImplementedError: "addmm_cuda" not implemented for 'Long'`；float32 是另一个任务摘要。VMware 原帮助版本为 CLI 1.17.0、无参数帮助退出码 4294967295，`list` 原文是 `Total running VMs: 0`；不能称为 Workstation 版本或真实 Linux 来宾已通过。硬件总物理内存 16,849,256,448 字节不能写成空闲内存；显卡/显存名称不能代替框架运算。

## 旧 PDF 的实际内容和视觉读取

只读打开实际 `output/pdf/AI实验环境管家_课程能力版_技术文档.pdf`：9 页、363,180 字节，SHA256 为 `5C7BD452C51F79441C3AB9117AFA4DDDA52C7CCE1567A7E6F921D865E1E44501`。完整提取并逐页读取 6,608 字符；各页为 668、697、608、799、753、477、808、804、994 字符，完整产品 HEAD 与旧产品一致。

已实际查看保存的 `page-1.png` 至 `page-9.png` 全九页，没有看到裁断、重叠、缺字方块或页脚覆盖；这是读取旧保存渲染图，没有重新生成或渲染旧 PDF。构建记录、visual-qa 的 PDF 摘要/页数/大小一致；20 项产品源 SHA 重算无差异；两张原截图和两张局部图 SHA 一致，Pillow 在内存按记录矩形裁切后逐像素比较一致。

| 页 | 实际读到的内容及边界 |
|---|---|
| 1 | 旧版两条新纵切为 PyTorch、VM；Notebook/Java/数据库仍候选，完整旧产品 HEAD 清楚 |
| 2 | 固定任务、多组件身份、四状态、规则/AI 与本机标准库服务边界 |
| 3 | 旧真实桌面任务局部；硬件来源/时间与 4GiB 提醒不是保证 |
| 4 | CPU/GPU 分层和 int64→float32 真实探测程序修复，非用户反馈 |
| 5 | vmrun/实例/来宾分层，来宾未知，手动来宾采集不是远程证明 |
| 6 | 三模式、文件课程包、手机宽度模拟，摘要不是教师签名 |
| 7 | 真实旧提交和独立发现，未伪造具体用户 Bug 引导或三链 |
| 8 | 旧 69 测试/10+9+9 浏览器及审查适用范围；无真实 AI 诊断 |
| 9 | 旧 `.ps1` 启动示例与材料/设备/上传缺口，硬截止 11 月 18 日 15:00 |

旧 PDF 无本轮新功能内容，启动示例仍为 `.ps1`；它不能作为本轮的新技术文档或不改执行策略的 Python 直启证据。

## 读取边界的说明

正式基线当前 782 个非 Git 文件，778 清单之外有清单自身、清单 SHA 文本、生成回执和 `data/courses.sqlite`。课程数据库为 12,288 字节，仍在原位置。

本次补充脚本在计算全部非 Git 文件统计时，曾读取该 SQLite 文件的原始字节以计算摘要；未解析表、未复制或输出数据库内容。此操作超出了主执行者要求的仅枚举该库边界，已向主执行者如实说明并停止该范围。后续审计排除 `data/`、`private/` 和 `.env` 内容，仅检查它们的存在/元数据；本报告不写成从未读取过该数据库字节。没有读取 `.env` 或 private 内容，也未将数据库摘要加入新版本来源或默认数据。

## 下一步停止点

本次旧基线补读与复算完成。新产品仍在开发中；等待主执行者固定新产品 HEAD、候选清单与 SHA 后，再独立审查源码、测试、真实证据、页面状态与第三方实际采用范围。新产品改变后必须另行复核，不能把本报告自动扩成新交付通过。
