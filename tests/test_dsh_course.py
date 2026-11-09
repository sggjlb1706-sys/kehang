"""Constructed DSH contracts, never evidence of a real Agent execution."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from campuslab.dsh_course import (SUPPORTED_VERSION, INPUT_BYTES, make_task, validate_spec,
                                  collect, analyze, compare_identity, prepare_workspace, evidence_template)


class DshCourseTests(unittest.TestCase):
    def test_route_snapshots_are_fixed(self):
        from campuslab.rules import seal
        self.assertNotEqual(make_task(route='desktop')['id'], make_task(route='cli')['id'])
        spec=make_task(); spec['verify']='run-arbitrary-command'
        with self.assertRaises(ValueError):validate_spec(seal(spec))
        with self.assertRaises(ValueError):make_task(route='other')

    def test_missing_desktop_does_not_require_node(self):
        with tempfile.TemporaryDirectory() as folder, patch('campuslab.dsh_course.subprocess.run') as run:
            r=collect(make_task(),str(Path(folder)/'DeepSeek Harness.exe'))
        run.assert_not_called()
        result=analyze(make_task(),r)
        self.assertFalse(result['passed'])
        self.assertEqual(next(c['status'] for c in result['checks'] if c['id']=='dsh:software'),'missing')
        self.assertFalse(any(c['id']=='dsh:node' for c in result['checks']))

    def test_cli_selected_node_and_package_are_paired_without_dsh_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);node=root/'node.exe';node.touch()
            pkg=root/'node_modules'/'@deepseek-ai'/'dsh';(pkg/'lib').mkdir(parents=True)
            (pkg/'lib'/'bin.js').write_text('must never run',encoding='utf-8')
            manifest=pkg/'package.json'
            manifest.write_text(json.dumps(dict(name='@deepseek-ai/dsh',version=SUPPORTED_VERSION,
                engines={'node':'>=24.9.0'},bin={'dsh':'lib/bin.js'})),encoding='utf-8')
            with patch('campuslab.dsh_course._node_identity',return_value=dict(actual=str(node),version='24.8.0',error='')) as probe:
                r=collect(make_task(route='cli'),str(node),str(manifest))
            probe.assert_called_once_with(node)
        result=analyze(make_task(route='cli'),r)
        self.assertEqual(next(c['status'] for c in result['checks'] if c['id']=='dsh:node'),'mismatch')
        self.assertFalse(result['passed'])

    def test_package_bin_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);node=root/'node.exe';node.touch();manifest=root/'package.json'
            manifest.write_text(json.dumps(dict(name='@deepseek-ai/dsh',version=SUPPORTED_VERSION,
                engines={'node':'>=24.9.0'},bin={'dsh':'../evil.js'})),encoding='utf-8')
            with patch('campuslab.dsh_course._node_identity',return_value=dict(actual=str(node),version='24.21.0',error='')):
                r=collect(make_task(route='cli'),str(node),str(manifest))
        self.assertFalse(analyze(make_task(route='cli'),r)['passed'])
        self.assertIsNone(r['facts']['installation']['bin'])

    def test_prepare_never_overwrites_and_uses_fixed_data(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'lesson'; prepare_workspace(make_task(),str(target))
            self.assertEqual((target/'input.csv').read_bytes(),INPUT_BYTES)
            with self.assertRaises(ValueError):prepare_workspace(make_task(),str(target))

    def test_prepared_template_is_not_success_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'lesson';prepare_workspace(make_task(),str(target))
            initial=json.loads((target/'evidence-template.json').read_text(encoding='utf-8'))
            self.assertFalse(initial['permission']['confirmed'])
            self.assertEqual(initial['calls'],[])
            r=collect(make_task(),str(Path(folder)/'DeepSeek Harness.exe'),workspace=str(target))
            template=evidence_template(r)
            self.assertIsNone(template['started_at'])
            self.assertIsNone(template['ended_at'])
            with self.assertRaises(ValueError):
                collect(make_task(),str(Path(folder)/'DeepSeek Harness.exe'),workspace=str(target),evidence=template)

    def test_artifact_alone_or_declaration_does_not_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);exe=root/'DeepSeek Harness.exe';exe.write_bytes(b'fixture')
            work=root/'lesson';prepare_workspace(make_task(),str(work));(work/'summary.json').write_text('{"count":3,"sum":42}')
            with patch('campuslab.dsh_course._desktop_metadata',return_value=dict(product='DeepSeek Harness',version=SUPPORTED_VERSION,error='')):
                r=collect(make_task(),str(exe),workspace=str(work),provider='deepseek',model='deepseek-flash')
        result=analyze(make_task(),r)
        self.assertFalse(result['passed'])
        self.assertEqual(next(c['status'] for c in result['checks'] if c['id']=='dsh:artifact'),'pass')
        self.assertEqual(next(c['status'] for c in result['checks'] if c['id']=='dsh:tools'),'unknown')

    def test_complete_user_excerpt_is_distinguished_from_simulation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);exe=root/'DeepSeek Harness.exe';exe.write_bytes(b'fixture')
            work=root/'lesson';prepare_workspace(make_task(),str(work));(work/'summary.json').write_text('{"count":3,"sum":42}')
            with patch('campuslab.dsh_course._desktop_metadata',return_value=dict(product='DeepSeek Harness',version=SUPPORTED_VERSION,error='')):
                r=collect(make_task(),str(exe),workspace=str(work),provider='deepseek',model='deepseek-flash')
                evidence=excerpt(r)
                r=collect(make_task(),str(exe),workspace=str(work),provider='deepseek',model='deepseek-flash',evidence=evidence)
                self.assertTrue(analyze(make_task(),r)['passed'])
                evidence['source']='protocol-simulation'
                simulated=collect(make_task(),str(exe),workspace=str(work),provider='deepseek',model='deepseek-flash',evidence=evidence)
                self.assertFalse(analyze(make_task(),simulated)['passed'])
                self.assertEqual(analyze(make_task(),r)['evidence_basis'],'本人提供DSH最小工具摘要 + 本机固定产物核验；非远程真实性证明')

    def test_mismatched_evidence_identity_and_unapproved_calls_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);exe=root/'DeepSeek Harness.exe';exe.write_bytes(b'fixture')
            work=root/'lesson';prepare_workspace(make_task(),str(work));(work/'summary.json').write_text('{"count":3,"sum":42}')
            with patch('campuslab.dsh_course._desktop_metadata',return_value=dict(product='DeepSeek Harness',version=SUPPORTED_VERSION,error='')):
                r=collect(make_task(),str(exe),workspace=str(work),provider='deepseek',model='deepseek-flash')
                for change in [lambda x:x.update(model='other'), lambda x:x['calls'][0].update(path='../secret'),
                    lambda x:x.update(api_key='NEVER-EXPORT'),lambda x:x.update(ended_at='2020-01-01T00:00:00Z')]:
                    evidence=excerpt(r);change(evidence)
                    with self.subTest(change=change),self.assertRaises(ValueError):
                        collect(make_task(),str(exe),workspace=str(work),provider='deepseek',model='deepseek-flash',evidence=evidence)

    def test_retest_rejects_component_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            r=collect(make_task(),str(Path(folder)/'DeepSeek Harness.exe'),provider='deepseek',model='deepseek-flash')
        b=deepcopy(r);b['collected_at']=(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat()
        for change in [lambda x:x['facts']['model'].update(model='other'),
            lambda x:x['facts']['workspace'].update(requested='D:\\other'),
            lambda x:x['facts']['installation'].update(sha256='f'*64),
            lambda x:x['target'].update(requested='D:\\other.exe')]:
            new=deepcopy(b);change(new)
            with self.subTest(change=change),self.assertRaises(ValueError):compare_identity(r,new)

    def test_incomplete_fact_or_wrong_actual_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            r=collect(make_task(),str(Path(folder)/'DeepSeek Harness.exe'))
        broken=deepcopy(r);del broken['facts']['runtime']
        with self.assertRaises(ValueError):analyze(make_task(),broken)
        broken=deepcopy(r);broken['target'].update(actual='D:\\other.exe',exists=True)
        with self.assertRaises(ValueError):analyze(make_task(),broken)


def excerpt(report):
    now=datetime.now(timezone.utc)
    start=now-timedelta(seconds=2);end=now-timedelta(seconds=1)
    f=report['facts']
    return dict(schema=1,source='dsh-user-excerpt',task_id=report['task_id'],route=f['installation']['route'],
        target=report['target']['requested'],installation_sha256=f['installation']['sha256'],
        package_json=f['installation']['package_json'],runtime=f['runtime']['actual'],runtime_version=f['runtime']['version'],
        workspace=f['workspace']['requested'],workspace_id=f['workspace']['id'],provider=f['model']['provider'],model=f['model']['model'],
        started_at=start.isoformat(),ended_at=end.isoformat(),
        permission=dict(confirmed=True,read=['input.csv'],write=['summary.json'],tools=['read','write']),
        model_result='completed',calls=[dict(tool='read',path='input.csv',status='success',at=start.isoformat()),
                                      dict(tool='write',path='summary.json',status='success',at=end.isoformat())],
        artifact_sha256=f['artifact']['sha256'])


if __name__=='__main__':unittest.main()
