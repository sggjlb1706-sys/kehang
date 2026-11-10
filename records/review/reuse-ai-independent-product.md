# 开源适配与 AI / Agent 课程版：独立产品初审全文

审查日期：2026-11-10。审查者 `/root/product_review` 及其独立只读子审查者 `/root/product_review/api_dsh_review` 均未参与本轮实现或修复。仅新增本审查报告和专用复现实验记录，未改产品、测试、既有报告、正式版、Git配置或系统。主执行者收到发现后开始修复的字节不属于本报告所审版本，须另行固定并复核。

## 固定对象与结论

- 独立工作区：`C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-reuse-ai-20261109`。
- 产品 HEAD：`bbee5bce71caa5ff9a0709b479db52d8190ddaed`，分支 `codex/reuse-ai-courses-20261109`。
- 候选清单：`records/review/reuse-ai-candidate.json`，SHA256 `2BF219A95A55D242D5EBD56C0D38BE21EDB79E20D13DE4ADA847CE8C8F230E35`。
- 开始审查时独立逐字节核对清单内 80 项源码/测试/第三方文件和 154 项证据，零不符；HEAD 相符。清单选择的第三方原件当时尚待随材料提交，字节由该清单固定，不冒称原产品提交已跟踪它们。

**初审发现 2 项 P2 和 1 项 P3；本固定版本尚不能闭合产品验收。** 未发现其他有依据的阻塞。112 项现有单测独立实跑通过，但未覆盖下列分支。修复须保留原发现/失败，并以新 HEAD/SHA、针对回归和必要贯通证据作独立 delta；不能把本初审写成已通过。

## 实际阅读与核对范围

完整读取本轮执行提示词、`docs/能力对照-复用AI-20261109.md`、适用 `AGENTS.md`，并核对 TASK/PLAN/PROVENANCE 当轮约定。完整追通 `rules.py` 的固定任务/校验/分析/比较、`collect.py` 参数分派、`courses.py`、`portable.py`、`web.py`，以及 `web/app.js` 的新旧任务入口、状态清理、命令生成、报告导入、教师任务、异步令牌、预览/同意、分享和教学重试；读取新增表单 HTML、指导的新场景分支及原诊断的发送/脱敏接缝。

对 Notebook 的 `notebook_course.py` / `notebook_probe.py`、Java、SQLite、AI课程/探测器、DSH、教学适配及其针对测试逐模块完整阅读。原六类的任务快照在独立复算中与 e0aca9c 基线完全相同；原 Node、PyTorch、VM 的相关采集/身份与分析接缝作回归核对，不把新课程扩展当作对全部历史实现的重新认证。

读取 Educates 两份原始模板、Apache LICENSE/NOTICE、采用 manifest/ADAPTATION、Python适配及前端实际 header/title/body 组织，核对 `name/title/description/cooldown=3` 到封闭检查、外部 JS 展示和本人重采动作的调用链。它是小范围结构与字段移植，原 Hugo/HTTP examiner 脚本分派被替换；非整个平台部署，也非只留外链。保留官方源码/作者/许可，产品不运行 shell/args/autostart/无限重试。DSH 子审核读官方固定版 package、CLI分派/安全/provider资料和桌面运行时相关段落，确认桌面与 CLI 分层有来源支持；详细阅读范围见子报告。

五套已归档浏览器记录合计 52 组，其 source SHA 与开始审查时产品一致：原 Python/模型10组、Node9组、PyTorch/VM等9组、新AI/DSH6组、Notebook/JDK/SQLite18组；另核对最终3项构造UI回归。这里是源字节和归档证据核对，不是本审查重新执行全部52组。抽看 Notebook 390px 和 Java 桌面截图，正文/状态可读；390px均为桌面Edge模拟，不是实体手机。DSH长页仅核对布局记录和状态边界，不以缩略图认证每段文字的视觉质量。

## 发现

### P2-1：JDK版本命令退出证据未知仍可全部通过

位置：固定 HEAD 的 `campuslab/java_course.py:69` 至 `:74`。

版本字符串落在范围时先置 pass，随后仅在 `returncode is not None` 且失败时降级；因此返回码为 `None` 的版本观察仍被标为 pass。同源检查只看 home/hash/版本，也未要求版本命令成功。保留其余编译/运行事实，就能让两项版本命令退出证据均未知的报告显示全部通过。

最小构造复现：采用 `tests.test_java_course.evidence()`，只把 `facts.tools.java.returncode` 与 `facts.tools.javac.returncode` 改成 `None`，调用共用 `rules.analyze`。实际结果 `passed=true`，六项全部 pass。原始构造报告/结果保存于 `reuse-ai-product-review/java-no-version-exit.json`；不是设备实测或真实学生故障。

影响：未知版本执行证据被提升为已通过，违反“不完整/未知不能全通过”的核心契约。应要求实际版本观察具有成功退出证据（或拒绝矛盾报告）；两个工具分别处理，不能借编译/运行的其他事实补成该项成功。

### P2-2：可执行 Python 缺 SSL 时丢失身份并误归通用运行异常

位置：固定 HEAD 的 `campuslab/ai_probe.py:13`、`campuslab/ai_course.py:250` 至 `:253`。

API探测器在 `import ssl` 失败时直接非零退出，不返回已启动解释器身份或 `stdlib=False`；父采集器把所有非零退出统一归为 runtime。因此该实际路径中 `python=None`、`stdlib=None`，Python与API依赖均未知，不能区分已明确缺少依赖与运行异常。分析器虽然支持 `stdlib=False → missing`，实际探测器不产生这个分支。

独立子审使用既有官方嵌入 ZIP 的临时副本，仅不解压 `_ssl.pyd`，明确选择该副本 Python，真实调用未发送模式的 collect。观察到 `category=runtime`、`dependency_status=unknown`、`python_status=unknown`、`passed=false`。未安装/注册/联网，临时副本已清理，原ZIP和产品未改。这是受控真实依赖缺失夹具，不是本人现有环境损坏。完整脚本、结果及20项子审测试在 `reuse-ai-api-dsh-review/probe_contracts.py`、`probe-results.json`、`unit-tests.txt`，子审全文 `review.md`。

影响：没有造成假通过，但本轮明确要求的“缺依赖/运行异常”分型未落实，且已取得的解释器身份丢失。建议先采身份，对必要标准库导入单独捕获、返回缺依赖事实与无密钥类别；依赖不齐不调用接口，后续以相同夹具复核。

### P3-1：Java运行超时错误写入已成功的编译阶段

位置：固定 HEAD 的 `campuslab/java_course.py:121` 至 `:129`。

编译和运行共用一个 except。固定 javac 编译已成功、java 运行出现 OSError/TimeoutExpired 时，except 把运行错误写到 `facts.compile.error`。观察结果变成编译 `returncode=0` 却 `java:compile=mismatch`，运行阶段仍写“尚未编译运行”。

使用已存在JDK路径只作文件身份读取，mock两个固定版本调用成功、编译成功、随后运行 TimeoutExpired 的窄协议复现，记录于 `reuse-ai-product-review/java-runtime-timeout.json`；未实际挂起JDK，非真实超时实测。应保留编译成功，把运行异常归入 run。此项不造成假通过，影响失败定位的准确性。

## 独立执行与证据复算

- `python -B -m unittest discover -s tests`：112项通过，输出 `reuse-ai-product-review/unit.txt`。子审另运行API/DSH20项通过；这些是同一测试集的子集，不能加总成132项。
- 原六类 task 与基线源码工厂输出完全一致；新增七类按共用规则重算选定当前A/B，结果见 `reuse-ai-product-review/reanalysis.json`。
- Notebook 当前A/B为10项 stable-pass：真内核/明确解释器、NumPy/Pandas、固定数据、清理均有报告。真实Pandas缺失负例与错内核/缺目标记录有清楚标签，换解释器未伪装同目标修复。
- JDK 当前正常A/B为6项 stable-pass；SQLite当前为5项 stable-pass，文件内容前后相同。SQLite独立rollback模式/侧文件拒绝、固定只读SELECT、授权器及工作量限制与本轮范围一致；不扩成服务器数据库验收。
- DeepSeek API 当前Python/标准库/固定请求为pass，实际调用与成果unknown；没有收费或其他真实外部模型请求。网页学习构造正确数字成果仍不使登录/远端连接通过。
- DSH桌面指定软件路径missing，CLI的所选Node为pass、指定包missing；准备的专用工作区为pass，模型/本人权限/工具回合unknown、尚无产物missing。不是全机安装扫描，更不是实际Agent成功。子审复现重复旧成功摘要即使改采集时间也被拒绝。
- 新归档Qwen报告 `records/courses/model/20261109T082553Z/B.json` 经当前规则重算通过，目标是既有model-venv；这与错误选择PyTorch解释器缺transformers的较早真实负例分开保留。此处为新报告复算，不冒称审查者重新加载了权重。

## 边界与后续复核

审查没有安装/下载成品、运行DSH、发外部模型请求、读凭据/旧进程密钥、读本人课程数据库、启动VM或改变系统策略。使用已有开发依赖执行单测、读取指定原始报告/源文件，以及在专用临时目录制造明确负例。基线补充报告记录的先前代理额外hash用户DB边界偏差保留，本审查未重复该操作，也不改写成“从未读取过DB”。

本初审仅覆盖所列固定产品与证据。材料PDF、视频、Prompt完整链、最终HEAD、完整交付SHA、ZIP/CRC、副本启动/历史和旧版保护需独立材料/交付核对，不能由产品初审推导为全部通过。真实API单次同意、已安装DSH及本人Agent授权、Linux来宾/集群、第二设备/实体手机、本人MP4、评审远程访问和实际提交仍按取得证据分别判断。
