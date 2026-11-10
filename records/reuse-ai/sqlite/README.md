# SQLite 单机 SQL 入门固定课程

仅SQLite独立rollback-journal文件路线，不声称MySQL/PostgreSQL服务器课程已支持。不接受WAL模式或带-wal/-shm/-journal侧文件的数据库，避免只核对主文件SHA却遗漏关联数据；database_mode明确进入固定快照。明确选择数据库文件，mode=ro与query_only打开，只执行固定表结构读取和分组SELECT；禁用trusted_schema、扩展加载默认保持关闭，authorizer限制为SELECT/READ及count/sum，进度回调限制查询工作量。采集前后记录内容SHA，绝不创建/修改目标数据库。

准备数据是独立显式动作：`D:\ANACONDA\python.exe -B -m campuslab.sqlite_course --prepare-demo C:\课程示例\scores.sqlite`。要求父目录已经存在，目标文件不存在；拒绝覆盖。所建表和三行数据为本项目原创：A10/A20/B12。该准备函数不会由采集器自动调用。

先写6项测试，targeted-first-red.txt因模块缺失失败，实现后6项通过。完成后按单文件身份边界补WAL反例，最终7项通过。测试实际在专用临时SQLite数据库运行，验证只读采集不改变字节、缺失文件不被创建、错误DB/结果不通过、任意SQL重封任务拒绝、换DB内容/路径或运行时拒绝复检。构造的坏结果/字段不冒称学生真实故障。较早A/B对应尚未写入database_mode的开发快照，保留历史，不当作最终当前任务证据；最终路径见本目录最终复核记录及browser-data最终记录。

真实A/B在 `20261109T080945725345Z/`。显式准备并选定该目录下scores.sqlite，使用已有工具Python `D:\ANACONDA\python.exe` 中SQLite3.50.2。固定SELECT得到A/2/30与B/1/12；前后SHA均 `84da226bfffb8e684ae3d1690ace11dabff3aae03f0b79fbbf38bc6c39ba37e9`。两次全部5项通过，同一文件/内容摘要/工具运行时与有序时间；这属于稳定通过，不是数据库故障修复。

实际触发命令 `D:\ANACONDA\python.exe -B records\reuse-ai\notebook\run-real.py`；脚本先明确调用prepare_demo，再独立调用collect A/B，不把准备数据库说成只读采集。故意不存在目标的报告也保留，采集没有创建该路径。

实施时读取Python官方[sqlite3文档](https://docs.python.org/3/library/sqlite3.html)核对URI mode=ro、set_authorizer、set_progress_handler及连接关闭语义。产品依赖已有Python标准库sqlite3；该模块属于可选构建组件，缺失时需要选择含它的工具Python，不自动安装。JDK/Notebook/原课程通过均不替代SQL固定结果。

此处是本机文件SQL真实证据；没有连接其他数据库实例、读取账号凭据或修改任何正式课程库。原始报告含本机路径，仅供本人本机审阅。
