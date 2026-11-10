"""One portable CSV → Notebook → SQLite exercise; submitted data is never code."""
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import zipfile

from .notebook_course import CSV, EXPECTED
from .rules import canonical, seal, task
from .sqlite_course import ROWS

FILES = Path(__file__).with_name('data') / 'practice'
SCOPE = '仅核对提交JSON中的固定任务、资料版本、数据摘要和数值结果；不执行上传代码，不证明实际操作、学习掌握、作品原创或未复制。环境报告、本人阅读声明和成果核验分别记录。'


def make_practice():
    return seal(dict(schema=1, kind='kehang-practice', material_version='scores-20261110-v1',
        title='从CSV到SQL：同源成绩数据分析',
        objectives=['用明确选择的Notebook内核读取CSV并计算分组统计。',
                    '把同源CSV导入专用SQLite文件，以SELECT复算分组结果。',
                    '提交限定JSON，核对两条路径的成果并保留修订记录。'],
        prerequisites=['Windows；已有Python 3.10—3.14、Jupyter/ipykernel、NumPy≥1.24、Pandas≥2.0。不会自动安装。',
                       '明确选择课程Python及其kernel.json；SQLite练习使用同一已有Python的标准库。',
                       '将全部资料解压至新的专用目录；不要放入私人课程库或覆盖已有数据库。'],
        dataset_sha256=hashlib.sha256(CSV.encode('utf-8')).hexdigest(),
        component_task_ids={'notebook':task('notebook-data')['id'],'sqlite':task('sqlite-basics')['id']},
        expected={'notebook':EXPECTED,'sqlite':ROWS},
        steps=[dict(title='1. 准备并分别检查两个环境任务',
                    body='下载全部资料。教师发布后分别给出Notebook与SQLite课程码；先选Notebook任务，明确课程Python和kernel.json并手动采集。SQLite文件将在第3步由本人显式创建。',
                    expected='资料目录包含README、CSV、Notebook、SQLite模板、成果模板和课堂资料包；环境检查与成果状态独立。',
                    recovery='缺依赖/错内核时按Notebook环境差异手动处理；没有SQLite文件时先完成第3步，不将缺失当通过。'),
               dict(title='2. 在Notebook中计算并导出中间结果',
                    body='在已有Jupyter打开01_Notebook练习.ipynb，选择已确认的课程内核。按提示填三处TODO并从头逐格运行，保存Notebook及notebook-result.json。',
                    expected='3行，score合计42，A组30、B组12。',
                    recovery='先运行第一格确认工作目录及sys.executable；找不到CSV时把Notebook与CSV放在同一解压目录。None/TODO不是完成成果。'),
               dict(title='3. 用SQLite复算并形成提交文件',
                    body='编辑02_SQLite练习.py中的QUERY，填入按category分组、计算COUNT与SUM并排序的SELECT。用同一课程Python在终端主动运行该文件。它仅在scores.sqlite不存在时创建专用演示库，再只读查询。',
                    expected='查询行A/2/30、B/1/12；生成实训成果.json，原notebook-result.json保留。',
                    recovery='SQL出错后修改QUERY再运行；不要删除首次错误日志。缺Notebook结果先回第2步。数据库结构/内容不符时换新专用目录，不覆盖私人文件。'),
               dict(title='4. 提交、复检并导出完成物',
                    body='上传实训成果.json，保留首次错误和后续正确的核验记录。分别选择Notebook与SQLite环境任务，导入各自初检/较晚同目标复检。导出完成物并保存本人Notebook。',
                    expected='两项成果数值符合固定要求；两个环境任务分别有自己的报告/复检。',
                    recovery='旧任务/旧资料请重新下载当前包并实际重做；错误数值回对应模板复算后再次提交。相同正确结果不能证明未复制。')],
        scope=SCOPE))


def validate_practice(spec):
    if not isinstance(spec,dict) or canonical(spec) != canonical(make_practice()):
        raise ValueError('实训要求、资料版本或任务摘要不匹配，请重新取得当前固定资料包')
    return spec


def export_package(spec):
    validate_practice(spec)
    return dict(schema=1,kind='kehang-practice-package',practice=spec,
                sha256=hashlib.sha256(canonical(spec).encode('utf-8')).hexdigest())


def import_package(package):
    if not isinstance(package,dict) or canonical(package) != canonical(export_package(make_practice())):
        raise ValueError('课堂资料包不匹配；请向教师重新取得原件，不能导入自定义命令或变更核验要求')
    return package['practice']


def publish(store,spec):
    validate_practice(spec)
    courses={name:store.publish(task(scenario)) for name,scenario in
             [('notebook','notebook-data'),('sqlite','sqlite-basics')]}
    return dict(practice=spec,package=export_package(spec),courses=courses)


def submission_template(spec):
    validate_practice(spec)
    return dict(schema=1,kind='kehang-practice-result',practice_id=spec['id'],
                material_version=spec['material_version'],dataset_sha256=spec['dataset_sha256'],
                component_task_ids=spec['component_task_ids'].copy(),notebook=None,sqlite=None)


def check(spec,submission):
    validate_practice(spec)
    result=dict(practice_id=spec['id'],checked_at=datetime.now(timezone.utc).isoformat(),
                status='missing',passed=False,components={},scope=SCOPE,
                next_step='先按资料完成Notebook和SQLite练习，再提交实训成果.json；环境探针不能代替本人提交。')
    def state(status,message):
        result.update(status=status,next_step=message)
        return result
    if submission is None or submission == {}:
        return result
    template=submission_template(spec)
    if not isinstance(submission,dict) or set(submission)!=set(template):
        return state('invalid','成果须为资料中限定JSON对象，不能提交Notebook、SQL、分享报告或额外命令。请核对成果模板后重新导出。')
    if type(submission['schema']) is not int or submission['schema']!=1 or submission['kind']!='kehang-practice-result':
        return state('invalid','成果格式或schema无效，请使用当前资料中的模板重新导出。')
    if any(not isinstance(submission[key],str) for key in ('practice_id','material_version','dataset_sha256')) or not isinstance(submission['component_task_ids'],dict):
        return state('invalid','任务、资料或组件身份的字段类型无效，请使用原模板。')
    if any(submission[key]!=template[key] for key in ('practice_id','material_version','dataset_sha256','component_task_ids')):
        return state('obsolete','成果的任务、资料版本、数据摘要或组件身份与当前要求不一致；重新取得当前资料并实际复做，不能只改标识。')
    nb,sql=submission['notebook'],submission['sqlite']
    if nb is not None and (not isinstance(nb,dict) or set(nb)!=set(EXPECTED) or
        any(type(nb[k]) is not int for k in ('rows','array_sum')) or not isinstance(nb['group_totals'],dict) or
        any(not isinstance(k,str) or type(v) is not int for k,v in nb['group_totals'].items())):
        return state('invalid','Notebook结果须包含整数rows、array_sum及按组记录整数的group_totals；不能用布尔值或文本代替。')
    if sql is not None and (not isinstance(sql,list) or any(not isinstance(row,list) or len(row)!=3 or
        not isinstance(row[0],str) or type(row[1]) is not int or type(row[2]) is not int for row in sql)):
        return state('invalid','SQLite结果须为[组名,整数计数,整数合计]的行数组，请按原模板重新导出。')
    for key,value,expected in [('notebook',nb,EXPECTED),('sqlite',sql,ROWS)]:
        status='missing' if value is None else ('pass' if value==expected else 'mismatch')
        result['components'][key]=dict(status=status,expected=expected,submitted=value,
            next_step={'missing':'先完成该项实际操作并导出结果。','mismatch':'回该项模板检查CSV、分组/排序和数值，复算后重新提交；保留本次记录。',
                       'pass':'本项提交数值符合固定要求；另外保存实际操作文件及独立环境证据。'}[status])
    statuses=[item['status'] for item in result['components'].values()]
    if 'mismatch' in statuses:
        return state('mismatch','结果有误：按下方对应组件重新计算并再次提交，保留本次错误记录。')
    if 'missing' in statuses:
        return state('missing','缺少部分成果：完成标明缺失的组件后重新提交。')
    result.update(status='pass',passed=True,next_step='两项成果数值符合要求。保存Notebook、CSV、SQLite文件和全部提交记录；分别完成两组件同目标环境复检后导出完成物。')
    return result


def materials_zip(spec):
    validate_practice(spec)
    out=BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('课堂资料包.json',json.dumps(export_package(spec),ensure_ascii=False,indent=2))
        z.writestr('scores.csv',CSV)
        z.writestr('成果模板.json',json.dumps(submission_template(spec),ensure_ascii=False,indent=2))
        for name in ('README.md','01_Notebook练习.ipynb','02_SQLite练习.py'):
            z.writestr(name,(FILES/name).read_bytes())
    return out.getvalue()
