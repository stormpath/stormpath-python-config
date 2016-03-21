from unittest import TestCase

from stormpath_config.helpers import _extend_dict


class ExtendDictTest(TestCase):
    def test_extend_dict(self):
        original = {
            'a': 1,
            'b': {
                "A": 1,
                "B": 2
            }
        }

        extend_with = {
            'b': {
                "B": 3,
                "C": 4
            },
            'c': 3
        }
        extend_with_copy = dict(extend_with)
        returned = _extend_dict(original, extend_with)

        self.assertEqual(returned, original)
        self.assertEqual(extend_with, extend_with_copy)
        self.assertEqual(original, {'a': 1, 'c': 3, 'b': {'A': 1, 'B': 3, 'C': 4}})
