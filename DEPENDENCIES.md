# 环境与可复现依赖

| 用途 | 需要的已有环境 |
|---|---|
| 网页和课程库 | Windows、Python ≥3.10（本机 3.13），Python 标准库含 sqlite3，支持原生 JavaScript 的现代浏览器 |
| 代表实训 | 课程 Python ≥3.10 且 <3.15，jupyter_client ≥8.0、ipykernel ≥6.0、NumPy ≥1.24、Pandas ≥2.0，已有 Jupyter Notebook/Lab 编辑器或兼容客户端，kernel.json 必须绑定所选 Python |
| SQLite 固定环境 | SQLite ≥3.35，独立回滚日志格式 scores.sqlite，专用目录。学生准备数据时使用课程 Python 中的 sqlite3 |
| 下载工具 | 可分发的官方 Windows 64 位 Python 3.13.17 嵌入包，沿用基线 vendor/python-3.13.17-embed-amd64.zip；SHA256 9E35319BFFEDAB8B36AD44D8F377CB4F1733BCEC257A0B6D04D94F01486DDB38。只读探针与课程解释器分别识别 |
| 路径选择 | 回车/L只读Python安装登记与PATH候选；F文件窗口使用Windows现有PowerShell及.NET WinForms，未安装新依赖。窗口不可用可继续用候选列表或手填，执行策略不修改 |
| 开发验证与材料重建 | Python unittest、Playwright 和 Edge、nbclient/nbformat、ReportLab、Pillow、PyMuPDF、Poppler 和 FFmpeg（本机现有）。常规网页及学生操作无需开发验证工具 |

诊断环境模板见 `.env.example`。网页不自动加载此文件。未配置时可正常使用课堂流程；课航诊断/聊天需另行配置并逐轮同意；API 与 DSH 现归拓展指南，阅读指南不会发起操作。其他课程各有自己的环境要求。
