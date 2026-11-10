# 开源适配与 AI / Agent 课程版：独立修复复核

日期：2026-11-10。复核者 `/root/product_review` 未参与实现或修复；本次仅新增本报告，未修改初审/子审报告、旧失败证据、产品或测试。范围为初审三项发现的闭合及产品差异核对，不扩为材料或最终交付审查。

## 固定版本与字节核对

产品修复 HEAD：`2c5ade24c512a6b15c7111f808192f480627c4fb`，工作区 `C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-reuse-ai-20261109`。冻结清单 `records/review/reuse-ai-final-candidate.json` 的 SHA256 实测为 `BD242703233272836DC99B6B819339EA30CC26CD9F404F7FB48E6FC0B6DFC615`；HEAD相符，80项源码/测试/第三方字节、165项指定证据全部匹配，零不符。

与初审固定 `bbee5bce71caa5ff9a0709b479db52d8190ddaed` 及其清单比较，仅4项源发生变化：`campuslab/ai_probe.py`、`campuslab/java_course.py`、`tests/test_ai_course.py`、`tests/test_java_course.py`；无新增/移除，另76项保持原字节。完整阅读该4项diff和对应现行执行分支，变更均可追溯到三项初审发现。UI、共用分派、其余课程以及实际采用的Educates结构/第三方原件未改变。其他新工具或材料不由本次产品diff结论自动覆盖。

## 三项发现闭合

| 初审发现 | 实际修复 | 本次独立复现与结果 | 结论 |
|---|---|---|---|
| P2-1 JDK版本退出未知仍全通过 | 版本判断要求返回码已取得；同源检查要求两工具成功退出且无错误 | 分别对java、javac构造原正常报告，仅置该工具returncode=None。各自`java:java`或`java:javac`为unknown，`java:identity`为unknown，整体passed=false；另一工具及既有编译/运行事实保留 | 闭合 |
| P2-2 缺SSL依赖被归通用runtime且丢失Python身份 | 探测器先记录actual/OS/Python，单独捕获必要依赖导入失败，回传stdlib=False与dependency_missing；依赖不齐不调用API | 用既有官方嵌入ZIP在临时目录解压，唯一省略`_ssl.pyd`；明确选择其python.exe真实调用collect。实际Python3.13.17及路径保留，python=pass、api:dependency=missing、category=dependency_missing、attempted=false；协议/成果unknown，passed=false | 闭合 |
| P3-1 Java运行异常污染成功的编译事实 | 根据编译返回码把异常写入当前compile或run阶段 | 专用临时JDK夹具、mock版本成功和编译成功，再抛运行TimeoutExpired。compile返回0且error空，java:compile=pass；run.error含TimeoutExpired，java:run=unknown，整体不通过 | 闭合 |

Java两类复现是构造报告/调用协议，不称为真实编译器故障或实际挂起。SSL负例是受控真实依赖缺失夹具，不称为本人既有Python损坏；临时副本/目录在结束时全部清理，原ZIP未变，未安装/注册。上述复核没有网络API请求、DSH运行或凭据读取。初审 `reuse-ai-product-review/java-no-version-exit.json`、`java-runtime-timeout.json`，子审 `reuse-ai-api-dsh-review/probe-results.json` 和两个初审全文均原样保留，未用修复结果覆盖旧失败。

## 测试与集中证据

本次独立实跑 `D:\ANACONDA\python.exe -B -m unittest discover -s tests`，终端实际输出：115项、3.015秒、OK、进程退出0。新增3项针对回归与三处修复相符；没有把API/DSH子集测试再加到115项上。

独立逐项核对五套最终归档浏览器记录status和source SHA，52组全部通过且与当前产品字节一致：

- `records/browser/20261110T003103731709Z/results.json`：原Python/模型网页10组。
- `records/browser/20261110T003104245789Z-courses/results.json`：PyTorch/VM等9组。
- `records/browser/20261110T003116207099Z-node/results.json`：Node9组。
- `records/reuse-ai/browser-ai/20261110T003136119642Z/results.json`：新增AI/DSH6组。
- `records/reuse-ai/browser-data/20261110T003103340935Z/results.json`：Notebook/JDK/SQLite18组，另有起止源SHA稳定标志true。

其余四套脚本没有记录起始SHA稳定字段，因此本复核只确认记录的最终source SHA匹配，不把不存在的稳定字段推断为已记录。另核对 `records/courses/review-ui/20261110T003123Z/results.json`：3项构造UI回归通过，所列源SHA相符。52组与这3项是主执行者重新运行的归档证据核对，本复核没有再启动浏览器重复跑全部场景。

对 `records/courses/model/20261110T003151Z/A.json`、`B.json` 用当前共用rules再次比较：outcome=verified、B通过，local/offline均true、实际输出2、ended_with_eos=true。这是新真实离线推理报告的独立复算；复核者没有重新加载模型，亦未把它称为外部AI报错诊断成功。

## 复核结论与适用范围

**初审2项P2与1项P3均闭合；在本次固定产品HEAD和SHA范围内，未发现新增阻塞。** 本结论与初审全文、API/DSH子审全文共同适用，初审关于真实证据/模拟/本人操作的限制继续保留。

真实DeepSeek API仍未调用，DSH仍缺本人明确安装/模型/授权与真实Agent任务，网页本人学习记录不认证登录；Linux来宾/SSH/Hadoop集群、第二设备/实体手机等仍按实际证据列缺。Notebook/JDK/SQLite正常本机通过不提升这些未验证项目。

新版PDF、视频素材/Prompt链、最终HEAD/清单、交付工具、完整Git副本、运行时、ZIP内容SHA/CRC、Python直启烟测和旧版保护，须另做独立材料/交付核对。本产品delta不认证赛事资格、完整材料合格或实际提交成功。
