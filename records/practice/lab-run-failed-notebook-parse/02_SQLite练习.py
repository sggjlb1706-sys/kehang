"""本人主动运行的固定CSV/SQLite练习模板；课航网页不会运行本文件。"""
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
from contextlib import closing

# TODO：填写README中的分组SELECT；空字符串会提示返回编辑。
QUERY = ''


def main():
    root = Path(__file__).resolve().parent
    if not QUERY.strip():
        raise ValueError('请先填写QUERY的TODO，再主动运行本练习。')
    raw = (root / 'scores.csv').read_bytes()
    package = json.loads((root / '课堂资料包.json').read_text(encoding='utf-8'))
    spec = package['practice']
    if hashlib.sha256(raw).hexdigest() != spec['dataset_sha256']:
        raise ValueError('CSV与本资料版本不一致，请重新取得完整资料。')
    notebook = json.loads((root / 'notebook-result.json').read_text(encoding='utf-8'))
    if any(notebook.get(k) != spec[k] for k in ('material_version','dataset_sha256','component_task_ids')) or notebook.get('practice_id') != spec['id']:
        raise ValueError('Notebook中间结果属于旧任务/资料；请从当前Notebook重新操作。')
    database = root / 'scores.sqlite'
    if not database.exists():
        # Exclusive creation: never replace another file, even if it appears now.
        with database.open('xb'):
            pass
        with closing(sqlite3.connect(database)) as db, db:
            db.execute('CREATE TABLE scores(id INTEGER PRIMARY KEY,category TEXT NOT NULL,score INTEGER NOT NULL)')
            rows = list(csv.DictReader(raw.decode('utf-8').splitlines()))
            db.executemany('INSERT INTO scores VALUES(?,?,?)',
                           [(i,row['category'],int(row['score'])) for i,row in enumerate(rows,1)])
            db.execute('PRAGMA application_id=1129070930')
            db.execute('PRAGMA user_version=1')
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        db.execute('PRAGMA query_only=ON')
        db.execute('PRAGMA trusted_schema=OFF')
        if db.execute("SELECT type FROM sqlite_master WHERE name='scores'").fetchone() != ('table',):
            raise ValueError('请选择专用普通scores表数据库；勿覆盖私人文件。')
        result = [list(row) for row in db.execute(QUERY).fetchall()]
    if hashlib.sha256(database.read_bytes()).hexdigest() != before:
        raise ValueError('数据库内容在查询期间变化，请停止并核对专用目录。')
    submission = json.loads((root / '成果模板.json').read_text(encoding='utf-8'))
    submission['notebook'] = notebook['notebook']
    submission['sqlite'] = result
    (root / '实训成果.json').write_text(json.dumps(submission,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    print('已生成实训成果.json；请回课航核验，数值符合不证明学习掌握或原创。')


if __name__ == '__main__':
    main()
