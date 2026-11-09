from copy import deepcopy
import unittest

from campuslab.preparation import resolve_need, recommend, validate_hardware


def hardware():
    field = lambda value: dict(value=value, source='constructed-test', collected_at='2026-11-08T10:00:00+08:00', reason='')
    return dict(schema=1, kind='hardware', collected_at='2026-11-08T10:00:00+08:00',
                tool_runtime=r'C:\Tool\python.exe', drive='D:\\', fields=dict(
                    os=field('Windows 11'), ram_bytes=field(16*1024**3),
                    storage_free_bytes=field(100*1024**3),
                    gpus=field([dict(id='GPU-test', name='Test GPU', vram_bytes=8*1024**3)])))


class PreparationTest(unittest.TestCase):
    def test_supported_goals_and_confirmation(self):
        for text, expected in [('我想学Python', 'python-basics'), ('我想配置Node.js', 'node-basics'),
                               ('运行本地模型', 'local-qwen'), ('PyTorch CPU', 'pytorch-cpu'),
                               ('PyTorch课程要求GPU', 'pytorch-gpu'), ('虚拟机Linux实验', 'vm-linux')]:
            with self.subTest(text=text):
                result = resolve_need(text)
                self.assertEqual(result['status'], 'recognized')
                self.assertEqual(result['scenario'], expected)
                self.assertTrue(result['requires_confirmation'])

    def test_ambiguity_errors_conflicts_and_catalog(self):
        self.assertEqual(resolve_need('我想学深度学习')['status'], 'clarify')
        self.assertEqual(resolve_need('安装失败了')['status'], 'clarify')
        self.assertTrue(resolve_need('ModuleNotFoundError')['error_help'])
        self.assertEqual(resolve_need('Python和Node都要安装')['status'], 'conflict')
        self.assertEqual(resolve_need('课程要求本地模型但我只用云端')['status'], 'conflict')
        self.assertEqual(resolve_need('课程要求GPU但没有GPU')['status'], 'conflict')
        for text in ('MySQL数据库', 'Hadoop大数据', '云计算'):
            self.assertEqual(resolve_need(text)['status'], 'catalog_only')
        for text, scenario in [('Java JDK', 'java-jdk'), ('Jupyter Notebook', 'notebook-data'),
                               ('Python数据分析Notebook', 'notebook-data'), ('SQLite SQL', 'sqlite-basics'),
                               ('DeepSeek API', 'deepseek-api'), ('DeepSeek网页', 'ai-web-deepseek'),
                               ('DSH桌面', 'dsh-desktop'), ('DSH CLI', 'dsh-cli')]:
            self.assertEqual(resolve_need(text)['scenario'], scenario)
        for text in ('DeepSeek', 'DSH'):
            self.assertEqual(resolve_need(text)['status'], 'clarify')
        self.assertEqual(resolve_need('Linux Hadoop')['status'], 'catalog_only')
        self.assertEqual(resolve_need('Java JDK Hadoop')['status'], 'catalog_only')
        self.assertEqual(resolve_need('课程要求本地DeepSeek API')['status'], 'conflict')
        self.assertEqual(resolve_need('必须GPU Notebook')['status'], 'conflict')
        self.assertEqual(resolve_need('运行本地模型但是我只用云端')['status'], 'conflict')

    def test_clarification_cannot_select_arbitrary_code(self):
        self.assertEqual(resolve_need('深度学习', 'pytorch-gpu')['scenario'], 'pytorch-gpu')
        with self.assertRaises(ValueError): resolve_need('深度学习', 'run-shell')
        with self.assertRaises(ValueError): resolve_need('Python', 'node-basics')

    def test_recommendations_are_evidence_bound_and_never_pass(self):
        spec = dict(scenario='local-qwen', model={'local_required':True})
        report = hardware()
        self.assertEqual(recommend(spec, report)['status'], 'ready_to_check')
        report['fields']['gpus']['value'] = []
        self.assertEqual(recommend(spec, report)['status'], 'confirm_route')
        self.assertIn('CPU', ' '.join(recommend(spec, report)['actions']))
        self.assertIn('不能替代', ' '.join(recommend(spec, report)['alternatives']))
        report['fields']['ram_bytes']['value'] = 2*1024**3
        self.assertEqual(recommend(spec, report)['status'], 'resource_pressure')
        report['fields']['ram_bytes']['value'] = None
        report['fields']['ram_bytes']['reason'] = 'test: query unavailable'
        self.assertEqual(recommend(spec, report)['status'], 'unknown')
        self.assertFalse(recommend(spec, report)['environment_passed'])
        self.assertTrue(recommend(spec, report)['requirement_unmodified'])
        self.assertEqual(recommend(spec)['status'], 'unknown')

    def test_hardware_shape_and_boolean_numbers_rejected(self):
        for mutate in (lambda h:h['fields'].pop('gpus'),
                       lambda h:h['fields']['ram_bytes'].update(value=True),
                       lambda h:h['fields']['storage_free_bytes'].update(value=-1),
                       lambda h:h.update(collected_at='2026-11-08'),
                       lambda h:h['fields']['gpus'].update(value=[dict(id='x',name='x',vram_bytes=False)])):
            report = deepcopy(hardware()); mutate(report)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): validate_hardware(report)


if __name__ == '__main__': unittest.main()
