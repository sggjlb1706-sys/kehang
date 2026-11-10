# Java / JDK 固定课程验证

目标是明确JDK目录中的java.exe与javac.exe同源、版本符合固定演示要求，并实际编译运行本项目原创小程序。只调用目标bin中两工具，不用PATH的javac；清除JAVA_TOOL_OPTIONS、_JAVA_OPTIONS、JDK_JAVA_OPTIONS、JDK_JAVAC_OPTIONS和CLASSPATH注入，只在自己的临时目录写固定源码/类文件。

先写6项针对测试；`targeted-first-red.txt`首次因测试文件raw字符串尾部反斜杠导致SyntaxError。修正测试后，`targeted-red-after-test-syntax-fix.txt`确实因模块缺失失败，再实现后6项通过。两次失败原样保留，不能把语法错误说成产品或用户环境故障。

真实A/B在 `20261109T080945725345Z/`。显式目标 `C:\Program Files\Zulu\zulu-21`，java/javac均21.0.1，两工具各自通过-XshowSettings读取到相同java.home、分别记录二进制SHA。临时源码以-proc:none编译，退出0；所选java运行本次产物，退出0，输出42和相同java.home。A/B全部6项通过，保持JDK目录、两工具路径/SHA/home/版本及正确时间顺序。

真实命令由 `D:\ANACONDA\python.exe -B records\reuse-ai\notebook\run-real.py`触发；每次版本、编译、运行的参数列表保存在报告commands，不经过shell拼接。专用临时目录执行结束自动清理，不覆盖学生项目。故意不存在JDK的报告保留missing/unknown且commands为空，未借已安装PATH环境。其他版本、编译错误、不同home和替换二进制为明确构造测试，不冒称真实设备维修。

此任务的21.0至25.0以下为演示版本范围，不是所有学校要求。SQL、Hadoop、VM来宾等仍须各自证据，JDK通过不代表组合课程通过。

实施时核对Oracle Java21官方[java命令](https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html)与[javac命令](https://docs.oracle.com/en/java/javase/21/docs/specs/man/javac.html)，据其显式classpath、输出目录与环境变量语义实现。没有安装或下载JDK，没有复制上游Java业务代码。

仅本开发电脑真实运行，未测第二设备/独立新手/其他JDK组合。原始路径报告只供本人本机审阅。
