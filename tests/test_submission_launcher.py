"""No-key checks of the portable connected launcher; never send a model request."""
import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform == 'win32' and shutil.which('pwsh'), 'Windows PowerShell 7 required')
class SubmissionLauncherTest(unittest.TestCase):
    def launch_copy(self, directory, tamper=False):
        root = Path(directory) / '课航 新路径'
        for name in ('campuslab', 'web'):
            shutil.copytree(ROOT/name, root/name)
        (root/'tools').mkdir()
        shutil.copy2(ROOT/'tools/Start-ConnectedModel.ps1', root/'tools/Start-ConnectedModel.ps1')
        files = []
        for name in ('campuslab/diagnosis.py', 'campuslab/chat.py', 'campuslab/web.py'):
            digest = hashlib.sha256((root/name).read_bytes()).hexdigest()
            files.append(dict(path=name, sha256=digest))
        (root/'SOURCE-MANIFEST.json').write_text(json.dumps(dict(candidate='portable-test-candidate', files=files)), encoding='utf8')
        if tamper:
            with (root/'campuslab/chat.py').open('a', encoding='utf8') as stream:
                stream.write('\n# changed after packaging\n')
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        result = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-File',
            str(root/'tools/Start-ConnectedModel.ps1'), '-Python', sys.executable, '-Port', str(port)],
            cwd=directory, capture_output=True, encoding='utf8', timeout=30)
        return root, result

    def test_no_git_copy_reaches_secret_prompt_using_own_source_and_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root, result = self.launch_copy(directory)
            self.assertNotEqual(result.returncode, 0)  # NonInteractive intentionally forbids Read-Host.
            self.assertIn('Read-Host', result.stderr)
            receipt = json.loads((root/'data/connected/启动记录.json').read_text(encoding='utf-8-sig'))
            self.assertEqual(Path(receipt['repo']), root)
            self.assertEqual(Path(receipt['module']), root/'campuslab/diagnosis.py')
            self.assertEqual(receipt['commit'], 'portable-test-candidate')
            self.assertFalse((root/'data/connected/courses.sqlite').exists())

    def test_changed_packaged_model_module_is_rejected_before_secret_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            root, result = self.launch_copy(directory, tamper=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('Read-Host', result.stderr)
            self.assertFalse((root/'data/connected/启动记录.json').exists())


if __name__ == '__main__':
    unittest.main()
