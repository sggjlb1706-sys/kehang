"""Constructed presentation states; no live API or Agent execution."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from campuslab.guidance import plan
from campuslab.rules import task, analyze
from campuslab.dsh_course import collect as dsh_collect
from campuslab.ai_course import empty_run
import test_ai_course


class ContextualGuidanceTest(unittest.TestCase):
    def static_dsh(self, scenario='dsh-desktop'):
        spec=task(scenario)
        with tempfile.TemporaryDirectory() as folder:
            path=str(Path(folder)/('DeepSeek Harness.exe' if scenario=='dsh-desktop' else 'node.exe'))
            report=dsh_collect(spec,path)
        if scenario=='dsh-desktop':
            report['target'].update(exists=True,actual=path)
            report['facts']['installation'].update(exists=True,product='DeepSeek Harness',version=spec['software_version'],sha256='a'*64,error='')
        return spec,report

    def test_preparation_declaration_is_not_detection_evidence(self):
        for scenario in ('dsh-desktop','dsh-cli','deepseek-api'):
            spec=task(scenario)
            for prepared in ('unsure','missing','installed'):
                result=plan(spec,prepared=prepared)['contextual']
                self.assertIn('尚无检测报告',result['status'])
                self.assertIn('不是已验证事实',result['status'])
                self.assertIn('不',result['boundary'])
            with self.assertRaises(ValueError):plan(spec,prepared='success')

    def test_desktop_has_no_system_python_or_node_requirement(self):
        spec=task('dsh-desktop');context=plan(spec)['contextual']
        self.assertIn('桌面',context['title'])
        self.assertIn('不是本路线前置条件',' '.join(context['requirements']))
        self.assertNotIn('课程 Python',' '.join(context['requirements']))
        self.assertNotIn('package.json',' '.join(context['requirements']))

    def test_cli_uses_its_own_node_and_package(self):
        spec,report=self.static_dsh('dsh-cli')
        context=plan(spec,report=report)['contextual']
        self.assertIn('Node',' '.join(context['requirements']))
        self.assertIn('24.9.0',' '.join(context['requirements']))
        self.assertIn('package.json',' '.join(context['requirements']))
        self.assertEqual(context['next_title'],'CLI运行时')

    def test_static_desktop_points_to_workspace_not_reinstallation(self):
        spec,report=self.static_dsh();before=deepcopy(report)
        context=plan(spec,report=report)['contextual']
        self.assertEqual(context['next_title'],'专用练习目录')
        self.assertIn('尚无真实DSH任务摘要',context['status'])
        self.assertIn('没有',context['next_body'])
        self.assertFalse(analyze(spec,report)['passed'])
        self.assertEqual(report,before)

    def test_uninvoked_api_is_unknown_not_failed_deployment(self):
        spec=task('deepseek-api');report=test_ai_course.AICourseTests().report();report['facts']['run']=empty_run()
        context=plan(spec,report=report)['contextual']
        self.assertEqual(context['next_title'],'实际API响应')
        self.assertIn('没有实际API响应证据',context['status'])
        self.assertIn('不发送API',context['boundary'])
        self.assertIn('终端单次授权',context['next_body'])

    def test_actual_authentication_failure_and_pass_are_distinct(self):
        spec=task('deepseek-api');report=test_ai_course.AICourseTests().report()
        report['facts']['run'].update(category='authentication',http_status=401,model=None,role=None,finish_reason=None,content='')
        self.assertEqual(plan(spec,report=report)['contextual']['next_title'],'核对本次调用的认证问题')
        passed=test_ai_course.AICourseTests().report();before=deepcopy(passed)
        context=plan(spec,report=passed)['contextual']
        self.assertEqual(context['next_title'],'保留原始结果，同目标复检')
        self.assertEqual(passed,before)

    def test_explanation_modes_do_not_hide_context_or_weaken_rules(self):
        spec,report=self.static_dsh();original=deepcopy(spec)
        values=[plan(spec,mode,report=report,prepared='installed') for mode in ('novice','standard','quick')]
        self.assertTrue(all(value['contextual']==values[0]['contextual'] for value in values))
        self.assertTrue(all(any(action['title'].startswith('DSH任务的模型接入') for action in value['remediation']) for value in values))
        self.assertEqual(spec,original)


if __name__=='__main__':unittest.main()
