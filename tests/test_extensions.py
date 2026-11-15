import unittest
from campuslab.chat import context
from campuslab.extensions import BY_ID, COURSES, LEGACY
import test_web


class ExtensionTest(unittest.TestCase):
    def test_catalog_separates_courses_and_existing_tools(self):
        value = context(dict(route='selection', step=0))
        self.assertEqual({x['scenario'] for x in value['supported_courses']}, set(COURSES))
        self.assertEqual({x['id'] for x in value['extension_tools']}, set(BY_ID))
        self.assertTrue(set(COURSES).isdisjoint(LEGACY))

    def test_tool_chat_has_guide_context_without_course_evidence(self):
        for tool in BY_ID:
            value = context(dict(route='extensions', step=0, extension=tool))
            self.assertEqual(value['extension']['id'], tool)
            self.assertNotIn('evidence', value)
            self.assertNotIn('course', value)
        with self.assertRaises(ValueError):
            context(dict(route='extensions', step=0, extension='not-a-tool'))
        with self.assertRaises(ValueError):
            context(dict(route='extensions', step=0, extension='deepseek-api', report={}))


class ExtensionWebTest(unittest.TestCase):
    setUpClass = classmethod(test_web.WebTest.setUpClass.__func__)
    tearDownClass = classmethod(test_web.WebTest.tearDownClass.__func__)
    request = test_web.WebTest.request
    def test_guides_are_reachable_without_creating_reports(self):
        import json
        value = json.load(self.request('/api/extensions'))
        self.assertEqual(len(value['guides']), 6)
        self.assertEqual(self.app.local_check.jobs, {})
        self.assertEqual(self.request('/extensions.js').status, 200)
        catalog = json.load(self.request('/api/catalog'))
        self.assertTrue(all(x['kind']=='extension' for x in catalog if x['scenario'] in LEGACY))
