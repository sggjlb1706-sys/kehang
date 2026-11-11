from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from subprocess import CompletedProcess
import base64
import json


class LauncherPathTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='课航 选择路径 ')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'检测工具';self.root.mkdir()
        self.python=Path(self.temp.name)/'课程 Python/python.exe'
        self.python.parent.mkdir();self.python.write_bytes(b'not executed in selection tests')

    def test_enter_lists_candidates_and_number_selects_without_running_python(self):
        from campuslab.launcher import choose_path
        messages=[];answers=iter(['','1'])
        with patch('campuslab.launcher.discover_python',return_value=[(str(self.python),'注册信息')]),patch('campuslab.launcher.subprocess.run') as runner:
            chosen=choose_path(self.root,'python',lambda _:next(answers),messages.append)
        self.assertEqual(chosen,str(self.python));runner.assert_not_called()
        self.assertIn('未检测','\n'.join(messages))

    def test_browse_returns_unicode_space_path_and_cancel_is_retryable(self):
        from campuslab.launcher import choose_path
        answers=iter(['F','F'])
        with patch('campuslab.launcher.choose_file',side_effect=[None,str(self.python)]) as picker:
            self.assertEqual(choose_path(self.root,'python',lambda _:next(answers),lambda _:None),str(self.python))
        self.assertEqual(picker.call_count,2)

    def test_invalid_directory_runtime_and_missing_file_can_recover_without_collect(self):
        from campuslab.launcher import choose_path
        runtime=self.root/'runtime/python.exe';runtime.parent.mkdir();runtime.write_bytes(b'tool')
        answers=iter([str(self.python.parent),str(runtime),str(self.root/'missing/python.exe'),'?','Q'])
        messages=[]
        with patch('campuslab.launcher.collect') as collector:
            self.assertIsNone(choose_path(self.root,'python',lambda _:next(answers),messages.append))
            collector.assert_not_called()
        text='\n'.join(messages)
        for expected in ['文件夹','runtime','不存在','Anaconda Prompt']:self.assertIn(expected,text)

    def test_discovery_filters_runtime_missing_alias_and_deduplicates(self):
        from campuslab.launcher import discover_python
        runtime=self.root/'runtime/python.exe';runtime.parent.mkdir();runtime.write_bytes(b'tool')
        alias=Path(self.temp.name)/'Microsoft/WindowsApps/python.exe';alias.parent.mkdir(parents=True);alias.write_bytes(b'alias')
        entries=[(str(self.python),'注册信息'),(str(runtime),'注册信息'),(str(alias),'注册信息'),(str(self.root/'missing/python.exe'),'注册信息')]
        with patch('campuslab.launcher._registered_python',return_value=entries),patch('campuslab.launcher.shutil.which',return_value=str(self.python)),patch('campuslab.launcher.subprocess.run') as runner:
            choices=discover_python(self.root)
        self.assertEqual([p for p,_ in choices],[str(self.python)]);runner.assert_not_called()

    def test_kernel_browse_is_explicit_and_wrong_filename_retries(self):
        from campuslab.launcher import choose_path
        kernel=Path(self.temp.name)/'课程 内核/kernel.json';kernel.parent.mkdir();kernel.write_text('{}')
        answers=iter([str(self.python),'F'])
        with patch('campuslab.launcher.choose_file',return_value=str(kernel)):
            self.assertEqual(choose_path(self.root,'kernel',lambda _:next(answers),lambda _:None),str(kernel))

    def test_discovery_failure_gives_manual_recovery_and_q_cancels(self):
        from campuslab.launcher import choose_path
        answers=iter(['L','F','Q']);messages=[]
        with patch('campuslab.launcher.discover_python',return_value=[]),patch('campuslab.launcher.choose_file',side_effect=OSError('not available')):
            self.assertIsNone(choose_path(self.root,'python',lambda _:next(answers),messages.append))
        self.assertIn('不代表','\n'.join(messages));self.assertIn('窗口','\n'.join(messages))

    def test_dialog_error_in_local_encoding_returns_recoverable_error(self):
        from campuslab.launcher import choose_file
        with patch('campuslab.launcher.subprocess.run',return_value=CompletedProcess([],1,b'',b'\xd5\xe2')):
            with self.assertRaisesRegex(OSError,'窗口'):choose_file('python',self.python.parent)

    def test_dialog_paths_are_inert_json_and_do_not_change_execution_policy(self):
        from campuslab.launcher import choose_file,FILE_DIALOG_SCRIPT
        directory=self.root/"课程 $() & '特殊目录"
        result=CompletedProcess([],0,json.dumps({'selected':str(self.python)}).encode('utf8'),b'')
        with patch('campuslab.launcher.subprocess.run',return_value=result) as runner:
            self.assertEqual(choose_file('python',directory),str(self.python))
        args,kwargs=runner.call_args
        self.assertEqual(base64.b64decode(args[0][-1]).decode('utf-16le'),FILE_DIALOG_SCRIPT)
        self.assertEqual(json.loads(kwargs['input'])['directory'],str(directory))
        self.assertNotIn('-ExecutionPolicy',args[0]);self.assertFalse(kwargs.get('shell',False))


if __name__=='__main__':unittest.main()
