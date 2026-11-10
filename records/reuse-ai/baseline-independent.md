# 复用与AI课程轮：正式基线独立只读核对

核对日期：2026-11-09（Asia/Shanghai）。核对者为本轮 `baseline_audit` 代理，未参与新版本产品、测试、适配或修复实现。本报告只核对旧正式基线及对应证据；不认证尚未完成的新产品。按主执行者后续明确授权，仅在新工作区新建本报告，没有修改旧版文件、Git配置、系统策略或原始证据。

## 固定对象

- 正式基线：`D:\传智杯\versions\competition-courses-20261108`。
- 对照源仓库：`C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-courses-20261108`。
- 正式交付HEAD：`e0aca9ca04f350c5db0e3d6f197307260eee6276`。
- 分支：`codex/courses-20261108`。
- 独立审查固定产品HEAD：`3dddd3314d63496965c2f23ca3a01a43b20167d1`。
- 本报告存放的新工作区：`C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-reuse-ai-20261109`；实际分支 `codex/reuse-ai-courses-20261109`。新工作区clone由主执行者完成，本代理不把它作为自己执行的操作。

## 完整读取范围与统计

完整读取本轮《后续工作提示词_开源二次开发与课程AI_Agent补全版_20261109.md》及基线AGENTS.md。以下目录逐文件读取全部内容，JSON全量解析，包含首次失败、原始报告、分析、任务快照、命令输出及证据脚本；不是只读README或汇总。

| 目录/类别 | 文件数 | 字节数 | 细分 |
|---|---:|---:|---|
| records/courses/torch（含float32-retest） | 35 | 55,468 | 25 JSON、8 TXT、1 README、1 Python证据脚本 |
| records/courses/vm | 25 | 53,123 | 14 JSON、9 TXT、1 README、1 Python证据脚本 |
| records/courses/preparation | 10 | 9,025 | 2 JSON、7 TXT、1 README |
| 指定独立审查/回执及仓库外报告 | 8 | 56,571 | 见下列清单，回执中的全文也已读取 |
| 根交付SHA清单 | 1 | 98,690 | 778项全部解析并重算 |
| technical-pdf-build.json | 1 | 5,375 | 全文读取并核对实际PDF/20产品源/截图 |
| visual-qa.json | 1 | 2,272 | 全文读取；历史视觉结论与本次行为分开 |

另完整读取根清单 `.json.sha256`、`records/courses/final-status.json`，以及实际9页技术PDF的全部6,608字符提取文本。PDF只做只读检查，未运行创建/编辑标记，未重生成或重渲染旧PDF。

八项指定审查/回执原文为：

1. `records/review/courses-delivery-receipt.json`（含独立交付核对摘要与嵌入全文）。
2. `records/review/courses-independent-code.md`。
3. `records/review/courses-independent-evidence.md`。
4. `records/review/courses-independent-delta.md`。
5. `records/review/courses-independent-delta-evidence-note.md`。
6. `records/review/courses-materials-delta.md`。
7. `records/review/courses-delivery-preflight.md`。
8. 仓库外 `C:\Users\DELL\Documents\ChatGPT\传智杯\交付\课程能力版-20261109\独立交付核对.md`。

完整阅读有关工具：`tools/deliver_courses.py`、`delivery_smoke.py`、`course_baseline.py`、`verify_baseline.py`、`verify_legacy.py`、`freeze_candidate.py`、`catalog_legacy.py`；另读取 `.gitignore`，追查默认课程数据库创建接缝 `campuslab/web.py` 和完整 `campuslab/courses.py`。本报告不冒称已由此代理完整阅读全部产品源码或测试；其余源码/测试追通由主执行者安排的另一代理负责。

## 实际Git、清单与字节核对

实际执行的Git命令均采用单次精确 `-c safe.directory=<本仓库绝对路径>`，没有更改全局配置或所有者。

- C、D仓库 `status --short --branch`：工作树均干净；HEAD与分支均匹配上述固定对象。
- `ls-files`：777项。逐项比较C/D工作字节，差异0；按Git blob对象格式 `blob <长度>\0<内容>` 独立计算SHA1并与D索引blob ID比较，差异0。
- 完整解析D盘98,690字节交付清单，778项重算SHA256：缺失0、摘要不符0。
- 清单自身SHA256：`93DC407BE48FFB4D2E8E79A852303B61AE4F578435DB3C06C81CF9BF900BAAC6`；根 `.sha256` 的摘要及文件名精确一致。
- `git ls-tree -r --name-only 3dddd33 -- campuslab web Start-Web.ps1` 得到20项产品文件，逐项 `git show <产品HEAD>:<路径>` 读取原blob，与D盘产品字节比较：全部一致。
- `merge-base --is-ancestor` 分别核验R1 `eee876053eebfb7d82e2ad6a9b45272f0075b1fe`、Node `42d86482fa1540b35fcdda6bbdf15d888f6b8cd1`、产品 `3dddd33` 到交付HEAD：均成功。
- C/D `rev-list --all`：各31个可达提交，集合完全相同。D盘 `git fsck --full --no-reflogs` 退出0，无对象完整性错误。
- 实读产品HEAD之后的提交路径：后续只涉及材料、证据归档及交付工具；20项已审产品字节实核一致，不仅根据文案判断。

产品20项包括：Start-Web.ps1；campuslab下 `__init__.py`、collect.py、courses.py、diagnosis.py、guest_probe.py、guidance.py、node_collect.py、node_probe.js、portable.py、preparation.py、probe.py、rules.py、torch_course.py、torch_probe.py、vm_course.py、web.py；web下app.js、index.html、style.css。

## 运行数据与已有修改边界

新检查发现D盘正式版有被忽略的 `data/courses.sqlite`：12,288字节，创建/修改UTC为2026-11-09 03:11:17，晚于02:48的交付记录。未读取数据库内容。web.py默认使用 `ROOT/data/courses.sqlite`；CourseStore初始化会创建父目录和courses表，因此它符合正常服务启动的运行产物，不能据此断言具体操作者或操作内容。

D盘当前非Git文件为782项。778项清单之外恰为：清单自身、清单.sha256、生成交付回执、该课程数据库。源码/材料没有发生字节差异。正常运行数据库应保持原位，不能覆盖、删除或作为新版本默认课程库复制。

C盘旧工作副本有867项忽略文件，顶层计数为campuslab 2、private 7、records 854、tools 3、vendor 1；没有本次查出的data库或.env项。只枚举路径，不读取private内容或凭据。新版本完整Git克隆自然排除这些私有映射、缓存和测试解压runtime；vendor需另按已固定来源与SHA处理。不应把旧private、data、.env或测试提取目录加入新版本默认数据。

## ZIP与旧原件保护

旧ZIP `D:\传智杯\submission\课程能力版_20261108_待补本人视频.zip` 实际44,841,193字节，SHA256 `A8A62225EB2BC235FD7C259600F946F537FD6447AEA08C35A594D4BF752C23C6`，808项，无重复路径。实际 `ZipFile.testzip()` 返回None，全部CRC通过；清单778项成员重新计算SHA256全部匹配。此处未声称本代理又逐项比对ZIP所有非清单成员；完整808项内容对比属于已读的上轮独立报告范围。

为确保只读，没有运行可能首次创建收据的保护工具main；依据其完整源码与现有记录，用内存Python重算：旧Node361项非Git文件无差异、无新增；原R1 212项无差异、无新增；旧原型/证据及保护副本814项无差异。未修改旧PDF、ZIP、版本目录或原型。

## 原始实测与首次失败的具体边界

PyTorch目录：

- 首次模块缺失的单测失败、验证脚本缺仓库导入路径的 `ModuleNotFoundError` 均保留，不能描述成学生环境修复。
- 最初int64任务CPU A/B运行成功；GPU B明确触发但返回 `addmm_cuda not implemented for Long`，报告不通过。当前float32任务有新摘要，另存float32-retest，旧失败未覆盖。
- float32真实CPU A/B为同一显式解释器，Python3.11.16、torch2.14.0+cu126，固定结果[[4,4],[10,8]]；GPU A缺实际运算而未知，GPU B有CUDA:0运算与同一UUID，九项通过。该过程是补齐运行证据，不是环境修复。
- 基础Python报告确有torch缺失；不是干净无Python实体设备。`current-rule-recompute` 明确仅规则复算，不能称新采集。部分早期源码SHA不同于最终产品是实际历史记录；当前报告适用性由最终审查另核验。

VM目录：

- first-red是模块尚未实现时的真实导入失败；vmrun -v记录确有 `Invalid argument: -v`，不能当版本查询成功。无参数帮助可读CLI1.17.0、真实退出4294967295；不是Workstation产品版本。
- 固定list原文 `Total running VMs: 0`；VirtualBox标准路径缺失。没有所选可读实例或Linux来宾报告。
- 最初CIM受限保留未知；另次获准只读提权取得HypervisorPresent=true、三旗标false，规则仍保留未知，未推断BIOS关闭。
- 真实VMware B晚于A，比较incomplete；软件存在不能代替实例、来宾、固定课程运行通过。

preparation目录：

- 首次模块缺失、首次实现后 `Python和Node都要安装` 被识别为recognized而预期conflict 的失败均保留。
- 原始CIM拒绝访问、nvidia-smi与D盘容量成功分别可见；后续只读Windows API回退取得物理内存总量与Windows版本，另存新报告。
- 内存是总物理内存而非当前空闲内存；显存为驱动报告，不证明框架实际运算。脚本声明network_requests=0不是操作系统流量抓包结论。

## 旧技术PDF实际核对

使用既有PyMuPDF只读打开实际文件，9页，363,180字节，SHA256 `5C7BD452C51F79441C3AB9117AFA4DDDA52C7CCE1567A7E6F921D865E1E44501`。全文提取6,608字符，各页字符数为668、697、608、799、753、477、808、804、994；每页均非空，完整产品HEAD在文本中。

技术PDF构建记录与visual-qa记录的页数/大小/摘要匹配；构建20项产品源SHA重算无差异。两张原截图与两张矩形裁切图SHA均匹配，Pillow在内存按记录矩形裁切并逐像素比较，完全一致。

本次没有逐页查看PNG或重新做视觉可读性检查，不把已读visual-qa中的历史视觉通过结论写成本代理新视觉实查。PDF提取可读不证明布局无缺陷。旧PDF仍仅描述上轮课程范围，且启动示例为.ps1，不能直接作为本轮新增能力的材料或无需修改执行策略的启动证明。

## 结论与后续审查边界

正式基线源码、完整历史、交付清单、已审20产品字节、旧ZIP及原件保护核对通过。唯一新增的非交付运行数据为D盘被忽略课程库，保持原位并排除复制即可；没有理由重置或改写旧版。

本报告只为本轮开发前基线核对作证。未运行本轮产品测试/浏览器/Notebook/JDK/SQL/DSH，未启动服务/VM/内核，未安装、联网调用模型、读取凭据、推送、上传或更改系统。真实Linux来宾、第二设备、实体手机、正式MP4、三条完整Prompt链、评审远程访问及本人上传回执等缺口仍按原证据保留。

本代理保留未参与实现的独立只读身份，后续新产品必须在主执行者固定HEAD与候选SHA后另行审查；本报告不自动扩张为新功能或最终交付通过。
