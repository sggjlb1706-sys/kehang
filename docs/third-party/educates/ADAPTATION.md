# Educates 教学动作模板适配说明

上游：educates/educates-training-platform，固定 d7e018f0cee382a595d2c9ecc6c938da099eb67e，Copyright 2020-2026 The Educates Authors，Apache-2.0。原LICENSE与NOTICE随此目录保留；manifest逐文件记录官方路径、上游Git blob、字节数和SHA256。

实际采用的是两个教学动作模板的字段与展示结构移植，属于**适配修改**，并非把上游后端或整个平台搬进产品。源 `actions/examiner-execute-test.html` 提取 name/title/description、默认cooldown=3，再交 `partials/clickable-action.html` 组织可点击的标题、正文、状态和动作参数。本项目在 `campuslab/teaching.py` 翻译为封闭教学步骤数据，保留这四字段及3秒冷却值，名称改绑已审查的固定检查ID；页面按当前任务和报告展示步骤，并引导本人重新采集。

原参数可携带args、autostart、retries等；已完整读其示例和后端 `modules/examiner.ts`。后端会按名称查找可执行文件、spawn程序、按退出码判成功。本项目将该分派改为已导入原始报告的确定性checks，不接受程序名、任意路径、shell、args、自动启动或无限重试。重试操作必须由本人按同任务/同组件的新报告触发，页面动作不会运行命令。四状态沿用主规则，不能用“动作完成”改写通过。

原两个HTML在此原字节保存用于核对，产品运行的是已标注修改和作者声明的Python适配；不运行Hugo、Express、Kubernetes、容器或上游脚本。01-basic-test.md、04-retries-and-delay.md和examiner.ts只作调用链审查留档，没有把其中的终端命令作为产品执行能力。

针对性验证：tests/test_teaching.py 对四状态映射、未知检查拒绝、额外args/任意shell名/非法cooldown拒绝作证；新场景网页、教师包和同目标复检的最终贯通结果由本轮浏览器记录与独立审查另行覆盖，不以本说明代替实测。
