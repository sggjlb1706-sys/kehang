# 新手引导版补充复核

2026-11-11，固定提交bcb6bb44576cfe04a647f7b7b5997fc31a00a034。原初审两项与教师发布第二阶段问题均通过独立复核，执行者12组浏览器回归在此Git快照重新执行通过。慢配置保留主动填写的目标或summary开启选择，无运行时备用入口可用，单项/实训包取消及成功后可再次选择。

另在相邻需求识别流程实际发现一项P2：初次/api/need尚未返回时，用户点击学习首页，迟到的error_help结果仍会打开诊断面板并scrollIntoView，实测route维持home但scrollY从0变320。第二阶段也受影响：识别“我想学Python”得到候选后，暂缓确认候选的第二次/api/need，点击首页再放行；实测home/epoch2变为course/epoch3。两者均只核needEpoch，没有核用户导航代次。

两阶段应分别记录其实际启动时的导航代次，响应后在显示或选择任务之前检查。候选确认不能简单复用更早识别请求的导航代次，否则用户返回后主动点击已显示候选也可能被误拒。此问题由独立审查者新增发现，不是用户反馈。

证据：independent-bcb6bb4/independent-result.json和late-need-help.png；need-phase2-bcb6bb4/result.json及after.png。教师修复正例另见teacher-phase2-bcb6bb4/result.json，其route与epoch都保持home/2。

本报告仅保留当前实际闭合与新反例；等待新冻结提交复核，不能提前写0阻断。所有验证使用临时产品、临时库与本机服务，没有修改产品、模型调用、安装、DSH或外部设备操作。
