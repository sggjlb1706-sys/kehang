# PyTorch课程纵切验证（2026-11-08）

本目录记录本轮真实开发与本机验证，非第二设备、独立新手或从零安装证明。课程来源方向参考重庆科技大学深度学习大纲；Python3.10至3.15以下、torch>=2.2、固定float32矩阵程序及CUDA:0要求均为本项目演示配置，不是该校原版课程约束。

## 当前结果

- `unit-first-failure.txt`：先编写9项协议/规则测试，模块尚不存在，实际失败。`unit-second-run.txt`：首次实现后9项通过。`unit-final.txt`：补充GPU探测错误不能全部通过后10项通过。
- `float32-retest/`：当前固定任务真实采集。明确课程解释器 `D:\ANACONDA\envs\pytorch\python.exe`，Python3.11.16、torch2.14.0+cu126、CUDA构建12.6、RTX4060 Laptop GPU约8GB。CPU A/B五项均通过，稳定复检；GPU A未主动运算，GPU运行保留未知，整体未通过；GPU B显式`--gpu-run`后九项通过。CPU和GPU为不同任务快照，均记录固定float32矩阵结果`[[4,4],[10,8]]`。
- `actual-base-python.json`：另明确选择现有 `D:\ANACONDA\python.exe`，真实验证框架缺失路径，不代表无Python设备。
- `current-rule-recompute.json`：最后仅收紧GPU错误处理后，用当前规则复算上述真实报告，未重新采集设备。源码SHA逐项保存；probe采集程序字节未变。

GPU设备UUID独立记录并用于同目标复检。设备名称不代替UUID；未获得UUID时GPU身份保留未知。同一解释器中的另一个UUID不可复检为同一目标。已知身份不可通过CPU成功替代；初检GPU身份未知、复检补齐可归为验证补齐，不编造环境修复。

## 保留的真实失败

`real-output.txt`是开发验证脚本首次直接运行时未将仓库加入导入路径，发生`ModuleNotFoundError: campuslab`。修正仅发生在验证脚本；它不是产品环境故障。

根目录的`cpu-A/B.json`、`gpu-A/B.json`及`real-summary.json`是最初使用int64的真实探测结果。CPU通过，GPU实际运算报`NotImplementedError: addmm_cuda not implemented for Long`，规则保持不符合。随后将固定程序明确改为float32，并在任务快照记录dtype；新结果全部存入`float32-retest/`，没有覆盖原件。旧int64任务摘要不再是当前受支持模板，仅为首次失败留档。这是探测程序修复，不能称为学生电脑环境被修复。实际采集脚本为`run-real.py`，其中输出路径已改为新目录，首次执行和重试日志分别保留。

## 技术核对来源

2026-11-08读取PyTorch官方2.14文档，匹配本机2.14版本：

- [CUDA可用性](https://docs.pytorch.org/docs/2.14/generated/torch.cuda.is_available.html)：接口返回当前CUDA可用布尔值，不能单独证明实际运算成功。
- [设备属性](https://docs.pytorch.org/docs/2.14/generated/torch.cuda.get_device_properties.html)：按明确设备取得属性；本任务固定CUDA:0，并读取该对象UUID。
- [矩阵乘法](https://docs.pytorch.org/docs/2.14/generated/torch.matmul.html)：二维张量执行矩阵乘法。实际dtype/backend是否工作仍由固定程序运行核验。

本实现不安装、下载、修改环境或发AI请求。记录中的网络请求0表示采集脚本无网络/API调用，不是操作系统流量抓包结论。未测试CPU专用PyTorch构建、其他显卡、多个GPU设备或其他版本组合；这些分支只具备明确标注的构造协议测试。
