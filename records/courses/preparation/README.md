# 准备能力开发证据

本轮真实顺序：先写5项针对性单测，运行得到模块缺失失败；实现后保留Node紧邻中文时识别遗漏的失败（`unit-after-implementation.txt`）；修正该分词条件后5项通过（`unit-pass.txt`）。随后实际预检得到CIM访问失败但NVIDIA/容量可读报告；新增只读Windows API回退后另存重采报告。未安装、未修改系统/网络、未读取旧进程或调用模型。

实际命令（工作目录为本仓库；执行时间在各报告中）：

```powershell
& 'D:\ANACONDA\python.exe' -B -m unittest discover -s tests -p test_preparation.py
& 'D:\ANACONDA\python.exe' -B -m campuslab.preparation --drive 'D:\' --output 'records\courses\preparation\actual-hardware.json'
& 'D:\ANACONDA\python.exe' -B -m campuslab.preparation --drive 'D:\' --output 'records\courses\preparation\actual-hardware-fallback.json'
```

第二个报告使用新增回退代码重新采集。原始CIM与nvidia-smi命令、退出码和stdout/stderr随报告保留；stdout没有密钥。设备UUID是本机驱动证据，交流分享须走既有脱敏预览，不直接公开原始报告。

硬件预检可在没有torch、transformers或模型权重的工具Python运行；这次使用已有基础Python，未调用课程Python或模型。该证据是本开发机实测，不是干净设备、第二电脑或手机实测。
