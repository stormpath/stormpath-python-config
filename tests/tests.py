import os
from unittest import TestCase
from stormpath_config.loader import ConfigLoader
from stormpath_config.strategies import *


class LoadFileConfigStrategyTest(TestCase):
    def test_load_file_config(self):
        lfcs = LoadFileConfigStrategy('default_config.yml')
        config = lfcs.process()

        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 300)

    def test_load_file_config_with_existing_config(self):
        lfcs = LoadFileConfigStrategy('stormpath.yml', must_exist=False)
        existing_config = {'application': {'name': 'App Name'}, 'key': 'value'}
        config = lfcs.process(existing_config)

        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 301)
        self.assertEqual(config['application']['name'], 'MY_APP')
        self.assertEqual(config['key'], 'value')

    def test_load_non_existent_file_config_with_existing_config(self):
        lfcs = LoadFileConfigStrategy('i-do-not-exist.yml', must_exist=False)
        existing_config = {'application': {'name': 'App Name'}, 'key': 'value'}
        config = lfcs.process(existing_config)

        self.assertEqual(config['application']['name'], 'App Name')
        self.assertEqual(config['key'], 'value')

    def test_load_file_json_config_with_existing_config(self):
        config = {'application': {'name': 'App Name'}, 'key': 'value'}
        lfcs = LoadFileConfigStrategy('stormpath.json')
        config = lfcs.process(config)
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 302)
        self.assertEqual(
            config['client']['apiKey']['id'], 'MY_JSON_CONFIG_API_KEY_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'],
            'MY_JSON_CONFIG_API_KEY_SECRET')
        self.assertEqual(config['client']['connectionTimeout'], None)
        self.assertEqual(config['application']['name'], 'MY_JSON_APP')
        self.assertEqual(config['key'], 'value')


class LoadAPIKeyConfigStrategyTest(TestCase):
    def test_load_api_key_config(self):
        lapcs = LoadAPIKeyConfigStrategy('apiKey.properties')
        config = lapcs.process()

        self.assertEqual(
            config['client']['apiKey']['id'], 'API_KEY_PROPERTIES_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'], 'API_KEY_PROPERTIES_SECRET')

    def test_load_empty_api_key_config(self):
        lapcs = LoadAPIKeyConfigStrategy('empty_apiKey.properties')
        config = lapcs.process()

        self.assertEqual(config, {})

    def test_load_empty_api_key_config_must_exist(self):
        lapcs = LoadAPIKeyConfigStrategy(
            'empty_apiKey.properties', must_exist=True)

        with self.assertRaises(Exception):
            lapcs.process()

    def test_api_key_properties_file_after_default_config(self):
        lfcs = LoadFileConfigStrategy('default_config.yml')
        config = lfcs.process()
        lapcs = LoadAPIKeyConfigStrategy('apiKey.properties')
        returned_config = lapcs.process(config)

        self.assertEqual(returned_config, config)
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 300)
        self.assertEqual(
            config['client']['apiKey']['id'], 'API_KEY_PROPERTIES_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'], 'API_KEY_PROPERTIES_SECRET')

    def test_empty_api_key_properties_file_after_default_config(self):
        lfcs = LoadFileConfigStrategy('default_config.yml')
        config = lfcs.process()
        lapcs = LoadAPIKeyConfigStrategy('empty_apiKey.properties')
        returned_config = lapcs.process(config)

        self.assertEqual(returned_config, config)
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 300)
        self.assertIsNone(config['client']['apiKey']['id'])
        self.assertIsNone(config['client']['apiKey']['secret'])


class LoadEnvConfigStrategyTest(TestCase):
    def test_stormpath_config_environment(self):
        config = {
            'client': {
                'apiKey': {'id': 'api key id', 'secret': 'api key secret'},
                'cacheManager': {'defaultTtl': 300, 'defaultTti': 300}
            },
            'application': {'name': 'App Name'},
            'key': ['value1', 'value2', 'value3']
        }
        os.environ["STORMPATH_CLIENT_APIKEY_ID"] = "env api key id"
        os.environ["STORMPATH_ALIAS"] = "env api key secret"
        os.environ["STORMPATH_CLIENT_CACHEMANAGER_DEFAULTTTI"] = "301"
        os.environ["STORMPATH_APPLICATION_NAME"] = "env application name"
        lecs = LoadEnvConfigStrategy(
            'STORMPATH', {"STORMPATH_CLIENT_APIKEY_SECRET": "STORMPATH_ALIAS"})
        config = lecs.process(config)

        self.assertEqual(config['client']['apiKey']['id'], 'env api key id')
        self.assertEqual(
            config['client']['apiKey']['secret'], 'env api key secret')
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 300)
        self.assertEqual(config['client']['cacheManager']['defaultTti'], 301)
        self.assertEqual(config['key'], ['value1', 'value2', 'value3'])
        self.assertEqual(config['application']['name'], 'env application name')


class ConfigLoaderTest(TestCase):
    def setUp(self):
        client_config = {
            "application": {
                "name": "CLIENT_CONFIG_APP",
                "href": None
            },
            "apiKey": {
                "id": "CLIENT_CONFIG_API_KEY_ID",
                "secret": "CLIENT_CONFIG_API_KEY_SECRET",
            }
        }

        self.strategies = [
            # 1. Default configuration.
            LoadFileConfigStrategy('default_config.yml', must_exist=True),

            # 2. apiKey.properties file from ~/.stormpath directory.
            LoadAPIKeyConfigStrategy('apiKey.properties'),

            # 3. stormpath.[json or yaml] file from ~/.stormpath
            #    directory.
            LoadFileConfigStrategy('stormpath.yml'),

            # 4. apiKey.properties file from application directory.
            LoadAPIKeyConfigStrategy('no_apiKey.properties'),

            # 5. stormpath.[json or yaml] file from application
            #    directory.
            LoadFileConfigStrategy('stormpath.json'),

            # 6. Environment variables.
            LoadEnvConfigStrategy(prefix='STORMPATH'),

            # 7. Configuration provided through the SDK client
            #    constructor.
            ExtendConfigStrategy(extend_with=client_config),

            # Post-processing: If the key client.apiKey.file isn't
            # empty, then a apiKey.properties file should be loaded
            # from that path.
            LoadAPIKeyFromConfigStrategy(),

            # Post-processing: If an apiKey key is set, then this key
            # should be mapped to the key client.apiKey.
            MoveAPIKeyToClientAPIKeyStrategy(),

            # Post-processing: Validation
            ValidateClientConfigStrategy(),
        ]
        os.environ["STORMPATH_CLIENT_APIKEY_ID"] = "env api key id"
        os.environ["STORMPATH_CLIENT_APIKEY_SECRET"] = "env api key secret"
        os.environ["STORMPATH_CLIENT_CACHEMANAGER_DEFAULTTTI"] = "303"

    def test_config_loader(self):
        cl = ConfigLoader(self.strategies)
        config = cl.load()

        self.assertEqual(
            config['client']['apiKey']['id'], 'CLIENT_CONFIG_API_KEY_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'],
            'CLIENT_CONFIG_API_KEY_SECRET')
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 302)
        self.assertEqual(config['client']['cacheManager']['defaultTti'], 303)
        self.assertEqual(config['application']['name'], 'CLIENT_CONFIG_APP')


class EdgeCasesShowCaseTest(TestCase):
    def test_config_extending(self):
        """There is only default config and the config provided through
        the client constructor. How should client config extend the
        default?
        """
        client_config = {
            'client': {
                'apiKey': {
                    'id': 'CLIENT_CONFIG_API_KEY_ID',
                    'secret': 'CLIENT_CONFIG_API_KEY_SECRET',
                }
            }
        }

        strategies = [
            # 1. We load the default configuration.
            LoadFileConfigStrategy('default_config.yml', must_exist=True),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            LoadEnvConfigStrategy(prefix='STORMPATH'),
            # 7. Configuration provided through the SDK client
            #    constructor.
            ExtendConfigStrategy(extend_with=client_config),
            LoadAPIKeyFromConfigStrategy(),
            MoveAPIKeyToClientAPIKeyStrategy(),
            ValidateClientConfigStrategy(),
        ]

        cl = ConfigLoader(strategies)
        config = cl.load()

        # Client config didn't contain 'baseUrl' key in the 'client.
        # When default config was updated by client config, the
        # 'baseUrl' key was deleted. This is how Python's update()
        # method work. Also, it seems that this is how jQuery's extend
        # work: http://jsfiddle.net/L11q3LqL/
        self.assertFalse('baseUrl' in config['client'])

    def test_api_key_file_from_config_with_lesser_loading_order(self):
        """Let's say we load the default configuration, and then
        stormpath.yml file with client.apiKey.file key. Then we provide
        API key ID and secret through environment variables - which
        have greater loading order than the stormpath.yml. Because
        of the post processing, API key we specified in environment
        variables will be overriden with API key specified in file
        defined in stormpath.yml.
        """
        os.environ["STORMPATH_CLIENT_APIKEY_ID"] = "greater order id"
        os.environ["STORMPATH_CLIENT_APIKEY_SECRET"] = "greater order secret"

        strategies = [
            # 1. We load the default configuration.
            LoadFileConfigStrategy('default_config.yml', must_exist=True),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            # 3. We load stormpath.yml file with client.apiKey.file
            LoadFileConfigStrategy('apiKeyFile.yml'),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            # 6. We load API key id and secret from environment
            #    variables.
            LoadEnvConfigStrategy(prefix='STORMPATH'),
            ExtendConfigStrategy(extend_with={}),
            LoadAPIKeyFromConfigStrategy(),
            MoveAPIKeyToClientAPIKeyStrategy(),
            ValidateClientConfigStrategy(),
        ]

        cl = ConfigLoader(strategies)
        config = cl.load()

        # client.apiKey will have value user wouldn't expect. Maybe we
        # should do post processing after every load strategy and
        # delete client.apiKey.file at the end of each post processing?
        self.assertEqual(
            config['client']['apiKey']['id'], 'API_KEY_PROPERTIES_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'], 'API_KEY_PROPERTIES_SECRET')
        self.assertEqual(
            config['client']['apiKey']['file'], 'apiKey.properties')

    def test_api_key_from_config_with_lesser_loading_order(self):
        """Similar to the previous test, but with apiKey key. Post
        processing will move apiKey key to client.apiKey key if such
        key exists. Because of this, it is possible to override a key
        with greater loading order.
        """
        client_config = {
            'client': {
                'apiKey': {
                    'id': 'CLIENT_CONFIG_API_KEY_ID',
                    'secret': 'CLIENT_CONFIG_API_KEY_SECRET',
                }
            }
        }

        strategies = [
            # 1. We load the default configuration.
            LoadFileConfigStrategy('default_config.yml', must_exist=True),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            # 3. We load stormpath.yml file with client.apiKey.file
            LoadFileConfigStrategy('apiKeyApiKey.json'),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            LoadEnvConfigStrategy(prefix='STORMPATH'),
            # 7. Configuration provided through the SDK client
            #    constructor.
            ExtendConfigStrategy(extend_with=client_config),
            LoadAPIKeyFromConfigStrategy(),
            MoveAPIKeyToClientAPIKeyStrategy(),
            ValidateClientConfigStrategy(),
        ]

        cl = ConfigLoader(strategies)
        config = cl.load()

        # client.apiKey will have value user wouldn't expect. Maybe we
        # should do post processing after every load strategy and
        # delete apiKey at the end of each post processing?
        self.assertEqual(
            config['client']['apiKey']['id'], 'MY_JSON_CONFIG_API_KEY_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'],
            'MY_JSON_CONFIG_API_KEY_SECRET')
