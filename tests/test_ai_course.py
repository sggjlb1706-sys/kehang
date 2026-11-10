"""Fixed AI learning task: consent, protocol and evidence remain distinct."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from email.message import Message
from io import BytesIO
import json
import unittest
from unittest.mock import patch

from campuslab import ai_course as ai
from campuslab.rules import seal


class AICourseTests(unittest.TestCase):
    def report(self):
        spec=ai.make_task()
        return dict(schema=1,task_id=spec['id'],collected_at=datetime.now(timezone.utc).isoformat(),
            target=dict(requested=r'C:\Course\python.exe',actual=r'C:\Course\python.exe',exists=True),
            facts=dict(os='Windows',python='3.13.1',stdlib=True,request=ai.preview(spec),
                run=dict(attempted=True,category='ok',http_status=200,model=spec['api']['model'],role='assistant',
                         finish_reason='stop',content='{"total":42,"count":3,"mean":14}',latency_ms=10)))

    def test_full_result_and_incomplete_response(self):
        spec=ai.make_task(); report=self.report()
        self.assertTrue(ai.analyze(spec,report)['passed'])
        for change in ({'category':'authentication'},
                       {'content':'已完成'},{'finish_reason':'length'},{'model':'other-model'},
                       {'http_status':200,'role':'user'}):
            with self.subTest(change=change):
                candidate=deepcopy(report);candidate['facts']['run'].update(change)
                self.assertFalse(ai.analyze(spec,candidate)['passed'])
        report['facts']['run']=ai.empty_run()
        self.assertFalse(ai.analyze(spec,report)['passed'])

    def test_closed_task_and_preview(self):
        spec=ai.make_task();candidate=deepcopy(spec);candidate['command']='do anything'
        with self.assertRaises(ValueError): ai.validate_spec(seal(candidate))
        preview=ai.preview(spec);preview['endpoint']='https://example.com/chat/completions'
        with self.assertRaises(ValueError): ai.validate_preview(spec,preview)
        preview=ai.preview(spec);preview['payload']['messages'][1]['content']='other question'
        ai.validate_preview(spec,preview)
        report=self.report();report['facts']['request']=preview
        self.assertFalse(ai.analyze(spec,report)['passed'])

    def test_identity_includes_exact_request_and_model(self):
        before=self.report();after=deepcopy(before)
        after['collected_at']=(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat()
        ai.compare_identity(before,after)
        after['facts']['request']['payload']['messages'][1]['content']='changed'
        with self.assertRaises(ValueError): ai.compare_identity(before,after)

    def test_no_consent_means_no_request_or_key_read(self):
        with patch('campuslab.ai_course.urlopen_once',side_effect=AssertionError('must not send')):
            result=ai.call_api(ai.make_task(),ai.preview(ai.make_task()),'not-a-real-key',False)
        self.assertEqual(result['category'],'not_called')

    def test_protocol_simulation_does_not_create_real_evidence(self):
        payload={'model':'deepseek-flash','choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'{"total":42,"count":3,"mean":14}'}}]}
        with patch('campuslab.ai_course.urlopen_once',return_value=(200,json.dumps(payload).encode())):
            run=ai.call_api(ai.make_task(),ai.preview(ai.make_task()),'test-key',True)
        self.assertEqual(run['category'],'ok')
        for code,category in [(400,'protocol'),(401,'authentication'),(402,'balance'),(404,'model_or_protocol'),(422,'model_or_protocol'),(429,'rate_limit'),(503,'server')]:
            with patch('campuslab.ai_course.urlopen_once',return_value=(code,b'{}')):
                self.assertEqual(ai.call_api(ai.make_task(),ai.preview(ai.make_task()),'x',True)['category'],category)

    def test_web_self_record_never_verifies_login(self):
        spec=ai.make_web_task()
        report=dict(schema=1,task_id=spec['id'],collected_at=datetime.now(timezone.utc).isoformat(),
            target=dict(requested=r'C:\Course\exercise',actual=r'C:\Course\exercise',exists=True),
            facts=dict(record=ai.web_record_template(spec)))
        report['facts']['record'].update(completed=True,checked_sources=True,response='{"total":42,"count":3,"mean":14}')
        result=ai.analyze_web(spec,report)
        self.assertTrue(result['learning_completed'])
        self.assertFalse(result['passed'])
        self.assertEqual(next(x for x in result['checks'] if x['id']=='web:login')['status'],'unknown')

    def test_truncated_and_missing_facts_rejected(self):
        report=self.report();del report['facts']['stdlib']
        with self.assertRaises(ValueError): ai.analyze(ai.make_task(),report)

    def test_response_headers_and_known_key_never_echo(self):
        class Response(BytesIO):
            status=200
        for length,content_type in [('100','application/json'),('2','text/html')]:
            response=Response(b'{}');response.headers=Message();response.headers['Content-Length']=length;response.headers['Content-Type']=content_type
            with patch('campuslab.ai_course.build_opener') as opener:
                opener.return_value.open.return_value=response
                with self.assertRaises(ValueError):ai.urlopen_once(object())
        payload={'model':'secret-known-key','choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'secret-known-key'}}]}
        with patch('campuslab.ai_course.urlopen_once',return_value=(200,json.dumps(payload).encode())):
            run=ai.call_api(ai.make_task(),ai.preview(ai.make_task()),'secret-known-key',True)
        self.assertNotIn('secret-known-key',json.dumps(run))
        for raw in (b'{"choices":[],"choices":[]}',b'[]',b'{"value":NaN}'):
            with patch('campuslab.ai_course.urlopen_once',return_value=(200,raw)):
                self.assertEqual(ai.call_api(ai.make_task(),ai.preview(ai.make_task()),'x',True)['category'],'protocol')

    def test_network_failure_categories(self):
        from urllib.error import URLError
        for error,category in [(TimeoutError(),'timeout'),(URLError('offline'),'network'),(OSError(),'runtime')]:
            with patch('campuslab.ai_course.urlopen_once',side_effect=error):
                self.assertEqual(ai.call_api(ai.make_task(),ai.preview(ai.make_task()),'x',True)['category'],category)
        self.assertEqual(ai.call_api(ai.make_task(),ai.preview(ai.make_task()),'',True)['category'],'unconfigured')

    def test_probe_preserves_identity_when_ssl_dependency_missing(self):
        import builtins,contextlib,io,runpy,sys
        original=builtins.__import__
        def without_ssl(name,*args,**kwargs):
            if name=='ssl':raise ModuleNotFoundError('No module named ssl')
            return original(name,*args,**kwargs)
        output=io.StringIO()
        with patch('builtins.__import__',side_effect=without_ssl),patch('sys.stdin',io.StringIO('{}')),contextlib.redirect_stdout(output):
            runpy.run_path(str(ai.Path(ai.__file__).with_name('ai_probe.py')),run_name='__main__')
        result=json.loads(output.getvalue())
        self.assertEqual(result['actual'],sys.executable)
        self.assertFalse(result['stdlib'])
        self.assertEqual(result['run']['category'],'dependency_missing')
        self.assertFalse(result['run']['attempted'])


if __name__=='__main__': unittest.main()
