from os import environ
from unittest import TestCase

from mock import patch

from stormpath_config.strategies import LoadEnvConfigStrategy


class LoadEnvConfigStrategyTest(TestCase):
    @patch.dict(environ, {
        'STORMPATH_CLIENT_APIKEY_ID': 'env api key id',
        'STORMPATH_ALIAS': 'env api key secret',
        'STORMPATH_CLIENT_CACHEMANAGER_DEFAULTTTI': '301',
        'STORMPATH_APPLICATION_NAME': 'env application name',
    })
    def test_stormpath_config_environment(self):
        config = {
            'client': {
                'apiKey': {'id': 'api key id', 'secret': 'api key secret'},
                'cacheManager': {'defaultTtl': 300, 'defaultTti': 300}
            },
            'application': {'name': 'App Name'},
            'key': ['value1', 'value2', 'value3']
        }

        lecs = LoadEnvConfigStrategy('STORMPATH', {'STORMPATH_CLIENT_APIKEY_SECRET': 'STORMPATH_ALIAS'})
        config = lecs.process(config)

        self.assertEqual(config['client']['apiKey']['id'], 'env api key id')
        self.assertEqual(config['client']['apiKey']['secret'], 'env api key secret')
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 300)
        self.assertEqual(config['client']['cacheManager']['defaultTti'], 301)
        self.assertEqual(config['key'], ['value1', 'value2', 'value3'])
        self.assertEqual(config['application']['name'], 'env application name')
