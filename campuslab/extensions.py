"""Existing AI/tool content as reference guides, separate from course evidence."""

CHECKED = '2026-11-15'
COURSES = ('python-basics', 'node-basics', 'java-jdk', 'notebook-data',
           'sqlite-basics', 'pytorch-cpu', 'pytorch-gpu', 'vm-linux')


def section(title, *paragraphs, code=None):
    value = dict(title=title, paragraphs=list(paragraphs))
    if code:
        value['code'] = code
    return value


GUIDES = [
    dict(id='dsh-desktop', title='DSH 桌面版', group='Agent 工具',
         summary='安装桌面应用，选择工作区并开始使用 Agent',
         version='Windows 64 位桌面预览版；下载版本以官网为准',
         sections=[
             section('适合做什么', '在桌面应用中整理资料、处理文件或编写代码。选择你愿意让 Agent 接触的项目目录。'),
             section('获取与安装', '打开下方 DSH 官方入口，选择 Windows（64 位），下载后由你打开安装程序并按提示完成安装。桌面路线使用官方打包应用，不需要先照 CLI 路线安装系统 Node.js 或 Python。', '本轮核对了官方下载入口与公共项目资料，未重新安装桌面版；安装器的具体按钮及版本差异以你下载的界面为准。'),
             section('首次配置', '打开应用的设置，找到模型配置（Settings → Models）。若使用 DeepSeek，在对应提供方中填写你自己的 API Key 并保存，再在会话中选择模型。Key 在工具内填写，不发给课航。', '现有官方模型配置文档以 Web UI 为例；桌面版若菜单名称不同，请按当前设置中的模型项核对，不将文档画面当作本机实测。API Key 和调用费用按开放平台说明处理。'),
             section('选择工作区并使用', '通过工作区选择入口添加一个项目目录，选中它，再新建会话。可以先问“请概括这个目录的文件用途，先不要修改文件”。查看回复和工具操作详情，再按需要继续。', '涉及文件修改或命令执行时，逐次阅读工具的授权提示；按当前权限策略决定是否允许。课航不会替你发起 Agent 任务。'),
             section('常见问题', '不能发送：先看是否选中了工作区和可用模型。认证失败：回模型设置核对提供方和 Key；余额或限流按平台提示处理。工具报错：查看该次工具调用的错误与目录权限，确认后再重试。', '找不到 PATH 中的 dsh 不是桌面版安装失败的依据。需要命令行时再查看 DSH CLI 指南。'),
         ],
         sources=[('DSH 官方下载', 'https://www.deepseek.com/harness/'),
                  ('官方模型配置（Web UI，桌面菜单需按版本核对）', 'https://deepseek-harness.github.io/deepseek-harness/en/guide/providers'),
                  ('官方桌面打包运行时说明', 'https://raw.githubusercontent.com/deepseek-ai/deepseek-harness/master/apps/desktop/package.json')]),
    dict(id='dsh-cli', title='DSH CLI / Web', group='Agent 工具',
         summary='从终端启动 DSH，在浏览器中选择模型与工作区',
         version='官方仓库当前 package.json：0.2.2-rc.3，Node.js ≥24.9.0；npm 实际版本以安装时为准',
         sections=[
             section('必要准备', '需要已有 Node.js 与 npm、能访问 npm 的网络，以及一个你准备使用的项目目录。官方源码当前要求 Node.js ≥24.9.0；这是 CLI 前提，不套用到桌面版。', '在自己的终端查看版本；版本不足时按 Node.js 官方安装页选择满足要求的版本。', code='node --version\nnpm --version'),
             section('从官方包启动', '在 PowerShell 中进入准备使用的目录，再运行下方官方命令。npx 可能提示下载包，由你确认；课航只展示命令。启动后打开终端实际打印的本机 URL，默认是 http://127.0.0.1:3080。', code='npx @deepseek-ai/dsh web'),
             section('配置模型和工作区', '在 Web UI 的 Settings → Models 填写你自己的 DeepSeek API Key 并保存。模型配置对下一次请求生效，通常不需要重启。然后点 Choose workspace，添加并选中项目目录；未选工作区时会话输入不可用。', '模型调用按平台计费。只在工具设置中填写 Key；不要粘贴到课航或项目文件。'),
             section('基本使用与退出', '新建会话，可以先请求“列出这个项目的主要文件并解释用途”。查看回复与工具详情；按权限提示审查每次需要授权的操作。需要停止本机服务时，回到启动它的终端按 Ctrl+C。'),
             section('常见问题', 'npx 找不到：核对 Node.js/npm 安装和当前终端 PATH，安装后重新打开终端。版本错误：查看错误要求并升级到相容 Node。下载超时：先检查 npm 网络提示。端口被占用：核对当前已有服务，依据官方 CLI 帮助调整，不随意结束陌生进程。', '网页打开但不能发送：确认模型和工作区均已选择。不同预览版可能改变选项，以本次包的帮助和官方说明为准。'),
         ],
         sources=[('官方 npm 启动方式', 'https://github.com/deepseek-ai/deepseek-harness'),
                  ('官方 Web UI 操作', 'https://deepseek-harness.github.io/deepseek-harness/en/guide/quickstart'),
                  ('当前源码版本与 Node 前提', 'https://raw.githubusercontent.com/deepseek-ai/deepseek-harness/master/package.json'),
                  ('Node.js 官方下载', 'https://nodejs.org/en/download')]),
    dict(id='deepseek-api', title='DeepSeek API', group='API 与连接',
         summary='自行发起一次请求，读取响应并定位常见错误',
         version='官方 Chat Completions；当前入门示例模型 deepseek-flash',
         sections=[
             section('必要准备', '需要 DeepSeek 开放平台的 API Key、可用额度和能访问 API 的网络。网页聊天账号与 API 额度分别确认。下方使用 PowerShell 的 HTTP 命令，不要求安装 SDK。', '请求会把 messages 内容发送到 DeepSeek，并可能产生费用。决定调用后再执行示例；Key 只保存在你自己的终端会话中。'),
             section('在终端临时输入 Key', '在自己的 PowerShell 中输入下方命令，在安全输入框中填写 Key。该值只交给当前进程；关闭终端或按下方清理变量即可移除。不要把真实 Key 写进脚本、截图或课航。', code="$toolSecret = Read-Host 'DeepSeek API Key' -AsSecureString\n$env:DEEPSEEK_API_KEY = [System.Net.NetworkCredential]::new('', $toolSecret).Password"),
             section('发起请求', '核对目的地、模型和消息，再由你在终端运行。当前示例关闭思考模式，只请求一段简短文本，不要求固定数据产物。', code="$toolBody = @{\n  model = 'deepseek-flash'\n  messages = @(@{role='user'; content='请用一句话解释 API'})\n  stream = $false\n  thinking = @{type='disabled'}\n  max_tokens = 128\n} | ConvertTo-Json -Depth 5\n$toolReply = Invoke-RestMethod -Uri 'https://api.deepseek.com/chat/completions' -Method Post -Headers @{Authorization=('Bearer ' + $env:DEEPSEEK_API_KEY)} -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($toolBody))\n$toolReply.choices[0].message.content"),
             section('查看响应与清理', '正常响应的 choices[0].message.content 是回答文本；usage 可帮助了解本次用量。终端没有报错但没有回答时，展开响应核对 choices、finish_reason 和错误说明。', '示例结构仅说明字段位置，不是真实调用记录：{"choices":[{"message":{"content":"这里是模型回答"}}],"usage":{"prompt_tokens":12,"completion_tokens":16,"total_tokens":28}}。阅读示例不会发请求。', code="$toolReply.usage\nRemove-Item Env:DEEPSEEK_API_KEY\nRemove-Variable toolSecret"),
             section('处理错误', '400：核对 JSON 和字段；401：核对 Key；402：检查平台余额；429：降低请求频率并稍后重试；500/503：查看服务状态，稍后重试。连接超时先核对本机网络与目的地，不反复自动发送。', '模型名称不可用时查看官方模型列表。只摘录不含 Key 的状态码和错误内容寻求帮助。无需导入课程报告。'),
         ],
         sources=[('官方首次调用与模型名称', 'https://api-docs.deepseek.com/'),
                  ('请求字段与思考模式开关', 'https://api-docs.deepseek.com/api/create-chat-completion/'),
                  ('API Key 平台', 'https://platform.deepseek.com/'),
                  ('官方错误码', 'https://api-docs.deepseek.com/quick_start/error_codes/'),
                  ('模型与价格', 'https://api-docs.deepseek.com/quick_start/pricing')]),
    dict(id='ai-web-deepseek', title='AI 网页与客户端', group='日常使用',
         summary='从官方入口提问、追问和核对回答，网页无需安装',
         version='DeepSeek 为主；保留既有 Qwen、豆包参考入口',
         sections=[
             section('从哪里进入', '从 DeepSeek 官网点“和 DeepSeek 对话”进入网页版；网页不需要安装。客户端按官方应用下载页选择设备版本，下载页中的 Harness 桌面应用属于另一条 Agent 路线，见 DSH 桌面指南。'),
             section('首次使用', '在官方页面按当前条件注册或登录。若有地区、设备或账号限制，按该产品当时的说明处理。密码和验证码只在官方页面输入。', '本轮可核对官网链接及下载页；聊天登录页抓取返回 403，没有核实登录后的按钮、套餐或实际连接。Qwen 和豆包入口保留，但登录后操作也未实测。'),
             section('提问与追问', '新建对话后，描述目标、已有条件和希望的输出。例如：“我第一次接触 Notebook，请解释它和 Python 解释器的关系，给一个入门顺序。”收到回答后，选不懂的一点继续追问。', '涉及版本、安装命令或课程知识时，回到课程要求或官方资料核对。分享报错前删除 Key、账号、个人文件内容；不需要上传固定 CSV 或提交课程产物。'),
             section('客户端与其他入口', '需要手机使用时，从官方 DeepSeek 下载页选择 iOS 或 Android。既有 Qwen、豆包参考入口在下方；按各自页面操作，不将一家产品的账号或能力套用到另一家。'),
             section('常见问题', '无法登录或加载：确认官方网址、网络与官方服务状态。回答不准确：补充目标和限制，要求来源后自行核对。无法上传文件：以当前产品显示的类型和大小限制为准。网页使用不依赖课航环境报告。'),
         ],
         sources=[('DeepSeek 官网与网页入口', 'https://www.deepseek.com/'),
                  ('DeepSeek 官方应用下载', 'https://www.deepseek.com/download/'),
                  ('Qwen 官方入口（仅入口核查）', 'https://chat.qwen.ai/'),
                  ('豆包官方入口（动态页面，登录后未核查）', 'https://www.doubao.com/')]),
    dict(id='local-qwen', title='本地 Qwen 模型', group='本地模型',
         summary='准备 Qwen2.5 小模型，在本机加载并生成文本',
         version='沿用已有 Qwen2.5-0.5B-Instruct 示例，不新增模型或运行框架',
         sections=[
             section('用途与准备', '适合了解模型文件、分词器和本地文本生成。需要 Python、PyTorch、Transformers、足够磁盘与内存；先使用 CPU 小模型示例。PyTorch 课程的环境检测仍在课程区，本指南不据此判定模型已能运行。', '当前 Transformers 安装文档测试前提为 Python 3.11+、PyTorch 2.6+；Qwen2.5 的模型卡提示 Transformers 低于 4.37 会报 qwen2 错误。按你选用版本的兼容文档准备，不以旧课程版本作为唯一方式。'),
             section('准备独立环境', '在你准备存放示例的目录打开 PowerShell。下方为自行决定执行的参考；先确认已有 Python，下载依赖会使用网络和磁盘。', code='python -m venv .venv\n.\\.venv\\Scripts\\python.exe -m pip install torch transformers huggingface_hub'),
             section('获取模型文件', '先阅读 Qwen 官方模型卡和许可。在自己的目录创建 download_model.py，放入下方代码，然后用 .venv 中的 Python 运行。它将下载模型文件到当前目录的 qwen-model；课航不会下载。', code="from huggingface_hub import snapshot_download\nsnapshot_download('Qwen/Qwen2.5-0.5B-Instruct', local_dir='qwen-model')\n# 在终端执行：.\\.venv\\Scripts\\python.exe download_model.py"),
             section('加载并生成文本', '把下方代码保存为 run_model.py，放在 qwen-model 同级目录，再运行 .\\.venv\\Scripts\\python.exe run_model.py。示例只加载已有本地文件并在 CPU 上生成少量文本，不开放网络服务。', code="from transformers import AutoTokenizer, AutoModelForCausalLM\npath = './qwen-model'\ntokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)\nmodel = AutoModelForCausalLM.from_pretrained(path, local_files_only=True)\ninputs = tokenizer.apply_chat_template(\n    [{'role': 'user', 'content': '请介绍一下你自己'}],\n    add_generation_prompt=True, return_tensors='pt', return_dict=True)\noutputs = model.generate(**inputs, max_new_tokens=64)\nprint(tokenizer.decode(outputs[0][inputs['input_ids'].shape[-1]:], skip_special_tokens=True))"),
             section('常见问题与连接边界', '找不到文件：确认模型已完整下载，且终端当前目录与示例相同。KeyError: qwen2：核对 Transformers 版本。内存不足：关闭占用内存的程序并减少生成长度，仍不足时停止尝试；不承诺所有电脑都能运行。', '此示例是本地脚本，不提供 HTTP 接口，不能直接填作课航聊天地址。若你已有兼容 Chat Completions 的模型服务，可按“课航 AI 连接”指南填写该服务提供的完整地址。本轮未新增或启动模型服务。'),
         ],
         sources=[('Qwen 官方模型卡、许可与示例', 'https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct'),
                  ('Transformers 官方安装与离线加载', 'https://huggingface.co/docs/transformers/en/installation'),
                  ('PyTorch 官方安装选择', 'https://pytorch.org/get-started/locally/')]),
    dict(id='kehang-ai', title='课航 AI 连接', group='API 与连接',
         summary='为课航内的聊天面板配置已有模型接口',
         version='课航当前实现：Chat Completions 完整请求地址；不会自动加载 .env 文件',
         sections=[
             section('准备接口', '需要一个已有且可用的 Chat Completions 接口、模型名称，以及服务要求的 Key。远程地址必须是 HTTPS；本机服务可用 http://127.0.0.1 或 http://localhost。填完整请求地址，不只填域名。', '例如 DeepSeek 当前兼容地址是 https://api.deepseek.com/chat/completions，模型可参考官方当前的 deepseek-flash。使用其他已有本机服务时，地址与模型名按该服务实际配置填写。'),
             section('在启动终端设置', '先回到当前启动课航的终端按 Ctrl+C 停止这次服务。在新版本目录打开 PowerShell，设置下方变量。若接口需要认证，再按 DeepSeek API 指南的安全输入方式读取 Key，并赋给 CAMPUSLAB_AI_KEY；无需认证的本机服务跳过 Key。', code="$env:CAMPUSLAB_AI_URL = 'https://api.deepseek.com/chat/completions'\n$env:CAMPUSLAB_AI_MODEL = 'deepseek-flash'\n# 需要认证时，在当前终端安全输入：\n$toolSecret = Read-Host '模型服务 API Key' -AsSecureString\n$env:CAMPUSLAB_AI_KEY = [System.Net.NetworkCredential]::new('', $toolSecret).Password\n.\\Start-Web.ps1 -Port 8776"),
             section('确认配置并使用', '重新打开课航，点“问 AI”。“已配置”只表示服务进程识别到了地址和模型，尚未证明真实连接。输入问题后先点“预览发送”，核对目的地、上下文和历史，再点“同意并发送这条”。', '真正收到模型回复后再判断该次请求是否完成。远程服务可能收费；每轮仍需你主动同意，课航不因阅读本页而发送请求。课程指引与检测可以独立使用。'),
             section('常见问题与清理', '仍显示未连接：确认变量设置在启动课航的同一个终端，并已重启服务。404：核对完整接口路径；401：核对 Key；超时：核对网络与服务。当前课航禁止重定向，请直接填最终地址。', '停止服务并关闭启动终端会移除该会话变量；同一终端继续使用时，可用 Remove-Item Env:CAMPUSLAB_AI_KEY 删除不再需要的 Key。不要把密钥写进项目 .env.example。'),
         ],
         sources=[('课航当前配置与发送实现', 'local:campuslab/diagnosis.py'),
                  ('课航启动方式与示例配置', 'local:Start-Web.ps1,.env.example'),
                  ('DeepSeek 兼容接口说明', 'https://api-docs.deepseek.com/')]),
]

BY_ID = {guide['id']: guide for guide in GUIDES}
LEGACY = frozenset(BY_ID) - {'kehang-ai'}


def catalog():
    return dict(checked=CHECKED, guides=GUIDES)
