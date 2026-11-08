# 课程能力补全轮：独立代码初审

审查日期：2026-11-08（北京时间）。审查者未参与本轮实现，只读检查固定产品与证据；未改源码、测试或候选清单。本报告是初审原件，后续修复须另作提交和delta复核，不覆盖本文。

## 固定对象与结论

- 仓库：`C:\Users\DELL\Documents\ChatGPT\传智杯\work\competition-courses-20261108`。
- 指定与实际HEAD：`f8e9a13662da14ed14e74d91d81d984caa41bb66`。
- 最终候选：`records/review/courses-review-candidate.json`，654项。
- 候选文件SHA256：`E68878BA78FD37F062DAB263C15704C145604EBBF15A3564152B6D51D9C87A28`。
- 独立重算654项：缺失0、字节摘要不符0。审查开始时仅最终候选自身未跟踪。首次`courses-candidate.json`是未完成证据采集时的预冻结，不作本次依据，来源说明见`records/courses/freeze-note.md`。

**当前固定版本不能关闭独立验收：发现4项P2，另有1项P3。** 问题涉及GPU课程要求降级、无效CUDA构建被通过、AI预览个人路径脱敏及更换目标后残留旧环境安装指导。下面均有直接代码/内存构造或本机Edge复现；不把构造证据说成真实设备故障。

## P2-1：带空格的GPU硬要求会被CPU关键词静默降级

责任位置：`campuslab/preparation.py:56`、`:63`、`:73`。

独立原样调用：

```python
resolve_need('PyTorch老师要求 GPU 运行，我想先用 CPU')
```

实际返回`status='recognized'`、`scenario='pytorch-cpu'`，并且`constraints.gpu_required=False`。`深度学习课程要求 GPU，但我的电脑只能 CPU`同样识别为CPU。对照不带空格的`PyTorch老师要求GPU，但我没有GPU只能CPU`才返回冲突。

原因是硬约束匹配只识别`要求gpu/必须gpu/需要gpu`等紧邻字符串；随后任何CPU关键词优先选择CPU任务。用户明确课程要求GPU时，确认入口却提出CPU固定快照，违反“不以CPU成功替代GPU要求”和冲突需澄清的约定。

建议：规范空白或使用明确的约束匹配，先保留GPU硬要求，再处理本人CPU条件；冲突应澄清，不能仅按CPU关键词生成降级快照。新增带空格及同时提到CPU/GPU的反例。

## P2-2：任意非空字符串可被认定为CUDA框架构建

责任位置：`campuslab/torch_course.py:133`。

以本轮真实`records/courses/torch/float32-retest/gpu-B.json`为基准，仅在内存修改：

```python
report['facts']['gpu']['build'] = 'CPU-only'
analyze(task('pytorch-gpu'), report)
```

实际`torch:cuda-build='pass'`，整体`passed=True`。当前规则只判断字符串是否非空，不能把不可解释或明确错误的构建值保留为未知/不符合。`available`和实际GPU运算是其他独立项目，不能替代本项CUDA构建证据的有效性。

建议：只接受固定探测器所能给出的有效CUDA版本格式；空值按既定缺失/未知语义处理，无效版本保留非通过。保持真实`12.6`报告通过，并加入无效字符串反例。

## P2-3：AI预览在JSON转义后脱敏，Windows个人路径未被删除

责任位置：`campuslab/web.py:167`；调用的`campuslab/diagnosis.py:redact`针对原始路径字符串匹配。

独立启动临时本机AppServer，向`/api/preview`提交无报告文字：

```text
C:\Users\Alice\private.txt sk-abcdefghijklmnop
```

实际解析返回的`preview`后，`user_error`仍含完整`C:\Users\Alice\private.txt`；`Alice`未删除，而`sk-...`已删除。没有发送AI请求。原因是先`json.dumps`把反斜杠转义成双反斜杠，再在JSON文本上匹配原始Windows路径，个人目录规则无法命中。带报告的目标路径同样走此接缝。

建议：像分享接口那样先递归脱敏各字符串值，再序列化为可编辑JSON。补充真正解析预览后断言个人目录消失的测试，避免用未转义子串检查得到假通过。编辑与单次同意仍应保留，不能用人工检查代替已声明的基础脱敏。

## P2-4：更换课程目标后仍显示旧解释器的安装建议

责任位置：`web/app.js:22`与`:107`，旧指导在`:63`生成。

独立Edge在临时数据库执行以下构造路径：选择Python任务，导入由真实A报告改成缺requests/运行失败的明确构造报告；待`#remediation`出现目标A的pip建议，再把`#target`填写为`C:\NewCourse\python.exe`。

实际`state.before===null && state.analysis===null`为真，但`#remediation`文本与更换前逐字相同，仍有：

```powershell
& "D:\ANACONDA\python.exe" -m pip install "requests>=2.31"
```

当前选择已是新目标，页面仍指导向旧目标安装依赖，违反指导绑定显式环境的要求。`clearTask`会清理指导，但目标/模型/实例编辑仅调用`clearReports`，未清理这块报告派生操作。导入新的A失败也有相同陈旧指导风险。

建议：清理报告时同时移除报告派生的差异指导；新报告验证通过后再重新生成。针对更换目标、实例及无效A导入验证旧命令不残留。

## P3-1：延迟的教师发布响应会覆盖后来确认的课程

责任位置：`web/app.js:77`至`:82`。

独立Edge暂停`/api/course`发布响应；在等待期间改选并确认Node任务，然后交付原Python教师发布响应。实际`#goal='node-basics'`，但`state.task.scenario='python-basics'`，标题为旧发布任务。发布回调未核对任务代次，晚到的`chooseTask`反而清理了新任务。

此复现没有恢复旧报告成功，页面也能看见任务标题变化，因此列P3；但它会让用户当前操作转到过期任务。建议发布请求捕获epoch及表单版本，用户已切换目标时只保留发布结果/课程码，不能覆盖当前任务，并补充延迟响应测试。

## 独立验证结果与通过的约束

1. 实际运行`D:\ANACONDA\python.exe -B -m unittest discover -s tests`：65项通过，2.324秒，退出0。既有测试没有覆盖上述新增反例；测试总通过不抵消发现。
2. 重算最终浏览器三组证据：`20261108T103533580266Z`为Python/模型网页10组，`20261108T103534010672Z-node`为Node9组，`20261108T101444960811Z-courses`为新课程9组；状态均passed，各自产品源码SHA均与固定候选一致。没有把首次脚本折叠字段失败当作当前产品失败。
3. 独立内存删除174处必须字段：173处拒绝、1处保留非通过，未出现缺字段全部通过。另将六类原始报告不改字节交给其他五种任务，30组均拒绝。对Python、Node、PyTorch CPU/GPU及Qwen的相同/更早时间，10组复检均拒绝。
4. 额外探查明确修改报告`task_id`的攻击边界：真实GPU报告重标为CPU任务可满足CPU子集；这不等于未改动报告被跨任务接受，也不是远程真实性证明。本项目未提供报告签名/设备远程证明，手改任意报告内容不能视为真实采集。前述P2-2则是独立构建值本身错误被认定通过，须收紧语义。
5. 新任务验证采用封闭模板重算；重封摘要不能引入任意检测代码。教师课程包用内容一致性摘要，静态指导转义教师标题；文案明确摘要不是教师数字签名。原Python/Node/Qwen快照仍能按各自规则复算。
6. GPU框架、设备可用性、UUID与实际运算分列；缺少主动运算时GPU任务不通过，跨已知UUID不能复检。CPU成功未直接满足GPU必需项。固定探测只运行既定张量程序，不安装或联网。
7. VM固定只读VirtualBox/VMware命令、显式实例和手动来宾报告分层。软件通过不使实例/来宾通过；来宾任务、实例DMI UUID、machine-id摘要、时效和复检时间均参与核对。没有发现启动/创建VM、安装、改系统或网络的网页入口。VMware UUID字节序另对照Broadcom官方[Virtual Machine UUID Format](https://knowledge.broadcom.com/external/article/344089/virtual-machine-uuid-format.html)，与代码使用little-endian前三字段转换一致；这不代替真实来宾测试。
8. 硬件预检由本人手动CLI触发，独立于torch/权重；字段未知附原因。推荐返回`environment_passed=False`，4GiB提醒不是性能保证；固定本地任务不被云端建议提升为通过。候选目录明确未实现Notebook/JDK/数据库/Hadoop检测。
9. AI配置不输出服务端密钥；无明确布尔同意时不发送；无证据预览明确事实缺口。AI返回与规则判断分离，不执行建议、重试或跟随重定向。复检原件与脱敏交流副本用途分开。P2-3影响的是发送预览中的基础路径脱敏，不是密钥被读取或已发生外发。

## 适用限制和下一步

本次未重复真实GPU/模型推理、未实际运行Linux来宾、未取得第二电脑/实体手机或真实AI诊断，也未做官方登录上传、仓库公开或系统修改。设备结论使用原始报告/命令和当前源码复算，浏览器独立复现仅用于上述界面缺陷。技术PDF和最终交付回执尚未形成，不在654项初审结论中认证。

修复上述P2后须以新HEAD/SHA进行delta：直接复核原样反例、旧合法CPU/GPU与A/B报告、原三组浏览器/AI同意和教师携带流程；不得覆盖本报告、原候选、旧失败或虚构用户Bug反馈。整套赛事材料、三条完整Prompt链和官方资格均不由本代码审查认证。
