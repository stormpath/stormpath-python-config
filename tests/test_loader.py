from os import environ
from unittest import TestCase

from mock import patch

from stormpath_config.loader import ConfigLoader
from stormpath_config.strategies import ExtendConfigStrategy, \
    LoadAPIKeyConfigStrategy, \
    LoadAPIKeyFromConfigStrategy, \
    LoadEnvConfigStrategy, \
    LoadFileConfigStrategy, \
    ValidateClientConfigStrategy


class ConfigLoaderTest(TestCase):
    def setUp(self):
        client_config = {
            'application': {
                'name': 'CLIENT_CONFIG_APP',
                'href': None
            },
            'client': {
                'apiKey': {
                    'id': 'CLIENT_CONFIG_API_KEY_ID',
                    'secret': 'CLIENT_CONFIG_API_KEY_SECRET',
                }
            }
        }

        self.load_strategies = [
            # 1. Default configuration.
            LoadFileConfigStrategy('tests/assets/default_config.yml', must_exist=True),

            # 2. apiKey.properties file from ~/.stormpath directory.
            LoadAPIKeyConfigStrategy('tests/assets/apiKey.properties'),

            # 3. stormpath.[json or yaml] file from ~/.stormpath
            #    directory.
            LoadFileConfigStrategy('tests/assets/stormpath.yml'),

            # 4. apiKey.properties file from application directory.
            LoadAPIKeyConfigStrategy('tests/assets/no_apiKey.properties'),

            # 5. stormpath.[json or yaml] file from application
            #    directory.
            LoadFileConfigStrategy('tests/assets/stormpath.json'),

            # 6. Environment variables.
            LoadEnvConfigStrategy(prefix='STORMPATH'),

            # 7. Configuration provided through the SDK client
            #    constructor.
            ExtendConfigStrategy(extend_with=client_config)
        ]
        self.post_processing_strategies = [
            # Post-processing: If the key client.apiKey.file isn't
            # empty, then a apiKey.properties file should be loaded
            # from that path.
            LoadAPIKeyFromConfigStrategy(),
        ]
        self.validation_strategies = [
            # Post-processing: Validation
            ValidateClientConfigStrategy()
        ]

    @patch.dict(environ, {
        'STORMPATH_CLIENT_APIKEY_ID': 'env api key id',
        'STORMPATH_CLIENT_APIKEY_SECRET': 'env api key secret',
        'STORMPATH_CLIENT_CACHEMANAGER_DEFAULTTTI': '303',
        'STORMPATH_APPLICATION_NAME': 'My app',
    })
    def test_config_loader(self):
        cl = ConfigLoader(self.load_strategies, self.post_processing_strategies, self.validation_strategies)
        config = cl.load()

        self.assertEqual(config['client']['apiKey']['id'], 'CLIENT_CONFIG_API_KEY_ID')
        self.assertEqual(config['client']['apiKey']['secret'], 'CLIENT_CONFIG_API_KEY_SECRET')
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 302)
        self.assertEqual(config['client']['cacheManager']['defaultTti'], 303)
        self.assertEqual(config['application']['name'], 'CLIENT_CONFIG_APP')
