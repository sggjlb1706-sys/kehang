# 新目录交付首次预检（2026-11-09）

实际执行 `D:\ANACONDA\python.exe -B -m tools.deliver_courses --execute` 时，权限提升后进程用户为DELL，源工作仓库所有者为CodexSandboxOffline；首次git status触发Git dubious ownership拒绝，进程退出1。停止点是任何D盘目录创建/复制之前，两个新目标仍不存在；原文件未被写入。这是本地交付工具的用户身份适配问题，不是产品测试或用户环境故障，也不是自动审批拒绝。

修正仅为交付脚本中的源仓库Git调用加本次命令的safe.directory；D盘副本继续使用其自己的逐命令safe.directory。没有修改全局Git配置、仓库所有者或系统策略。产品20项文件、技术PDF和既有审查原件不变；交付复跑以实际新回执为准。
