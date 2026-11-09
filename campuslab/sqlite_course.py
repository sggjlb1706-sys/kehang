"""SQLite-only introductory SQL, fixed SELECT and an explicitly prepared demo file."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import platform
import re
import sqlite3
import sys

from .rules import absolute, seal, timestamp, version

QUERY='SELECT category, COUNT(*), SUM(score) FROM scores GROUP BY category ORDER BY category'
ROWS=[['A',2,30],['B',1,12]]


def make_task(title=None):
    title=title or 'SQLite 单机 SQL 入门 · 固定只读任务'
    if not isinstance(title,str) or not 1<=len(title.strip())<=100:raise ValueError('任务名称须为1—100字')
    return seal(dict(schema=1,title=title,scenario='sqlite-basics',source='本项目原创三行演示数据库；仅SQLite单机SQL，不代表MySQL/PostgreSQL课程',
        os='Windows',sqlite_min='3.35',database_mode='standalone-rollback',verify='sqlite-readonly-select-v1',query=QUERY,expected=ROWS))


def validate_spec(spec):
    if not isinstance(spec,dict) or type(spec.get('schema')) is not int or spec.get('schema')!=1 or spec!=make_task(spec.get('title')):raise ValueError('SQLite任务摘要或固定要求不匹配')
    return spec


def prepare_demo(path):
    """Explicit preparation only; never called by collection and never overwrites a file."""
    path=Path(path);absolute(str(path))
    with path.open('xb'):pass
    try:
        with closing(sqlite3.connect(path)) as db,db:
            db.execute('CREATE TABLE scores(id INTEGER PRIMARY KEY,category TEXT NOT NULL,score INTEGER NOT NULL)')
            db.executemany('INSERT INTO scores VALUES(?,?,?)',[(1,'A',10),(2,'A',20),(3,'B',12)])
            db.execute('PRAGMA application_id=1129070930');db.execute('PRAGMA user_version=1')
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def _object(value,keys,label):
    if not isinstance(value,dict) or set(value)!=set(keys):raise ValueError(label+'证据不完整')


def analyze(spec,report):
    validate_spec(spec)
    if not isinstance(report,dict) or type(report.get('schema')) is not int or report.get('schema')!=1 or report.get('task_id')!=spec['id']:raise ValueError('报告与SQLite任务不一致')
    timestamp(report.get('collected_at'));target=report.get('target');facts=report.get('facts')
    _object(target,('requested','actual','exists'),'数据库目标');selected=absolute(target['requested'])
    if target['exists'] is not None and type(target['exists']) is not bool:raise ValueError('数据库存在状态无效')
    if target['actual'] is not None and (absolute(target['actual'])!=selected or target['exists'] is not True):raise ValueError('实际数据库与所选文件不同')
    _object(facts,('os','sqlite','tool_runtime','database','query'),'SQLite事实')
    if facts['os'] is not None and not isinstance(facts['os'],str) or facts['sqlite'] is not None and not isinstance(facts['sqlite'],str):raise ValueError('系统或SQLite版本类型无效')
    absolute(facts['tool_runtime']);database=facts['database'];query=facts['query']
    _object(database,('sha256','after_sha256','header_valid','error'),'数据库身份')
    for key in ('sha256','after_sha256'):
        if database[key] is not None and (not isinstance(database[key],str) or not re.fullmatch('[a-fA-F0-9]{64}',database[key])):raise ValueError('数据库摘要无效')
    if database['header_valid'] is not None and type(database['header_valid']) is not bool or not isinstance(database['error'],str):raise ValueError('数据库证据类型无效')
    _object(query,('read_only','returncode','rows','error'),'SQL查询')
    if query['read_only'] is not None and type(query['read_only']) is not bool or query['returncode'] is not None and type(query['returncode']) is not int or not isinstance(query['error'],str):raise ValueError('SQL执行证据类型无效')
    if query['rows'] is not None and (not isinstance(query['rows'],list) or any(not isinstance(row,list) or len(row)!=3 or not isinstance(row[0],str) or type(row[1]) is not int or type(row[2]) is not int for row in query['rows'])):raise ValueError('SQL结果类型无效')
    if target['actual'] is None and (database['sha256'] is not None or query['returncode'] is not None):raise ValueError('数据库未确认不得携带查询成功事实')
    if query['returncode'] is None and query['rows'] is not None:raise ValueError('未查询不能携带结果')
    checks=[]
    def check(key,status,observed,requirement):checks.append(dict(id=key,status=status,observed=observed,requirement=requirement))
    check('os','unknown' if facts['os'] is None else ('pass' if facts['os']=='Windows' else 'mismatch'),facts['os'],'Windows')
    observed=facts['sqlite'];release=re.fullmatch(r'\d+\.\d+\.\d+',observed or '')
    check('sqlite:runtime',('pass' if version(observed)>=version('3.35') else 'mismatch') if release else 'unknown',dict(version=observed,tool_runtime=facts['tool_runtime']),'明确记录工具Python中的SQLite>=3.35；不代表服务器数据库')
    state='missing' if target['exists'] is False else 'unknown'
    if database['header_valid'] is not None:state='pass' if database['header_valid'] and database['sha256'] and not database['error'] else 'mismatch'
    check('sqlite:database',state,database,'明确SQLite文件、有效文件头与内容摘要')
    check('sqlite:readonly','unknown' if query['read_only'] is None else ('pass' if query['read_only'] and database['sha256'] is not None and database['sha256']==database['after_sha256'] else 'mismatch'),dict(mode_ro=query['read_only'],before=database['sha256'],after=database['after_sha256']),'mode=ro、query_only及采集前后内容摘要相同')
    check('sqlite:query','unknown' if query['returncode'] is None else ('pass' if query['returncode']==0 and query['rows']==ROWS and not query['error'] else 'mismatch'),query,'固定分组SELECT得到A/2/30及B/1/12')
    return dict(task_id=spec['id'],target=target,collected_at=report['collected_at'],checks=checks,passed=all(c['status']=='pass' for c in checks))


def compare_identity(before,after):
    if absolute(before['target']['requested'])!=absolute(after['target']['requested']):raise ValueError('复检必须使用同一SQLite文件')
    if absolute(before['facts']['tool_runtime'])!=absolute(after['facts']['tool_runtime']):raise ValueError('复检须使用同一SQL工具运行时')
    a,b=before['facts']['database']['sha256'],after['facts']['database']['sha256']
    if a is not None and b is not None and a!=b:raise ValueError('数据库内容身份已变更，请重新初检')


def collect(spec,target):
    validate_spec(spec);absolute(target);path=Path(target)
    report=dict(schema=1,task_id=spec['id'],collected_at=datetime.now(timezone.utc).isoformat(),target=dict(requested=target,actual=None,exists=path.is_file()),
        facts=dict(os=platform.system(),sqlite=sqlite3.sqlite_version,tool_runtime=sys.executable,
        database=dict(sha256=None,after_sha256=None,header_valid=None,error='数据库不存在'),query=dict(read_only=None,returncode=None,rows=None,error='数据库未打开')))
    facts=report['facts']
    if path.is_file():
        report['target']['actual']=str(path.resolve())
        try:
            raw=path.read_bytes();facts['database'].update(sha256=hashlib.sha256(raw).hexdigest(),header_valid=raw[:16]==b'SQLite format 3\x00' and raw[18:20]==b'\x01\x01',error='')
            if not facts['database']['header_valid']:raise ValueError('本固定任务仅支持独立rollback-journal模式SQLite文件；不接受WAL数据库')
            if any(Path(str(path)+suffix).exists() for suffix in ('-wal','-shm','-journal')):
                facts['database']['error']='数据库有关联日志文件，当前固定单文件身份不足，请为本任务选择专用独立演示文件'
                raise ValueError(facts['database']['error'])
            with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
                db.execute('PRAGMA query_only=ON');db.execute('PRAGMA trusted_schema=OFF')
                kind=db.execute("SELECT type FROM sqlite_master WHERE name='scores'").fetchone()
                if kind!=('table',):raise ValueError('固定任务要求scores为普通数据表')
                schema=db.execute('PRAGMA table_info(scores)').fetchall()
                if [(r[1],r[2].upper()) for r in schema]!=[('id','INTEGER'),('category','TEXT'),('score','INTEGER')]:raise ValueError('scores表结构与固定演示任务不同')
                allowed={sqlite3.SQLITE_SELECT,sqlite3.SQLITE_READ,sqlite3.SQLITE_FUNCTION}
                def authorize(action,arg1,arg2,dbname,trigger):
                    if action not in allowed:return sqlite3.SQLITE_DENY
                    if action==sqlite3.SQLITE_FUNCTION and (arg2 or '').casefold() not in ('count','sum'):return sqlite3.SQLITE_DENY
                    return sqlite3.SQLITE_OK
                db.set_authorizer(authorize);steps=[0]
                def progress():steps[0]+=1;return int(steps[0]>1000)
                db.set_progress_handler(progress,1000)
                facts['query'].update(read_only=True,returncode=0,rows=[list(row) for row in db.execute(QUERY).fetchall()],error='')
        except (OSError,sqlite3.Error,ValueError) as exc:
            facts['query'].update(returncode=1,error=type(exc).__name__+': '+str(exc)[:500])
        finally:
            try:facts['database']['after_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:facts['database']['error']='无法复核采集后的文件摘要'
    report['collected_at']=datetime.now(timezone.utc).isoformat();analyze(spec,report);return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare-demo',required=True,type=Path);args=parser.parse_args()
    path=prepare_demo(args.prepare_demo)
    print('Created fixed SQLite demo: '+str(path))


if __name__=='__main__':main()
