from unittest import TestCase

from stormpath_config.helpers import to_camel_case


class ToCamelCaseTest(TestCase):
    def test_to_camel_case(self):
        self.assertEqual(to_camel_case('hithere'), 'hithere')
        self.assertEqual(to_camel_case('hi there'), 'hi there')
        self.assertEqual(to_camel_case('hi_there'), 'hiThere')
        self.assertEqual(to_camel_case('hi_there_yo'), 'hiThereYo')
