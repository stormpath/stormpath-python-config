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


class EdgeCasesTest(TestCase):
    def test_config_extending(self):
        client_config = {
            'client': {
                'apiKey': {
                    'id': 'CLIENT_CONFIG_API_KEY_ID',
                    'secret': 'CLIENT_CONFIG_API_KEY_SECRET',
                }
            }
        }

        load_strategies = [
            # 1. We load the default configuration.
            LoadFileConfigStrategy('tests/assets/default_config.yml', must_exist=True),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            LoadEnvConfigStrategy(prefix='STORMPATH'),
            # 7. Configuration provided through the SDK client
            #    constructor.
            ExtendConfigStrategy(extend_with=client_config)
        ]
        post_processing_strategies = [LoadAPIKeyFromConfigStrategy()]
        validation_strategies = [ValidateClientConfigStrategy()]

        cl = ConfigLoader(load_strategies, post_processing_strategies, validation_strategies)
        config = cl.load()

        self.assertTrue('baseUrl' in config['client'])

    @patch.dict(environ, {
        'STORMPATH_CLIENT_APIKEY_ID': 'greater order id',
        'STORMPATH_CLIENT_APIKEY_SECRET': 'greater order secret',
    })
    def test_api_key_file_from_config_with_lesser_loading_order(self):
        """Let's say we load the default configuration, and then
        stormpath.yml file with client.apiKey.file key. Then we provide
        API key ID and secret through environment variables - which
        have greater loading order than the stormpath.yml.
        """
        load_strategies = [
            # 1. We load the default configuration.
            LoadFileConfigStrategy('tests/assets/default_config.yml', must_exist=True),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            # 3. We load stormpath.yml file with client.apiKey.file
            LoadFileConfigStrategy('tests/assets/apiKeyFile.yml'),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            # 6. We load API key id and secret from environment
            #    variables.
            LoadEnvConfigStrategy(prefix='STORMPATH'),
            ExtendConfigStrategy(extend_with={})
        ]
        post_processing_strategies = [LoadAPIKeyFromConfigStrategy()]
        validation_strategies = [ValidateClientConfigStrategy()]

        cl = ConfigLoader(load_strategies, post_processing_strategies, validation_strategies)
        config = cl.load()

        self.assertEqual(config['client']['apiKey']['id'], 'greater order id')
        self.assertEqual(config['client']['apiKey']['secret'], 'greater order secret')
        self.assertFalse('file' in config['client']['apiKey'])

    def test_api_key_from_config_with_lesser_loading_order(self):
        """Similar to the previous test, but with apiKey key.
        """
        client_config = {
            'client': {
                'apiKey': {
                    'id': 'CLIENT_CONFIG_API_KEY_ID',
                    'secret': 'CLIENT_CONFIG_API_KEY_SECRET',
                }
            }
        }

        load_strategies = [
            # 1. We load the default configuration.
            LoadFileConfigStrategy('tests/assets/default_config.yml', must_exist=True),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            # 3. We load stormpath.yml file with client.apiKey.file
            LoadFileConfigStrategy('tests/assets/apiKeyApiKey.json'),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            LoadEnvConfigStrategy(prefix='STORMPATH'),
            # 7. Configuration provided through the SDK client
            #    constructor.
            ExtendConfigStrategy(extend_with=client_config)
        ]
        post_processing_strategies = [LoadAPIKeyFromConfigStrategy()]
        validation_strategies = [ValidateClientConfigStrategy()]

        cl = ConfigLoader(load_strategies, post_processing_strategies, validation_strategies)
        config = cl.load()

        self.assertEqual(config['client']['apiKey']['id'], 'CLIENT_CONFIG_API_KEY_ID')
        self.assertEqual(config['client']['apiKey']['secret'], 'CLIENT_CONFIG_API_KEY_SECRET')
