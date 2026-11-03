"""Small local course store: each publish creates an immutable snapshot."""
import json
from contextlib import closing
from pathlib import Path
import secrets
import sqlite3

from .rules import canonical, validate_task


class CourseStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS courses(code TEXT PRIMARY KEY, task TEXT NOT NULL)')

    def publish(self, spec):
        validate_task(spec)
        for _ in range(5):
            code = secrets.token_hex(5).upper()
            try:
                with closing(sqlite3.connect(self.path)) as db, db:
                    db.execute('INSERT INTO courses VALUES (?, ?)', (code, canonical(spec)))
                return dict(code=code, task=spec)
            except sqlite3.IntegrityError:
                continue
        raise ValueError('课程码生成冲突，请重试')

    def get(self, code):
        if not isinstance(code, str) or len(code) != 10 or any(x not in '0123456789ABCDEF' for x in code):
            raise ValueError('请输入10位课程码')
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute('SELECT task FROM courses WHERE code=?', (code,)).fetchone()
        if row is None:
            raise ValueError('未找到该课程')
        return validate_task(json.loads(row[0]))
