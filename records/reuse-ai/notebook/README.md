# Notebook 数据分析：实现与真实本机证据

本轮先写7项针对测试，`targeted-first-red.txt`是模块缺失的真实失败；实现后7项通过。错误、未知、错内核、任意启动命令/环境配置与身份变更均不能全部通过。构造测试不作为设备实测。

## 当前真实结果

`20261109T080945725345Z/`保存实际A/B及分析。本人任务授权内，明确选择已有 `D:\ANACONDA\python.exe` 与 `D:\ANACONDA\share\jupyter\kernels\python3\kernel.json`，不是普通Python求和冒充内核：

- 探测Python与实际新启动内核均是Python3.13.9及相同sys.executable。
- Jupyter Client8.6.3、ipykernel6.30.1；真实内核内导入NumPy2.3.4/Pandas3.0.3，分别记录模块文件身份。
- 新内核执行本项目原创固定三行CSV（A10、A20、B12）及数组，得到array_sum=42、group_totals={A:30,B:12}、rows=3。
- A/B全部10项通过；同kernel.json路径/SHA/argv、实际解释器身份和有序时间核对。最初模块级复核记录与最终共用rules复核分别保存，不能在尚未执行共用复核前冒称已完成。
- 两次kernel_stopped/channels_stopped均为true，临时内核和连接文件清理完毕；没有连接或停止用户原有Notebook会话。

真实命令：在新仓库目录运行 `D:\ANACONDA\python.exe -B records\reuse-ai\notebook\run-real.py`。首次验证脚本raw字符串尾部反斜杠产生SyntaxError（real-first-run.txt）；修正脚本后运行成功，原失败保留。这个失败发生在验证脚本，未启动内核，不是学生环境故障。对应各collector调用的完整固定命令在A/B报告commands中。

`deliberately-missing-target.json`是故意不存在路径的负例，非干净Windows设备。`deliberately-mismatched-kernel.json`选择专用构造kernel.json，其argv指另一解释器；静态校验拒绝启动，保留不符合/未知，不借另一份Python凑成功。

`pandas-missing-real-20261109T081140879259Z/`是另一个真实负例：在专用证据目录构造安全固定kernelspec（未注册/修改系统内核），明确指向已有PyTorch Python3.11.16，真实启动后观察到Jupyter Client8.10.0、ipykernel7.4.0、NumPy2.4.6及Pandas确实缺失。package:pandas=missing、固定单元运行mismatch，整体不通过；正常清理自己的内核。该kernelspec是测试夹具，不能说成用户原有已注册PyTorch内核实测，更不能把换解释器说成同目标修复。

## 固定执行边界

只接受已有kernel.json中绝对Python路径和固定 `-m ipykernel_launcher -f {connection_file}`，允许前置 `-Xfrozen_modules=off`。不接受env、自定义kernel provisioner、shell命令或任意Notebook代码。通过静态核对后，按相同明确Python重建最小临时kernelspec；启动时增加 `-I`，用专用IPython/Jupyter目录隔离用户启动脚本，仅监听127.0.0.1。依赖来自所选Python，不自动安装。

超时由内核探测器的ready/单元期限处理并finally关闭自己创建的内核；外层兜底超时仅按新建probe PID终止其进程树，不扫描或停止已有用户会话。正常路径清理已实测，兜底超时是代码/构造验证范围。

演示版本范围、数据与程序均是本项目要求，不是高校统一课程版本。`campuslab/data/notebook_scores.csv`为原创教学附件；执行程序只使用相同固定数据，不读取用户任意文件。

## 官方技术依据

实施时读取[Jupyter Client API](https://jupyter-client.readthedocs.io/en/stable/api/jupyter_client.html)的KernelManager、KernelSpecManager、start_kernel、execute、get_iopub_msg与shutdown_kernel；仅使用已有安装，未复制上游实现或引入JupyterHub/公网Notebook服务。课程方向来源沿用云南师范大学数据分析大纲，来源状态在课程目录注明；此处运行证据来自本轮代码，不由课程大纲背书。

本机完整内核流程已实测；新代码的第二设备、实体手机、干净无PythonWindows与独立新手仍未测。原始报告含本机路径，仅供本人本机审阅，公开交流使用脱敏副本。
