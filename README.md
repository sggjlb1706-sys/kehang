# 课航 · 计算机课程学习与实训助手

学生用同一张成绩表完成 Notebook 统计和 SQLite 查询，教师可以重算提交数值、核对两项环境报告、查看首次错误和重交记录。其他 13 类课程环境入口可从工作台的“确定任务”继续使用。

## 在已有 Windows 环境中启动

完整解压，进入有 `campuslab`、`web` 和 `vendor` 的根目录。网页服务使用已有 Python 3.10 或以上，只有标准库依赖。本机已核验的解释器为 `D:\ANACONDA\python.exe`。其他电脑将下一行的解释器替换为自己的绝对路径，也可使用已配置的 `python`。

```powershell
& 'D:\ANACONDA\python.exe' -B -m campuslab.web --port 8783 --database '.\data\practice.sqlite' --runtime-zip '.\vendor\python-3.13.17-embed-amd64.zip'
```

打开 http://127.0.0.1:8783/ 。端口被占用时换一个空闲端口，并用相同端口访问。按 Ctrl+C 停止本次服务。上面的路径会创建专用课程库。为演示教师与学生分别启动两个实例时，第二个实例请同时改端口和数据库文件名。

## 用一堂课复核产品

1. 在首页“教师发布 / 学生导入实训资料包”发布，导出课堂包，下载完整实训资料。在学生实例导入课堂包，展开目标、前置条件与步骤。
2. 解压全部资料至新目录。打开随包 Notebook，选择课程内核，填写三个统计表达式并运行。用同一份 CSV 按模板填写分组 SELECT，运行本地 SQLite 练习，得到 `实训成果.json`。
3. 回到课航，选成果文件、点击核验。教师可保存完成物，再在“教师核对学生完成物”中逐次重算。环境探针、本人阅读声明与提交数值在页面分别显示。
4. 在课堂面板分别进入 Notebook 和 SQLite 环境。Python / Notebook 下载检测工具后可双击 `Start-Collect.cmd`，输入本人目标、Notebook 内核及 A/B 阶段，确认 START。SQLite 使用高级命令选择练习实际生成的 scores.sqlite。两份原始报告可一次选择；较晚同目标报告才可作为复检。

**十分钟启动的前置**是已有 Python 和可用浏览器。要在该时间内演示计算，还需已有 Jupyter、受支持的 ipykernel、NumPy、Pandas 和匹配的内核定义。版本及开发工具见 `DEPENDENCIES.md`。本机练习不需账号、模型或密钥；`.env.example` 为自愿使用 AI 诊断时的进程环境变量模板。

## 评审材料

- `output/pdf/课航_实训闭环技术文档.pdf` 与 `output/video/课航_实训闭环演示.mp4` 对应本版。视频包含隔离标签页的实际演示、真实运行文件及注明来源的 AI 协作回顾。
- `docs/实训版操作前后对照.md` 记录代表路径的实际输入和文件选择次数。`docs/实训版Prompt链逐项核查.md` 给出过程来源与缺项。
- 全历史本机包另含 `records/practice/lab-run` 的执行后 Notebook、SQL、课堂产物与组件 A/B，`records/practice/completion-local.json` 的完整实际核验过程，以及 `REVIEW.md` 的独立审查入口。本机原始环境报告含本机路径。
- 完整历史以 `a7dac52` 的 39 个已有提交为基线。既有开源许可与适配见 `THIRD_PARTY_NOTICES.md`。交付物中旧版报告、PDF和脚本均保留其原版本语境。

这是同一电脑两个独立实例的代理验证。实训结果核验可以确认数值及版本，无法证明原创或学习掌握。真实模型请求、DSH Agent 授权回合、外部设备、至少三条完整核心 Prompt 链、评审可访问托管地址和正式提交回执仍有缺口。
