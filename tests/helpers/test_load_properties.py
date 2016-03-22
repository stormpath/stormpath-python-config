from unittest import TestCase

from stormpath_config.helpers import _load_properties


class LoadPropertiesTest(TestCase):
    def test_load_empty_filename(self):
        self.assertEqual(_load_properties(''), {})

    def test_load_missing_properties_file(self):
        self.assertEqual(_load_properties('blahasdfadsf.properties'), {})

    def test_load_properties_file_with_comments(self):
        self.assertEqual(len(_load_properties('tests/assets/file-with-comments.properties').keys()), 1)

    def test_load_invalid_properties_file(self):
        self.assertEqual(_load_properties('tests/assets/invalid.properties'), {})
