# 本版来源

2026-11-14第三轮由60a7669b45ecd4ad6a9c54d5febc3b39ace325bc完整独立克隆到D盘work/kehang-round3-20261114，分支codex/kehang-round3-20261114，固定产品65de1c4。原反馈与截图未改写；第二张图为API而非DSH。复用既有任务、固定采集器、analyze/compare、guidance与原UI交互，不升级课程版本、模型或判定。本轮共享样式与呈现逻辑为课航代码；使用Impeccable和unslop指导，unslop作者Damir Sokolovsky（https://x.com/heydamir），CC BY 4.0，流程适配署名保留在设计/验收说明。无新依赖、外部字体、图片、图标或自动部署；官方资料核对路径、真实/模拟/缺口和独立发现各自记录。

2026-11-14第二轮从a7aba975aa1d59e4a86f6df7803ed59ad4c97dd7完整独立克隆，位于D盘work/kehang-round2-20261114，分支codex/kehang-round2-20261114。需求为本人14:26反馈及当前执行任务；原件保留records/round2/original-feedback。欢迎页、页面AI规则与目标票据为本轮原创，复用现有13类课程定义、固定采集器、analyze/compare、原生文件选择与Windows Job Object。无第三方新代码、框架、字体、图片或云素材。Impeccable用于UI；Lean Build与Migration用于接入和兼容。测试、受控候选、真实采集、模拟端点和独立代理审查分别记录，不能把测试夹具当真实模型或用户验收。

2026-11-14课程首页与上下文聊天从Windows11图示交付版4249165继续开发，实际目录仍在D盘开发工作区，分支codex/kehang-course-chat-20261114。需求来自本轮用户关于课程可见性、连续提问和操作层次的反馈，原文见records/course-chat/feedback.md；用户明确没有报告具体Bug。首页、侧栏和会话票据为本仓库原创实现，复用原课程加载、guidance、analyze、脱敏及HTTP模型协议，不新增依赖、外部字体、图标或图片素材。impeccable用于产品界面与响应式检查。新增模型对话仅用本地HTTP协议夹具验证，不能作为真实模型效果或接入成功的证据；Python A/B另有本机真实执行原件。浏览器回归发现的缩屏遮挡由本轮实现者发现并修正，不记作用户首先发现。

Windows11全课程图示版从11e52b4f7361dd4efd1453b3b47240650fb74225完整克隆，58个已有可达提交，分支codex/kehang-win11-guides-20261113。用户本次原文见records/win11-guides/feedback.txt。参考[Microsoft文件资源管理器说明](https://support.microsoft.com/en-us/windows/experience/fileexplorer/file-explorer-in-windows)及[Windows可访问性说明](https://learn.microsoft.com/en-us/windows/apps/develop/accessibility)，在2026-11-13核对导航/查看扩展名与键盘原则；所有产品图示、文件图标和布局由本版HTML/CSS自制，无第三方截图/图标再分发。官方参考图仅放仓库外交付目录reference供核对，不打入产品和评审包。沿用impeccable的产品界面/上下文引导工作流，没有新依赖或云端素材调用。


报告位置图示版从f398ad5c006f9ef177589831f31bb7693561c129完整克隆，继承56个可达提交，分支codex/kehang-report-guide-20261112。依据用户2026-11-12本次原文与三张附件（records/report-guide/feedback）做局部引导修改。图示为课航HTML/CSS自制的地址栏/文件列表，并非用户文件系统扫描或现场截图；用户截图原件未改写。没有采用新第三方资源或安装。延用impeccable产品界面和上下文引导原则，实际测试区分本机真实Node A/B、旧Python原件与受控剪贴板拒绝。独立审查发现不得改写为用户首先发现。

一键本机检测版从正式路径引导版3b595f476c89a8390396cb3a78beb3fb27aca50d完整克隆，继承53个可达提交；独立分支codex/kehang-local-check-20261112。依据用户“想让AI直接进行本地检测”及明确选择“改成课航内一键本机检测”，将原手动限制仅在Python基础固定检查处调整，见AGENTS.md。没有重新开发规则、课程或实训；复用原PEP514/PATH发现、collect/probe、analyze/compare和AI预览同意流程。

进程管理使用Windows标准Job Objects，经ctypes调用，固定包装器等待父进程将它加入私有Job后才运行检查；关闭Job清理本次子进程。参考[Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)及其AssignProcessToJobObject、SetInformationJobObject官方说明。此前taskkill在受限进程环境出现拒绝访问，已弃用；负例与修正记录见本轮验收说明。没有新增第三方库、模型依赖、网络服务或开源代码复制。实际A/B、受控UI负例和同机代理审查分别记录，不冒充独立真人试用。

路径引导版从ffdeca5900218dd7f2911c43a1a5ce2578ccba4c完整克隆（51可达提交），分支codex/kehang-path-help-20261111。当前用户第二次具体反馈及两张附件在records/path-help/feedback。新增代码是课航自己的入口改进；按[Python PEP514](https://peps.python.org/pep-0514/)读取Windows安装登记，PATH只提供候选；使用Windows已有PowerShell与[.NET OpenFileDialog](https://learn.microsoft.com/en-us/dotnet/api/system.windows.forms.openfiledialog)提供用户主动文件选择。没有安装新依赖、改写Python安装登记或更改执行策略，或在选择前执行候选Python。模板为固定脚本，路径通过JSON传递，不拼接为脚本。

2026-11-11引导版从已交付实训版451d7b9a1f8a72440cabff82acf2163c53bf15ed完整克隆，继承45个可达提交；新分支codex/kehang-guided-20261111。UI反馈来自当前用户明确提出的首页混乱、下载选项不知如何选择、希望逐步下一步的原文和两张附件。记录见records/guided/feedback，不将本轮执行者发现的导航/B阶段问题改写成用户首先发现。没有新增框架、外部字体、图片资源、软件安装或模型请求；颜色延续原课航。

从正式课航版 a7dac52bfacf379dd13f1fe1a2d3120570e05532 独立克隆，保留 39 个已有提交。1844 项交付内容的逐项核对见 records/practice/baseline.json。新分支 codex/kehang-practice-20261110 的提交按实际工作形成。

课堂资料复用课航已有原创三行 CSV 和 SQLite 固定查询，沿用 notebook-data、sqlite-basics 两个原任务身份。新增课堂包、练习模板、声明与确定性核验由本版开发。已采用的 Educates 两个教学模板仍按原上游 Apache-2.0 记录在 docs/reuse.json 和 THIRD_PARTY_NOTICES.md。新增 DSH 公开 ASAR 元数据读取属于本地接口适配。

工具运行时沿用基线官方嵌入包，哈希见 DEPENDENCIES.md。媒体采用本机课航操作、脱敏协作原文、Git 差异和实际练习文件。来源、首次失败、测试负例和真人缺口分别保留。完整旧来源可用 git show a7dac52:PROVENANCE.md 查阅。
