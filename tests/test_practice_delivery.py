from pathlib import Path
import json
import tempfile
import unittest
import zipfile

from campuslab.practice import make_practice, submission_template
from tools.practice_delivery import build_zip, verify_zip, relative, reviewer_payload, RUNTIME


class DeliverySafetyTest(unittest.TestCase):
    def test_archive_rejects_extra_entries_changed_bytes_and_unsafe_names(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'release.zip'
            payload={'hello.txt':b'fixed release bytes'}
            build_zip(path,'release/',payload)
            with self.assertRaises(AssertionError):
                verify_zip(path,'release/',{'hello.txt':b'changed'})
            with zipfile.ZipFile(path,'a') as z:z.writestr('release/private.txt',b'unexpected')
            with self.assertRaises(AssertionError):verify_zip(path,'release/',payload)
            for name in ('../outside','/absolute','C:/outside','a/../../escape'):
                with self.assertRaises(ValueError):relative(name)

    def test_reviewer_excludes_raw_data_and_hidden_channels_and_redacts_prompt_text(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            sample=submission_template(make_practice());sample.update(make_practice()['expected'])
            values={'README.md':r'Known existing Python, personal directory C:\Users\PrivateStudent\work',
                    'campuslab/example.py':'# fixed code\n',RUNTIME:'official-runtime-fixture',
                    'records/practice/lab-run/实训成果.json':json.dumps(sample),
                    'records/practice/prompt-candidate-excerpts.json':json.dumps([dict(source='fixed-visible-source',messages=[
                        dict(role='system',channel=None,source_line=1,text='excluded system'),
                        dict(role='assistant',channel='analysis',source_line=2,text='excluded hidden'),
                        dict(role='user',channel=None,source_line=3,text=r'Please use C:\Users\PrivateStudent\work')])])}
            for name,text in values.items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
            payload=reviewer_payload(root,['README.md','campuslab/example.py','.env','records/raw.json','private/notes'])
            self.assertNotIn('.env',payload)
            self.assertFalse(any(name.startswith(('records/','private/','.git/')) for name in payload))
            prompt=json.loads(payload['prompts/可见协作脱敏节选.json'])
            self.assertEqual(len(prompt['sources'][0]['messages']),1)
            self.assertNotIn('PrivateStudent',payload['prompts/可见协作脱敏节选.json'].decode())
            self.assertNotIn('PrivateStudent',payload['README.md'].decode())
            self.assertEqual(payload['campuslab/example.py'],(root/'campuslab/example.py').read_bytes())


if __name__=='__main__':unittest.main()
