"""Exercise the actual browser literal encoder; never run a generated collector here."""
import base64
import json
from pathlib import Path
import shutil
import subprocess
import unittest


class PowerShellQuoteTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('powershell.exe') and shutil.which('node'),'Requires Windows PowerShell and Node development tools')
    def test_actual_js_encoder_preserves_smart_quotes_and_metacharacters(self):
        samples=[f'D:\\合法\\O{chr(cp)}Brien\\x' for cp in range(0x2018,0x2020)]
        samples.append('D:\\工具 O\'Brien $Literal `tick "double"\\x')
        app=Path(__file__).resolve().parents[1]/'web/app.js'
        node="const fs=require('fs'),vm=require('vm');const source=fs.readFileSync(process.argv[1],'utf8');const ps=vm.runInNewContext(source.match(/^const ps = (.+);$/m)[1]);process.stdout.write(JSON.stringify(JSON.parse(process.argv[2]).map(ps)));"
        encoded=json.loads(subprocess.check_output(['node','-e',node,str(app),json.dumps(samples,ensure_ascii=False)]))
        script='\n'.join('$taskValue = '+literal+'; [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($taskValue))' for literal in encoded)
        payload=base64.b64encode(script.encode('utf-16le')).decode()
        process=subprocess.run(['powershell.exe','-NoProfile','-EncodedCommand',payload],capture_output=True,timeout=15)
        self.assertEqual(process.returncode,0,process.stderr.decode(errors='replace'))
        decoded=[base64.b64decode(line).decode('utf-8') for line in process.stdout.splitlines()]
        self.assertEqual(decoded,samples)


if __name__=='__main__':unittest.main()
