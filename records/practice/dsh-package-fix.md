# DSH桌面PE prerelease误判：真实反例与最小修复

2026-11-10。由材料核对代理发现并实现，不是用户Bug反馈，不是独立审查结论。

明确所选真实安装 `D:\deep seekharness\DeepSeek Harness.exe` 可读取PE ProductName=DeepSeek Harness、ProductVersion=0.2.2.0。相邻resources/app.asar内根package.json的公开name/version/main实际为 `@deepseek-ai/dsh-desktop`、`0.2.2-rc.1`、`lib/main.js`。旧采集器仅拿PE文本与SemVer prerelease逐字比较，软件层误判mismatch，前后真实报告在 `dsh-installed-A/B.json`，未覆盖。

先增加针对测试并真实运行：`dsh-package-red.txt`为2失败+1错误（缺新元数据字段）；首次测试夹具把subprocess全局替换影响platform缓存的错误另保留 `dsh-package-first-harness-error.txt`。修正夹具只固定Windows平台事实后才取有效red，不把夹具错误说成产品Bug。

补丁只修改 `campuslab/dsh_course.py`。保留原任务ID和PE事实；可选桌面包字段记录固定相邻ASAR路径、完整ASAR SHA、根package SHA和公开身份。读取头限制8MiB、package限制64KiB；校验pickle长度、固定根package项、偏移/文件边界与SHA256完整性；拒绝link/unpacked/额外文件字段、重复JSON键、错误name/version/main，不读取配置、凭据或会话。仅PE0.2.2.0不能通过；必须同时有严格匹配的受支持桌面包。读取前后整包SHA一致，复检及新工具摘要绑定其身份。旧无扩展报告继续可分析；跨旧未知包与新已知包应重新初检。

ASAR格式只参考[Electron官方磁盘读取源码](https://github.com/electron/asar/blob/main/src/disk.ts)与[完整性字段源码](https://github.com/electron/asar/blob/main/src/integrity.ts)，本补丁为独立有限读取实现，没有复制上游执行器或引入依赖。ASAR包内完整性不是数字签名，也不认证发行者、实际启动、模型连接或工具执行。

`dsh-package-green-final.txt`：新增8项与原11项DSH测试共19项通过，含wrong name/version、完整性篡改、路径借用、超界/巨大头/偏移、包身份变更和摘要绑定。修复后当前真实静态A/B存 `dsh-installed-fixed-A/B.json`、comparison；软件层pass，整体仍incomplete，模型/本人权限/工具/成果均unknown。只读取明确安装的公开元数据和必要摘要，没有启动DSH/VM、安装、读取密钥或发送模型请求。
