# DeepSeek Harness课程：实现、构造测试与真实盘点

固定上游`fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159`，桌面/CLI版本`0.2.2-rc.1`。官方`apps/cli/package.json`为`@deepseek-ai/dsh`、入口`lib/bin.js`、Node `>=24.9.0`；桌面README明确自带Electron运行时和可选命令注册。因此桌面报告没有外部Node缺失项，CLI则只运行本人明确选定的Node固定身份表达式，移除NODE_OPTIONS/NODE_PATH，不运行DSH包入口、npx、完整配置转储或模型。

## 真实开发记录

前代理实际先写了DSH与教学适配两组测试，模块尚不存在；`targeted-first-red.txt`原样保留两个导入失败。接手实现后`targeted-after-implementation.txt`为13项通过，增加未完成证据模板不得成功后`targeted-with-template.txt`为14项通过。这些是构造/单元测试，不是实际DSH Agent执行。正例使用明确的fixture程序文件、patched PE/Node元数据和构造最小摘要；不能移作真实安装、登录、工具调用或模型证据。

代码分别记录软件/包、运行时、专用目录、公开模型标识、本人权限、工具摘要和本机JSON产物。DSH工具摘要必须严格绑定当前任务、程序/包SHA、所选Node、模型、目录UUID和产物；只接受固定read input.csv及write summary.json、正确时序和30分钟内证据。`protocol-simulation`不能令实际调用项通过。只有本人提供的本次DSH工具摘要与固定产物核验共同满足才能通过，并明确该依据不是远程真实性证明。产物本身、版本号或“已完成”文字均不足以全部通过。

## 本机实际只读预检

命令（工作目录是本轮独立仓库）：

```powershell
& 'D:\ANACONDA\python.exe' -B 'records\reuse-ai\dsh\run-metadata.py'
```

该次实际结果在`real-metadata/`及`real-metadata-command-output.txt`：

- 桌面开发者选择的标准候选`C:\Program Files\DeepSeek Harness\DeepSeek Harness.exe`不存在；软件missing，其余任务项unknown，无Node检测项。
- 明确选择既有`D:\Program Files\nodejs\node.exe`，固定表达式实际返回相同execPath、Node24.21.0，满足DSH CLI引擎；明确包位置`D:\Program Files\nodejs\node_modules\@deepseek-ai\dsh\package.json`不存在，软件missing。没有借用PATH中其他Node/npm或软件包。
- 两条路线各采A/B并核对同组件身份，均不通过。没有选择练习目录/模型，没有取得实际授权、工具回合或产物，相关项保持unknown。

这里只探测开发者明确列出的候选位置，不是全机安装扫描；`Get-Command dsh`未得到命令和标准路径缺失均不能证明所有位置的桌面应用不存在。没有读取任何DSH凭据/会话或发模型请求；没有实际DSH启动和Agent任务成功。

## 固定练习与本人最短后续操作

下载当前任务工具，使用工具Python或已有Python手动运行（PATH换成本人选择的尚不存在专用目录）：

```powershell
python -B -m campuslab.dsh_course --task task.json --prepare-workspace PATH
```

它只创建固定input.csv、目录标识、课程说明和**未完成**evidence-template.json，拒绝覆盖既有目录；不启动DSH。`prepare-cli-smoke.txt`是本轮实际CLI创建新测试目录的烟测输出，文件落在本轮ignored的`records/runtime/dsh-prepare-cli-smoke-20261109`；没有Agent产物。模板的时间/工具/模型结果和confirmed字段初始均未完成，不能直接通过。

本人已有合法可用的DSH后，选择软件、公开提供方/模型和专用目录；在DSH本人明确授权仅read input.csv/write summary.json工具，完成整数count=3、sum=42的小练习。不要授权终端、网络或其他文件操作。保留本次必要工具记录和实际产物，勿导出无关聊天、隐藏推理或任何凭据。

先用不带工具摘要的采集报告取得实际安装/运行时/模型/目录/产物身份，再运行：

```powershell
python -B -m campuslab.dsh_course --task task.json --template-from-report report-A.json --output evidence-bound.json
```

本人只按DSH实际记录填写含时区的start/end、固定相对路径的工具时间/状态及实际模型结果，确实授权才填confirmed=true；模板身份不改变。随后采集时通过`--agent-evidence evidence-bound.json`导入本人摘要，保存新原始报告。DSH实际复检须重新取得较晚工具/产物证据，重复旧摘要会拒绝；换路线、程序/包/Node、提供方/模型或目录也须重新初检。

当前缺少的是本人明确选定的已安装DSH及合法模型条件、本次启动/工具授权和必要实际运行证据。程序实现、协议测试或只读盘点不替代这些条件；其缺失不阻塞其他课程开发。
