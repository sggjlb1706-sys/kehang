# 课航实训：从CSV到SQL

目标：读取同一份三行成绩数据，用Notebook计算分组统计，再用SQLite查询复算；保存实际操作文件并提交限定JSON。教师要求和预期值固定，学生不能通过编辑课程包更改核验条件。

## 前置条件与资料位置

需要Windows、已有Python 3.10—3.14、Jupyter/ipykernel、NumPy≥1.24、Pandas≥2.0。课航不自动安装。SQLite使用该Python的标准库，不需要服务器数据库。环境未准备好时先按对应课程指导手动处理。

将整个ZIP解压到一个**新的专用目录**，例如`D:\课程练习\课航 CSV SQL`。以下六份文件须一起保留：本README、`scores.csv`、`01_Notebook练习.ipynb`、`02_SQLite练习.py`、`成果模板.json`、`课堂资料包.json`。不要在ZIP预览中运行，不覆盖私人目录或数据库。

教师：在课航实训区域发布固定课堂资料，下载课堂资料包JSON及全部资料ZIP，将它们通过可信渠道交给学生。学生：在另一实例导入课堂资料包后获得**两个分别发布的课程码**；Notebook与SQLite分别导入/分析环境报告。资料摘要只是内容一致性校验，不是教师数字签名。本轮传递验证为同一电脑的两个独立本机实例，不代表第二设备或独立新手测试。

## 1. 先检查Notebook环境

在课航选择Notebook环境任务，明确课程Python及同源`kernel.json`。例如已有Jupyter内核列表可在本人终端用所选Python执行`-m jupyter kernelspec list`查找；只选择自己的已知内核定义，不运行来源不明的配置。按下载工具指导手动采集初检报告，检查真实内核的`sys.executable`与所选Python一致。

固定环境探针运行数据成功只代表该探针的运行证据，不能代替本人的实训操作或成果提交。阅读勾选也不会让环境或成果通过。

## 2. Notebook读取与计算

在已有Jupyter中打开`01_Notebook练习.ipynb`，选择上一步确认的课程内核。启动Jupyter时将工作目录设为本解压目录，第一格会显示工作目录、解释器和CSV内容摘要；若找不到CSV，应把Notebook和CSV放在一起并切换到该目录后再运行。

从上至下运行。按提示填入三处TODO：`row_count`、`score_total`、`group_totals`，分别计算行数、score合计与按category分组的score合计。可使用`len(df)`、`df['score'].sum()`及`df.groupby('category')['score'].sum().to_dict()`这些Pandas操作，理解后填入相应位置。不要直接拿预期数字代替实际计算。

应看到数据`A,10 / A,20 / B,12`，共3行，合计42，A组30、B组12。最后一格会把本人计算结果写到`notebook-result.json`。保存已运行的Notebook原件；如果仍为None，最后一格会要求先完成TODO。包内的成果模板是字段说明，空值不是完成成果。

## 3. SQLite同源查询

用文本编辑器打开`02_SQLite练习.py`，只填`QUERY`的TODO：写一条从`scores`表按`category`分组，计算`COUNT(*)`和`SUM(score)`，再按`category`排序的SELECT。固定目标为：

```sql
SELECT category, COUNT(*), SUM(score) FROM scores GROUP BY category ORDER BY category
```

在该目录打开终端，用**自己在Notebook中确认的课程Python**主动运行脚本。例如在PowerShell中：

```powershell
& '课程Python的绝对路径\python.exe' -B '.\02_SQLite练习.py'
```

将示例路径替换为自己的实际路径；可以保留目录空格和中文。脚本定位自身目录，不借终端当前目录找资料。它校验CSV摘要，在`scores.sqlite`尚不存在时显式创建专用演示文件并导入CSV；已有文件不会被覆盖。之后以`mode=ro`、`query_only`只读执行本人填写的SELECT。它不会访问其他数据库，也不上传任何内容。

应得到`[['A', 2, 30], ['B', 1, 12]]`并生成`实训成果.json`，其中Notebook与SQLite结果及各自课程任务ID分别保留。若SQL有误，记录终端错误，修正QUERY后再次运行；已有演示库仍保持。若已有库结构或内容不匹配，使用新的专用目录重新操作，不要覆盖私人文件。缺少`notebook-result.json`时先回到第2步。

## 4. 提交与复检

在课航实训成果区域选取`实训成果.json`并核验。页面区分：缺少成果、结构错误、旧任务/资料身份不匹配、数值错误、数值符合。保留**首次错误**及后续正确的真实记录，然后重新提交；代理构造的测试负例会明确标注，不冒充学生犯错。

再分别选择Notebook与SQLite环境任务。SQLite的目标是刚创建的`scores.sqlite`；按各自下载工具手动采集初检A、稍后同目标复检B并导入。Notebook绑定同一Python与同一kernel.json，SQLite绑定同一文件内容和同一工具运行时；两者的通过结论不能混成一份环境证据。稳定复检不代表修复了不存在的故障。

下载页面的完成物JSON，连同已运行Notebook、CSV、`notebook-result.json`、SQLite练习源码、`scores.sqlite`、`实训成果.json`及两个组件各自的环境报告原件交给教师。关闭或刷新页面前保存完成物，页面会话记录不等于服务器长期成绩库。

## 教师如何核对

核对固定任务/资料/数据摘要及两项数值，阅读提交历史及实际操作文件；需要时在受控的本人环境重做固定步骤。课航的成果核验只读取限定JSON，不运行上传Notebook、Python、SQL或课程包命令。预期数字公开；同任务同数据的相同正确结果**不能证明实际操作、学习掌握、作品原创或未复制**。完成物只整理证据，不给出这些超出范围的认证。
