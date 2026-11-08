"""Independent review reproductions; all inputs are constructed fixtures."""
import json
import unittest
from campuslab.preparation import resolve_need
from campuslab.torch_course import analyze
from test_torch_course import evidence
import test_web


class ReviewRegressions(unittest.TestCase):
    setUpClass=classmethod(test_web.WebTest.setUpClass.__func__)
    tearDownClass=classmethod(test_web.WebTest.tearDownClass.__func__)
    request=test_web.WebTest.request

    def test_spaced_teacher_gpu_requirement_cannot_downgrade_to_cpu(self):
        for text in ('PyTorch老师要求 GPU 运行，我想先用 CPU',
                     '深度学习老师要求 CUDA，但我只能 CPU',
                     'PyTorch 课程要求 GPU，先检测 CPU 和 GPU'):
            with self.subTest(text=text):
                proposal=resolve_need(text)
                self.assertTrue(proposal['constraints']['gpu_required'])
                self.assertNotEqual(proposal['scenario'],'pytorch-cpu')

    def test_conflict_cannot_be_bypassed_by_cpu_clarification(self):
        result=resolve_need('PyTorch老师要求 GPU 运行，我想先用 CPU','pytorch-cpu')
        self.assertNotEqual(result['scenario'],'pytorch-cpu')

    def test_non_cuda_build_string_cannot_pass_gpu_course(self):
        for build in ('CPU-only','garbage','12',''):
            spec,report=evidence(True);report['facts']['gpu']['build']=build
            with self.subTest(build=build):self.assertFalse(analyze(spec,report)['passed'])

    def test_text_error_path_is_redacted_before_json_serialization(self):
        value=json.load(self.request('/api/preview',dict(error=r'C:\Users\Alice\private.txt api_key=fixture-secret')))
        preview=json.loads(value['preview'])
        self.assertNotIn('Alice',preview['user_error'])
        self.assertNotIn('fixture-secret',preview['user_error'])


if __name__=='__main__':unittest.main()
