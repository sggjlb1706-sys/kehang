"""SQLite read-only fixed-task tests; no server DB is implied."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import tempfile
import unittest
import sqlite3
from campuslab.sqlite_course import make_task, validate_spec, analyze, compare_identity, collect, prepare_demo
from campuslab.rules import seal


class SQLiteCourseTest(unittest.TestCase):
    def test_real_demo_query_preserves_bytes_and_preparation_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'demo.sqlite';prepare_demo(path)
            before=path.read_bytes();r=collect(make_task(),str(path))
            self.assertTrue(analyze(make_task(),r)['passed'])
            self.assertEqual(path.read_bytes(),before)
            self.assertTrue(r['facts']['query']['read_only'])
            with self.assertRaises(FileExistsError):prepare_demo(path)

    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'missing.sqlite';r=collect(make_task(),str(path))
            self.assertFalse(path.exists());self.assertFalse(analyze(make_task(),r)['passed'])

    def test_wrong_database_and_wrong_result_do_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'text.sqlite';path.write_text('not a database')
            r=collect(make_task(),str(path));self.assertFalse(analyze(make_task(),r)['passed'])
            path.unlink();prepare_demo(path);r=collect(make_task(),str(path))
            r['facts']['query']['rows']=[['A',2,0],['B',1,12]]
            self.assertFalse(analyze(make_task(),r)['passed'])

    def test_task_never_accepts_arbitrary_sql(self):
        spec=make_task();spec['query']='DROP TABLE scores'
        with self.assertRaises(ValueError):validate_spec(seal(spec))

    def test_wal_or_sidecar_database_cannot_reuse_single_file_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'demo.sqlite';prepare_demo(path)
            with sqlite3.connect(path) as db:
                db.execute('PRAGMA journal_mode=WAL')
                self.assertFalse(analyze(make_task(),collect(make_task(),str(path)))['passed'])
            db.close()

    def test_retest_binds_database_path_and_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'demo.sqlite';prepare_demo(path);a=collect(make_task(),str(path));b=deepcopy(a)
            compare_identity(a,b)
            b['facts']['database']['sha256']='F'*64
            with self.assertRaises(ValueError):compare_identity(a,b)

    def test_partial_and_boolean_numbers_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'demo.sqlite';prepare_demo(path);original=collect(make_task(),str(path))
            for change in [lambda r:r['facts'].pop('query'),lambda r:r['facts']['query'].update(returncode=False),
                           lambda r:r['facts']['query'].update(rows=[['A',True,30],['B',1,12]]),lambda r:r.update(task_id='wrong')]:
                r=deepcopy(original);change(r)
                with self.assertRaises(ValueError):analyze(make_task(),r)


if __name__=='__main__':unittest.main()
