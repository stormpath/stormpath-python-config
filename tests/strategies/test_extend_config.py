from unittest import TestCase

from stormpath_config.strategies import ExtendConfigStrategy


class ExtendConfigStrategyTest(TestCase):
    def test_extend_config(self):
        config = {
            'client': {
                'apiKey': {'id': 'api key id', 'secret': 'api key secret'},
                'cacheManager': {'defaultTtl': 300, 'defaultTti': 300},
            },
            'application': {'name': 'App Name'},
            'key': ['value1', 'value2', 'value3'],
        }
        extend_with = {
            'client': {
                'apiKey': {'id': 'extended api key id'},
                'cacheManager': {'defaultTtl': 301, 'defaultTti': 301, 'k': 1},
            },
            'application': {'name': 'Extended App Name'},
        }

        lecs = ExtendConfigStrategy(extend_with)
        lecs.process(config)

        self.assertEqual(config['client']['apiKey']['id'], 'extended api key id')
        self.assertEqual(config['client']['apiKey']['secret'], 'api key secret')
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 301)
        self.assertEqual(config['client']['cacheManager']['defaultTti'], 301)
        self.assertEqual(config['client']['cacheManager']['k'], 1)
        self.assertEqual(config['key'], ['value1', 'value2', 'value3'])
        self.assertEqual(config['application']['name'], 'Extended App Name')
