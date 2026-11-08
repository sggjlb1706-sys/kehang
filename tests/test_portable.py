from copy import deepcopy
import unittest
from campuslab.rules import task, seal
from campuslab.portable import export_package, import_package, guide_html


class PortableTest(unittest.TestCase):
    def test_snapshot_roundtrip_and_edit_rejection(self):
        spec=task()
        package=export_package(spec)
        self.assertEqual(import_package(package),spec)
        changed=deepcopy(package); changed['task']['title']='changed'
        with self.assertRaises(ValueError): import_package(changed)
        changed=deepcopy(package); changed['task']['verify']='arbitrary-command'
        changed['task']=seal(changed['task'])
        with self.assertRaises(ValueError): import_package(changed)

    def test_offline_guide_escapes_teacher_text_and_preserves_identity(self):
        spec=task(title='<script>alert(1)</script>')
        html=guide_html(spec)
        self.assertIn(spec['id'],html)
        self.assertIn('&lt;script&gt;',html)
        self.assertNotIn('<script>',html)
        self.assertIn('viewport',html)
        self.assertIn('文件传递',html)

    def test_unknown_package_shape_rejected(self):
        for value in ({},[],dict(schema=1,kind='course',task=task())):
            with self.assertRaises(ValueError):import_package(value)


if __name__=='__main__':unittest.main()
