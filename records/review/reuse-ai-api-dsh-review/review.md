# API / DSH 独立只读子审查

审查日：2026-11-10。审查者 `/root/product_review/api_dsh_review`，未参与实现或修复。固定产品 HEAD `bbee5bce71caa5ff9a0709b479db52d8190ddaed`；主审已核对候选清单 SHA256 `2BF219A95A55D242D5EBD56C0D38BE21EDB79E20D13DE4ADA847CE8C8F230E35`。本报告不认证材料或最终交付。

## 范围与实际验证

完整阅读 `campuslab/ai_course.py`、`ai_probe.py`、`dsh_course.py`、对应 `test_ai_course.py` / `test_dsh_course.py`、采集分派与复检接缝；核对指导中的 AI/DSH 分支。核对保留的官方 desktop/CLI package、CLI bin/args/installed-bin、安全说明、provider指南及桌面运行时/可选命令注册的相关段落。桌面与 CLI package 均为 `0.2.2-rc.1`；桌面发行与匹配DSH运行时版本同一，CLI引擎 `>=24.9.0`，桌面无需外部Node的区分有官方源码/文档支持。

独立运行 `python -B -m unittest tests.test_ai_course tests.test_dsh_course`，20项通过，原始结果 `unit-tests.txt`。这包含构造协议/假元数据，不代表真实 API 或 DSH 成功。另运行 `probe_contracts.py`，结果见 `probe-results.json`：已知构造密钥误入预览在probe前拒绝；重复成功Agent摘要不能仅修改采集时间冒充新复检。审查无真实外部模型请求、无DSH启动、无凭据/个人课程库读取。

## P2：API标准库依赖缺失在实际采集器中只能退化成通用运行异常

位置：`campuslab/ai_probe.py:13` 与 `campuslab/ai_course.py:250`、`:253`。

当所选Python可执行但缺少SSL模块时，探测器在 `import ssl` 处直接非零退出，既不返回解释器身份，也不返回 `stdlib=False`。父采集器将所有非零退出统一归为 `runtime`，报告为 `python=None` / `stdlib=None`，对应Python、API依赖均为未知。产品虽然支持分析 `stdlib=False → missing`，实际采集路径不能产生该事实。

复现使用现有官方嵌入ZIP的临时副本，仅不解压 `_ssl.pyd`，未安装、注册或修改原运行时；明确选择副本中的python.exe，调用未发送模式的真实 `collect`。结果为 `category=runtime`、`dependency_status=unknown`、`python_status=unknown`、`passed=false`。临时副本在结束时清理，原ZIP及产品未改动。这是受控实际依赖缺失夹具，不能描述为本人现有课程Python损坏。

影响：本轮明确要求“缺依赖”与“运行异常”分型，此分支无法给出缺依赖结论，且丢失实际可执行Python身份。它不会造成假通过，但未满足API课程的失败诊断验收。建议先采集解释器身份，对必须的标准库逐项捕获导入失败并返回 `stdlib=False` 与无密钥的类别；依赖不齐时不调用接口。修复后以同一临时夹具复核，保留本次失败。

## 其余所审边界

未发现其他有依据的阻塞：默认采集不取密钥/不发送，显式发送先显示固定目的地及实际消息、确认摘要后终端取密钥；响应体、CL/内容类型、重复外层JSON、工具调用、模型/角色/结束状态及固定数字分别核对，未知不提升。DSH只执行所选Node的固定身份表达式，未执行DSH或npx；桌面无Node检查；软件/运行时/工作区/公开提供方与模型/权限/工具摘要/本机产物分层，构造来源不会全通过，已知组件及实际任务时间复检限制均有覆盖。最小本人摘要是本人转录与本机产物的关联，报告明确不提供远程真实性证明。
