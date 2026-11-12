# 本版来源

路径引导版从ffdeca5900218dd7f2911c43a1a5ce2578ccba4c完整克隆（51可达提交），分支codex/kehang-path-help-20261111。当前用户第二次具体反馈及两张附件在records/path-help/feedback。新增代码是课航自己的入口改进；按[Python PEP514](https://peps.python.org/pep-0514/)读取Windows安装登记，PATH只提供候选；使用Windows已有PowerShell与[.NET OpenFileDialog](https://learn.microsoft.com/en-us/dotnet/api/system.windows.forms.openfiledialog)提供用户主动文件选择。没有安装新依赖、改写Python安装登记或更改执行策略，或在选择前执行候选Python。模板为固定脚本，路径通过JSON传递，不拼接为脚本。

2026-11-11引导版从已交付实训版451d7b9a1f8a72440cabff82acf2163c53bf15ed完整克隆，继承45个可达提交；新分支codex/kehang-guided-20261111。UI反馈来自当前用户明确提出的首页混乱、下载选项不知如何选择、希望逐步下一步的原文和两张附件。记录见records/guided/feedback，不将本轮执行者发现的导航/B阶段问题改写成用户首先发现。没有新增框架、外部字体、图片资源、软件安装或模型请求；颜色延续原课航。

从正式课航版 a7dac52bfacf379dd13f1fe1a2d3120570e05532 独立克隆，保留 39 个已有提交。1844 项交付内容的逐项核对见 records/practice/baseline.json。新分支 codex/kehang-practice-20261110 的提交按实际工作形成。

课堂资料复用课航已有原创三行 CSV 和 SQLite 固定查询，沿用 notebook-data、sqlite-basics 两个原任务身份。新增课堂包、练习模板、声明与确定性核验由本版开发。已采用的 Educates 两个教学模板仍按原上游 Apache-2.0 记录在 docs/reuse.json 和 THIRD_PARTY_NOTICES.md。新增 DSH 公开 ASAR 元数据读取属于本地接口适配。

工具运行时沿用基线官方嵌入包，哈希见 DEPENDENCIES.md。媒体采用本机课航操作、脱敏协作原文、Git 差异和实际练习文件。来源、首次失败、测试负例和真人缺口分别保留。完整旧来源可用 git show a7dac52:PROVENANCE.md 查阅。
