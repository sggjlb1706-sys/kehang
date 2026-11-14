# 第三轮固定提交独立只读审查

审查目标：579e8cfc2f8b161a818ab0b80b5b0f767fdacc29；基线60a7669b45ecd4ad6a9c54d5febc3b39ace325bc。
审查者未参与产品实现；未改产品文件。审查时产品文件相对固定提交无diff。只在data/temp创建验证脚本、隔离数据库和记录；无软件安装、真实模型/API调用、DSH/Agent/GPU执行、用户窗口操作或公网发布。

按仓库AGENTS读取TASK/PLAN/PROVENANCE；读取Impeccable与unslop SKILL、产品register与audit reference，context脚本正确定位此仓库。审查使用docs/第三轮设计审查.md既定方向，不重设方向。目视candidate欢迎/准备/教师和final教师、DSH准备、API窄屏准备、DSH CLI窄屏检测原图；未新增截图批次。

## 结论

无P0/P1阻断；1项P2范围问题。该问题不改变检测判定，不越过授权，但可令新课程的下一步错误地依据上一课程声明。

### P2 跨课程沿用准备声明

位置：web/app.js:53–54（chooseTask初始化）、95–96（传prepared），campuslab/guidance.py:186–190（使用声明与指导分流）。

亲自复现：欢迎→选DeepSeek API→在Python准备情况选择“尚未准备课程Python”→返回选课→首次进DSH桌面。DSH的prepared仍为missing，显示“先准备DSH桌面程序”及“本人说明尚未准备”，尽管未在DSH作此说明。反向选择installed同样被当作新路线声明。控件持久化是基线已有行为，但本轮新增专用下一步和“本人说明”使旧状态被套用到新课程。

建议：新任务进入时把prepared重置unsure，或按任务分别保存。最小修复为重置；保持报告与规则不变。

原始复现：data/temp/independent-r3-review/scope-repro.json。

## 亲自验证

- 7项contextual guidance单元测试通过。
- headless Edge检查75个页面/视口状态：1912×948、1366×768、768×1024、390×844、320×700；覆盖欢迎、主动展开AI、选课、API/DSH桌面/CLI准备、本机检测、手动备用、实训、实训准备、教师。无页面错误、横向溢出或外部请求。
- 主动展开AI后Escape返回入口焦点。关闭后迟到的预览与回答均被丢弃，不追加消息或重开；两者均为浏览器路由受控返回，不是真实AI效果。
- 教师表单5项输入均有可用宽度；切Node时Python字段隐藏，Node发布实际写入本次隔离数据库并成功返回。
- API/DSH无报告时准备声明明确“不是已验证事实”；专用检测的DSH不会显示Python选择模板，desktop目标为exe，CLI为node.exe。手动入口中的工具Python仅是包runtime备用，未被声明为DSH前置环境。
- 对比度扫描未检出正文失败。原始54条为▣装饰图标4.22:1，超过非文字图形3:1门槛；不作为问题。

原始检查：data/temp/independent-r3-review/review.json（passed只表示几何、请求、脚本错误通过，P2另见scope-repro）。

## 证据复核与限制

固定差异未改采集器/规则；新指导复用analyze的检查状态。单元证据区分未调用API、认证失败与通过；DSH静态软件证据不被当作Agent完成，桌面不额外要求系统Python/Node，CLI要求明确Node和包身份。

candidate的welcome-ai-390图因跨断点自动收起未实际展示AI，已向主控指出；主控计划在既定final批次补齐主动展开状态。不能仅凭旧图声称窄屏AI已目视。本人亲自进行的窄屏展开与几何检查另已通过。

未验证真实API响应、DSH模型连接或Agent任务、实体手机、真人满意/学习掌握；未把本次受控返回当作真实模型证据。

## 固定65de1c4修复复验

已只读复核65de1c4305ea4b194c7e8a584fe99cb8d28f8753。产品差异仅web/app.js:45在clearTask首行重置prepared='unsure'；未改采集器、规则、CSS或布局。另有截图采集修正和验收脚本。

亲自重做3条跨课程路线：API(missing)→DSH桌面、DSH桌面(installed)→CLI、CLI(missing)→API。均在新任务恢复unsure，状态为“本人尚不确定准备情况”，报告A/B为空。7项contextual单元测试再次通过。P2已关闭，最终没有未解决的P0/P1/P2发现。

新原始记录：data/temp/independent-r3-review/scope-final-65de1c4.json。

记录说明：第一次补验误用旧复现脚本，scope-repro.json被其同名写入覆盖成修复后结果；该修复后结果另存scope-fixed-65de1c4.json。原始P2复现的真实观察保留在本报告上方及审查者当时协作消息/工具输出，不能把覆盖后的scope-repro.json当作原始失败日志。

已亲自目视主控修正的final/welcome-ai-390.png：显示主动打开的AI、输入焦点、收起入口与可读状态。漏拍问题已解决，旧漏拍图被保留并命名为before-capture-correction，不列作产品问题。未新增设计截图轮次。
