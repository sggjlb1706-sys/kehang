# 虚拟机 / Linux 课程证据（2026-11-08）

本目录区分真实宿主盘点、构造协议测试与尚不可取得的来宾证据。没有安装、下载镜像、创建/启动虚拟机、修改BIOS/系统/网络或使用来宾口令。

## 已实现

`campuslab/vm_course.py` 固定 `vm-linux` 演示任务：Windows宿主身份与CIM虚拟化条件、明确选择的VirtualBox或VMware工具、明确实例及手动Linux来宾报告。教师或自主入口可以共享同一固定任务摘要。演示版本范围是本项目配置，不是学校统一要求或全版本兼容承诺；VMware显示的是 **vmrun CLI版本**，并非Workstation产品版本。

工具只允许以下固定只读调用，所有参数以列表传递，不拼接用户命令：

- VirtualBox：`VBoxManage.exe --version`、`list vms`、`showvminfo <所选UUID> --machinereadable`。
- VMware：`vmrun.exe` 无参数读取帮助/版本；`vmrun.exe -T ws list`仅列当前运行实例。用户明确选择的`.vmx`只读解析`uuid.bios`、`guestOS`和`displayName`，不运行配置内容。
- 宿主：固定CIM查询；MachineGuid只保存SHA-256，不输出原值。

`guest_probe.py`可作为单一文件手动复制到Linux来宾执行。它不发起网络、安装或修改系统；只读DMI实例UUID及machine-id（后者仅输出摘要），运行固定`/bin/uname -s`和Python固定求和。通过这些证据只表示演示环境验证，不宣称XV6、数据库或任意课程作业完成。

示例命令须由本人核对并在所选来宾中执行：

```sh
python3 guest_probe.py --task-id '<网页当前任务SHA256>' --vm-id '<同一VirtualBox UUID或Windows .vmx绝对路径>' --output guest-A.json
```

`.vmx`路径在Linux终端应使用单引号保护反斜杠；路径含单引号时须按终端的字面值规则转义。手动传回文件后，宿主采集器接收该JSON。来宾报告须与当前任务、实例UUID和所选路径匹配，DMI/machine-id缺失保留未知。证据有效期为本演示明确规定的30分钟；复检须较晚的宿主和来宾证据。DMI和文件摘要是本机报告关联手段，不是不可伪造的远程证明。

## 真实实测

`actual-summary.json`与对应原始报告来自当前沙箱环境：VirtualBox标准安装路径不存在；已装VMware的`vmrun 1.17.0 build-24832109`可读；固定`list`返回0个运行实例；CIM查询权限不足保留未知。

`actual-elevated-summary.json`与对应原始报告来自经工具自动批准的只读提权复核：成功取得原始CIM值，`HypervisorPresent=true`，三项处理器旗标为false。已有Hypervisor时这些旗标可能不能证明底层固件状态，规则仍保留未知，不将其描述为已关闭BIOS虚拟化。VMware固定list仍为0运行实例。没有选定可读`.vmx`或VirtualBox UUID，也没有来宾实测；不能把软件通过写成课程通过。

另用`D:\ANACONDA\python.exe -B records/courses/vm/real-host-retest.py`对同一VMware目标执行真实B采集，并通过现有统一`rules.compare`复算：结果`incomplete`，实例和来宾未知保持未知。A/B、比较和当时源码SHA分别保存在`vmware-actual-retest-B.json`、`vmware-actual-retest-comparison.json`和`real-collector-source-sha256.json`。脚本不是网页自动执行入口。

第一次调查曾误用`vmrun -v`；该版本不接受此参数，仅输出无效参数和帮助。后续实现改用无参数帮助读取版本；实际帮助退出码`4294967295`保留原值，规则明确识别这一帮助行为，没有伪写成退出0。`vmrun-invalid-v.*`为该失败的另次复现原始输出，不冒称首次终端输出文件。

## 测试

`first-red.txt`记录模块尚未实现时导入失败；`first-green.txt`记录最初10项测试通过；`final-targeted-tests.txt`记录扩充后的12项通过。构造测试覆盖双提供方四状态、缺失来宾/宿主未知、虚拟化旗标屏蔽、跨实例/宿主/来宾身份、旧来宾报告重用、时间与任务绑定、错误类型、篡改任务、固定只读命令和`.vmx`UUID解析。这些均非真实Linux来宾验证。

## 官方技术来源

- [Oracle VirtualBox 7.2：VBoxManage命令参考](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/vboxmanage.html)：列出注册实例和读取实例机器格式信息。2026-11-08查阅。
- [VMware Workstation Pro 17官方用户指南](https://techdocs2-prod.adobecqms.net/content/dam/broadcom/techdocs/us/en/pdf/vmware/desktop-hypervisors/workstation/vmware-workstation-pro-17-0.pdf)：`vmrun list`列出运行中的虚拟机。2026-11-08查阅；当前本机CLI版本和行为以原始输出为准。
- [哈工大深圳虚拟机实验环境使用指南](https://oslabs.hitsz.edu.cn/vm_env.html)：课程使用VirtualBox和Ubuntu来宾，强调宿主虚拟化检查。该校实验具体版本、磁盘数字和XV6验收不自动成为本演示要求。
