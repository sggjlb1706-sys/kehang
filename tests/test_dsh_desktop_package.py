"""Constructed ASAR metadata regression; never executes DSH or calls a model."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from campuslab.dsh_course import collect, analyze, make_task, compare_identity, evidence_template, SUPPORTED_VERSION


def bundle(folder, *, name='@deepseek-ai/dsh-desktop', version=SUPPORTED_VERSION, offset='0', size=None, bad_hash=False, link=None):
    body=json.dumps(dict(name=name,version=version,main='lib/main.js')).encode()
    digest=hashlib.sha256(body).hexdigest()
    entry=dict(size=len(body) if size is None else size,offset=offset,
               integrity=dict(algorithm='SHA256',hash='0'*64 if bad_hash else digest,blockSize=4194304,blocks=[digest]))
    if link is not None:entry['link']=link
    header=json.dumps(dict(files={'package.json':entry})).encode()
    padding=b'\x00'*((-len(header))%4)
    raw=struct.pack('<4I',4,len(header)+len(padding)+8,len(header)+len(padding)+4,len(header))+header+padding+body
    target=folder/'resources'/'app.asar';target.parent.mkdir(exist_ok=True);target.write_bytes(raw)
    return target


class DshDesktopPackageTests(unittest.TestCase):
    def collect_fixture(self, folder):
        exe=folder/'DeepSeek Harness.exe';exe.write_bytes(b'constructed PE fixture, metadata patched only')
        with patch('campuslab.dsh_course._desktop_metadata',return_value=dict(product='DeepSeek Harness',version='0.2.2.0',error='')),patch('campuslab.dsh_course.platform.system',return_value='Windows'),patch('campuslab.dsh_course.subprocess.run') as execute:
            report=collect(make_task(),str(exe))
        execute.assert_not_called()
        return report

    def software(self, report):
        return next(x['status'] for x in analyze(make_task(),report)['checks'] if x['id']=='dsh:software')

    def test_exact_package_resolves_pe_prerelease_without_claiming_agent(self):
        with tempfile.TemporaryDirectory(prefix='DSH 中文 空格 ') as temp:
            folder=Path(temp);path=bundle(folder);report=self.collect_fixture(folder)
            self.assertEqual(self.software(report),'pass')
            self.assertEqual(report['facts']['installation']['version'],'0.2.2.0')
            record=report['facts']['installation']['desktop_package']
            self.assertEqual(record['version'],SUPPORTED_VERSION)
            self.assertEqual(record['path'],str(path.resolve()))
            self.assertEqual(record['sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertFalse(analyze(make_task(),report)['passed'])
            self.assertEqual(next(x['status'] for x in analyze(make_task(),report)['checks'] if x['id']=='dsh:tools'),'unknown')

    def test_numeric_pe_version_alone_never_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(self.software(self.collect_fixture(Path(temp))),'mismatch')

    def test_wrong_name_version_or_tampered_integrity_never_pass(self):
        for options in [dict(name='unrelated-app'),dict(version='0.2.2'),dict(bad_hash=True),dict(link='../other/package.json')]:
            with self.subTest(options=options),tempfile.TemporaryDirectory() as temp:
                folder=Path(temp);bundle(folder,**options)
                self.assertEqual(self.software(self.collect_fixture(folder)),'mismatch')

    def test_out_of_bounds_offsets_and_lengths_are_rejected(self):
        for options in [dict(offset='-1'),dict(offset='9999999999999999999999'),dict(size=65537),dict(size=True)]:
            with self.subTest(options=options),tempfile.TemporaryDirectory() as temp:
                folder=Path(temp);bundle(folder,**options)
                self.assertEqual(self.software(self.collect_fixture(folder)),'mismatch')
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);path=bundle(folder);path.write_bytes(struct.pack('<4I',4,100000000,99999996,99999992))
            self.assertEqual(self.software(self.collect_fixture(folder)),'mismatch')

    def test_package_cannot_be_borrowed_from_other_installation(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);bundle(folder);report=self.collect_fixture(folder)
            report['facts']['installation']['desktop_package']['path']=str(folder/'other'/'resources'/'app.asar')
            with self.assertRaises(ValueError):analyze(make_task(),report)

    def test_bundle_identity_and_new_excerpt_are_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);bundle(folder);before=self.collect_fixture(folder);after=deepcopy(before)
            self.assertIn('desktop_package_sha256',evidence_template(before))
            after['facts']['installation']['desktop_package']['sha256']='f'*64
            with self.assertRaises(ValueError):compare_identity(before,after)

    def test_new_excerpt_cannot_omit_or_change_bundle_binding(self):
        from tests.test_dsh_course import excerpt
        from campuslab.dsh_course import _validate_excerpt
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);bundle(folder);report=self.collect_fixture(folder)
            evidence=excerpt(report);evidence['source']='protocol-simulation'
            with self.assertRaises(ValueError):_validate_excerpt(evidence,report)
            evidence['desktop_package_sha256']=report['facts']['installation']['desktop_package']['sha256']
            _validate_excerpt(evidence,report)
            evidence['desktop_package_sha256']='f'*64
            with self.assertRaises(ValueError):_validate_excerpt(evidence,report)

    def test_old_reports_keep_original_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            report=self.collect_fixture(Path(temp))
        report['facts']['installation'].pop('desktop_package',None)
        report['facts']['installation']['version']=SUPPORTED_VERSION
        self.assertEqual(self.software(report),'pass')
        self.assertNotIn('desktop_package_sha256',evidence_template(report))


if __name__=='__main__':unittest.main()
