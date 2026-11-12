"""User-started bundle entry for the Python and Notebook fixed collectors."""
import json
import base64
import os
from pathlib import Path
import shutil
import subprocess

from .collect import collect
from .rules import absolute, validate_task


PATH_HELP = '''不知道 Python 在哪里？
1. 在选择提示处直接按回车或输入 L：只读取 Windows 的 Python 注册信息和 PATH 候选，不运行这些程序。
2. 按列表编号选择课程使用的 Python。候选尚未检测；有多个时，请对照老师要求或编辑器当前选择的环境，不要凭编号猜。
3. 列表没有时输入 F，打开文件窗口，选择安装目录中的 python.exe。没有登记不代表没有安装。
怎么找到安装目录：在开始菜单搜索 Python，右键“打开文件所在的位置”；若看到快捷方式，再右键“属性”查看“目标”，找到它所在目录中的 python.exe。
Anaconda 用户：打开课程使用的 Anaconda Prompt，在该终端手动输入 python -c "import sys; print(sys.executable)"，将输出的整行路径复制回本窗口。
已经知道路径：可直接粘贴，或把 python.exe 拖入本窗口，带双引号也可以。不要只选文件夹，不要选检测包内 runtime/python.exe。
完全没有安装 Python：回网页上一步，选择“还没安装”查看官方准备指引；本工具不代装。
Notebook 还需 kernel.json：在课程 Python 对应的终端手动运行 python -m jupyter kernelspec list，找到与笔记本所选内核对应的目录，再选择其中的 kernel.json；不能把 python.exe 当内核文件。
输入 Q 退出。本次选择、浏览和查看帮助都不会开始课程检测；最终核对任务/路径并输入 START 后才开始。
'''

FILE_DIALOG_SCRIPT = r'''
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$settings = [Console]::In.ReadToEnd() | ConvertFrom-Json
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
try {
    $dialog.Multiselect = $false
    $dialog.CheckFileExists = $true
    $dialog.RestoreDirectory = $true
    $dialog.InitialDirectory = $settings.directory
    if ($settings.kind -eq 'python') {
        $dialog.Title = '选择课程 Python：python.exe（不要选包内 runtime）'
        $dialog.Filter = 'Python 程序 (python*.exe)|python*.exe'
        $dialog.FileName = 'python.exe'
    } else {
        $dialog.Title = '选择所选 Notebook 内核目录中的 kernel.json'
        $dialog.Filter = 'Jupyter 内核定义 (kernel.json)|kernel.json'
        $dialog.FileName = 'kernel.json'
    }
    if ($dialog.ShowDialog() -eq [Windows.Forms.DialogResult]::OK) {
        @{ selected = $dialog.FileName } | ConvertTo-Json -Compress
    } else { @{ selected = $null } | ConvertTo-Json -Compress }
} finally { $dialog.Dispose() }
'''


def _registered_python():
    """Read only the bounded PEP 514 registration locations, on user request."""
    import winreg as reg
    found=[]
    for hive,view in [(reg.HKEY_CURRENT_USER,0),(reg.HKEY_LOCAL_MACHINE,reg.KEY_WOW64_64KEY),(reg.HKEY_LOCAL_MACHINE,reg.KEY_WOW64_32KEY)]:
        try:
            with reg.OpenKey(hive,r'Software\Python',0,reg.KEY_READ|view) as companies:
                for i in range(min(reg.QueryInfoKey(companies)[0],64)):
                    company=reg.EnumKey(companies,i)
                    if company.casefold()=='pylauncher':continue
                    try:
                        with reg.OpenKey(companies,company) as tags:
                            for j in range(min(reg.QueryInfoKey(tags)[0],64)):
                                tag=reg.EnumKey(tags,j)
                                try:
                                    with reg.OpenKey(tags,tag+r'\InstallPath') as install:
                                        try:path=reg.QueryValueEx(install,'ExecutablePath')[0]
                                        except FileNotFoundError:
                                            directory=reg.QueryValueEx(install,'')[0]
                                            if not isinstance(directory,str):continue
                                            path=str(Path(directory)/'python.exe')
                                        if isinstance(path,str):found.append((path,'注册信息 '+company+'/'+tag))
                                except OSError:continue
                    except OSError:continue
        except OSError:continue
    return found


def _path_file(root,kind,value):
    candidate=Path(selected_path(value))
    if candidate.is_dir():raise ValueError('你选的是文件夹。请进入文件夹，选择 python.exe 或 kernel.json 文件。')
    expected=('python.exe','python3.exe') if kind=='python' else ('kernel.json',)
    if candidate.name.casefold() not in expected:raise ValueError('请选择 '+('python.exe（不是快捷方式或 pythonw.exe）' if kind=='python' else 'kernel.json（不是 python.exe）'))
    if not candidate.is_file():raise ValueError('这个文件不存在或无法读取。请重新选择，或输入 ? 查看查找步骤。')
    if kind=='python':
        if candidate.resolve().is_relative_to((root/'runtime').resolve()):raise ValueError('这是包内 runtime，不是课程 Python。请另选课程安装目录中的 python.exe。')
        if candidate.parent.name.casefold()=='windowsapps' and candidate.parent.parent.name.casefold()=='microsoft':
            raise ValueError('这是 Windows 应用执行别名。请另选实际安装目录中的 python.exe。')
    return str(candidate)


def discover_python(root):
    entries=_registered_python()
    path=shutil.which('python.exe')
    if path:entries.append((path,'PATH 候选'))
    choices=[];seen=set()
    for path,source in entries:
        try:target=_path_file(root,'python',path)
        except (ValueError,OSError):continue
        key=str(Path(target).resolve()).casefold()
        if key not in seen:choices.append((target,source));seen.add(key)
    return choices


def choose_file(kind,directory):
    powershell=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
    encoded=base64.b64encode(FILE_DIALOG_SCRIPT.encode('utf-16le')).decode('ascii')
    result=subprocess.run([str(powershell),'-NoLogo','-NoProfile','-STA','-WindowStyle','Hidden','-EncodedCommand',encoded],
                          input=json.dumps(dict(kind=kind,directory=str(directory)),ensure_ascii=False).encode('utf-8'),capture_output=True,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:raise OSError('文件选择窗口不可用')
    try:return json.loads(result.stdout.decode('utf-8-sig').strip())['selected']
    except (ValueError,KeyError,TypeError) as exc:raise OSError('文件选择窗口未返回有效结果') from exc


def choose_path(root,kind,ask=input,tell=print,directory=None):
    choices=[];label='课程 Python' if kind=='python' else 'Notebook 内核 kernel.json'
    tell('\n选择'+label+'。不知道路径也没关系：')
    tell(('直接按回车/L：列出候选并用编号选择；' if kind=='python' else '')+'F：浏览选择文件；?：查看详细查找步骤；Q：退出。也可粘贴或拖入完整路径。')
    while True:
        answer=ask(label+'（回车列出 / F浏览 / ?帮助 / Q退出）：' if kind=='python' else label+'（F浏览 / ?帮助 / Q退出）：').strip()
        if answer.upper()=='Q':return None
        if answer=='?' or (not answer and kind!='python'):
            tell(PATH_HELP);continue
        if kind=='python' and answer.upper() in ('','L'):
            choices=discover_python(root)
            if not choices:tell('未找到已登记的候选，这不代表没安装。输入 F 浏览文件，或 ? 查看查找方法。')
            for i,(path,source) in enumerate(choices,1):tell(str(i)+'. '+path+' ['+source+'；未检测]')
            if choices:tell('输入编号选择。列表只表示找到了文件，不能据此认定版本或依赖通过。')
            continue
        if answer.upper()=='F':
            try:answer=choose_file(kind,directory or Path.home())
            except OSError:tell('文件窗口无法打开。可用 L 列出 Python，或输入 ? 查看手动查找方法。');continue
            if not answer:tell('已取消文件选择，还没有开始检测。');continue
        if answer.isdecimal():
            number=int(answer)
            if not 1<=number<=len(choices):tell('编号不在当前候选列表中。请重新选择或输入 L。');continue
            answer=choices[number-1][0]
        try:return _path_file(root,kind,answer)
        except (ValueError,OSError) as exc:tell('暂时不能使用这个位置：'+str(exc))


def selected_path(value):
    value=value.strip()
    if len(value)>=2 and value[0]==value[-1]=='"':value=value[1:-1]
    if any(character in value for character in '\r\n\x00'):raise ValueError('路径不能含换行或空字符')
    absolute(value)
    return value


def run(root,ask=input,tell=print):
    root=Path(root).resolve()
    spec=validate_task(json.loads((root/'task.json').read_text(encoding='utf-8-sig')))
    if spec['scenario'] not in ('python-basics','notebook-data'):
        raise ValueError('此课程请使用网页中的高级命令入口')
    tell('课航 · 本人主动采集。不会安装软件，不会修改环境。')
    tell('工具目录：'+str(root))
    tell('固定任务：'+spec['title']+'\n任务摘要：'+spec['id'])
    target=choose_path(root,'python',ask,tell)
    if target is None:tell('已退出，未运行课程检测。');return None
    options={}
    if spec['scenario']=='notebook-data':
        tell('内核文件位置：在课程 Python 的终端手动运行 python -m jupyter kernelspec list，再选择对应目录中的 kernel.json。')
        directory=Path(target).parent/'share/jupyter/kernels'
        options['kernel_spec']=choose_path(root,'kernel',ask,tell,directory if directory.is_dir() else None)
        if options['kernel_spec'] is None:tell('已退出，未运行课程检测。');return None
        tell('Notebook 将启动一个临时内核，只执行包内固定演示程序，再关闭该内核。')
    stage=ask('保存初检 A 还是复检 B？请输入 A 或 B：').strip().upper()
    if stage not in ('A','B'):raise ValueError('请选择 A 或 B')
    output=root/('report-'+stage+'.json')
    if output.exists():raise ValueError('报告已存在，原件不会覆盖。复检请选择 B；新一轮请重新解压到新目录。')
    tell('课程目标：'+target)
    if options:tell('所选内核：'+options['kernel_spec'])
    tell('报告保存：'+str(output))
    if ask('核对任务和目标后，输入 START 开始本次固定采集；其他输入取消：').strip()!='START':
        tell('已取消，未运行课程程序。');return None
    report=collect(spec,target,**options)
    with output.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2)
    tell('报告已保存：'+str(output)+'\n找报告：打开上面的工具目录，在 task.json 旁找到 '+output.name+'，回到课航选择它。结果以网页规则核验为准。')
    return output


def main():
    try:run(Path(__file__).resolve().parents[1])
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print('采集未完成：'+str(exc)+'\n请核对完整解压、固定任务与完整路径；旧报告保持原样。')
        raise SystemExit(1)


if __name__=='__main__':main()
