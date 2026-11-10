"""User-started bundle entry for the Python and Notebook fixed collectors."""
import json
from pathlib import Path

from .collect import collect
from .rules import absolute, validate_task


def selected_path(value):
    value=value.strip()
    if len(value)>=2 and value[0]==value[-1]=='"':value=value[1:-1]
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
    target=selected_path(ask('课程 Python 完整路径（不是包内 runtime）：'))
    options={}
    if spec['scenario']=='notebook-data':
        options['kernel_spec']=selected_path(ask('该 Python 对应的已有 kernel.json 完整路径：'))
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
    tell('报告已保存：'+str(output)+'\n回到课航，选择此报告；初检与复检也可一次选择。结果以网页规则核验为准。')
    return output


def main():
    try:run(Path(__file__).resolve().parents[1])
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print('采集未完成：'+str(exc)+'\n请核对完整解压、固定任务与完整路径；旧报告保持原样。')
        raise SystemExit(1)


if __name__=='__main__':main()
