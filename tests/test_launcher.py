import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from campuslab.rules import task


class LauncherTests(unittest.TestCase):
    def test_locates_bundle_and_requires_explicit_confirmation(self):
        from campuslab.launcher import run
        with tempfile.TemporaryDirectory(prefix='课航 工具 ') as name:
            root=Path(name);spec=task('python-basics')
            (root/'task.json').write_text(json.dumps(spec),encoding='utf-8')
            target=root/'课程 Python/python.exe';target.parent.mkdir();target.write_bytes(b'unit selection fixture')
            with patch('campuslab.launcher.collect') as collector:
                answers=iter([str(target),'A','取消'])
                self.assertIsNone(run(root,lambda _:next(answers),lambda _:None))
                collector.assert_not_called()
            self.assertFalse((root/'report-A.json').exists())

    def test_report_never_overwrites_and_non_simple_course_is_refused(self):
        from campuslab.launcher import run
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);spec=task('python-basics')
            (root/'task.json').write_text(json.dumps(spec),encoding='utf-8')
            target=root/'课程 Python/python.exe';target.parent.mkdir();target.write_bytes(b'unit selection fixture')
            (root/'report-A.json').write_text('original',encoding='utf-8')
            with patch('campuslab.launcher.collect') as collector:
                answers=iter([str(target),'A'])
                with self.assertRaisesRegex(ValueError,'已存在'):
                    run(root,lambda _:next(answers),lambda _:None)
                collector.assert_not_called()
            self.assertEqual((root/'report-A.json').read_text(),'original')
            (root/'task.json').write_text(json.dumps(task('deepseek-api')),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'高级'):
                run(root,lambda _:self.fail('must not prompt'),lambda _:None)

    def test_notebook_requires_kernel_and_uses_exact_task(self):
        from campuslab.launcher import run
        with tempfile.TemporaryDirectory(prefix='课航 内核 ') as name:
            root=Path(name);spec=task('notebook-data')
            (root/'task.json').write_text(json.dumps(spec),encoding='utf-8')
            python=root/'课程 Python/python.exe';python.parent.mkdir();python.write_bytes(b'unit selection fixture')
            specfile=root/'课程 Kernel/kernel.json';specfile.parent.mkdir();specfile.write_text('{}')
            target=str(python);kernel=str(specfile)
            report={'task_id':spec['id'],'fixed_test':True}
            with patch('campuslab.launcher.collect',return_value=report) as collector:
                answers=iter([target,kernel,'B','START'])
                result=run(root,lambda _:next(answers),lambda _:None)
                self.assertEqual(result,root/'report-B.json')
                collector.assert_called_once_with(spec,target,kernel_spec=kernel)
            self.assertEqual(json.loads((root/'report-B.json').read_text(encoding='utf-8')),report)


if __name__=='__main__':unittest.main()
