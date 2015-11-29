import os
from unittest import TestCase

from base import *
from stormpath_config.loader import ConfigLoader
from stormpath_config.strategies import *
from stormpath_config.strategies import _extend_dict


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
        self.assertEqual(
            original, {'a': 1, 'c': 3, 'b': {'A': 1, 'B': 3, 'C': 4}})


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


class ExtendConfigStrategyTest(TestCase):
    def test_extend_config(self):
        config = {
            'client': {
                'apiKey': {'id': 'api key id', 'secret': 'api key secret'},
                'cacheManager': {'defaultTtl': 300, 'defaultTti': 300}
            },
            'application': {'name': 'App Name'},
            'key': ['value1', 'value2', 'value3']
        }
        extend_with = {
            'client': {
                'apiKey': {'id': 'extended api key id'},
                'cacheManager': {'defaultTtl': 301, 'defaultTti': 301, 'k': 1}
            },
            'application': {'name': 'Extended App Name'}
        }

        lecs = ExtendConfigStrategy(extend_with)
        lecs.process(config)

        self.assertEqual(
            config['client']['apiKey']['id'], 'extended api key id')
        self.assertEqual(
            config['client']['apiKey']['secret'], 'api key secret')
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 301)
        self.assertEqual(config['client']['cacheManager']['defaultTti'], 301)
        self.assertEqual(config['client']['cacheManager']['k'], 1)
        self.assertEqual(config['key'], ['value1', 'value2', 'value3'])
        self.assertEqual(config['application']['name'], 'Extended App Name')


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

        self.load_strategies = [
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
            ExtendConfigStrategy(extend_with=client_config)
        ]
        self.post_processing_strategies = [
            # Post-processing: If the key client.apiKey.file isn't
            # empty, then a apiKey.properties file should be loaded
            # from that path.
            LoadAPIKeyFromConfigStrategy(),

            # Post-processing: If an apiKey key is set, then this key
            # should be mapped to the key client.apiKey.
            MoveAPIKeyToClientAPIKeyStrategy()
        ]
        self.validation_strategies = [
            # Post-processing: Validation
            ValidateClientConfigStrategy()
        ]
        os.environ["STORMPATH_CLIENT_APIKEY_ID"] = "env api key id"
        os.environ["STORMPATH_CLIENT_APIKEY_SECRET"] = "env api key secret"
        os.environ["STORMPATH_CLIENT_CACHEMANAGER_DEFAULTTTI"] = "303"
        os.environ["STORMPATH_APPLICATION_NAME"] = "My app"

    def test_config_loader(self):
        cl = ConfigLoader(
            self.load_strategies,
            self.post_processing_strategies,
            self.validation_strategies)
        config = cl.load()

        self.assertEqual(
            config['client']['apiKey']['id'], 'CLIENT_CONFIG_API_KEY_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'],
            'CLIENT_CONFIG_API_KEY_SECRET')
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 302)
        self.assertEqual(config['client']['cacheManager']['defaultTti'], 303)
        self.assertEqual(config['application']['name'], 'CLIENT_CONFIG_APP')


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
            LoadFileConfigStrategy('default_config.yml', must_exist=True),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            LoadEnvConfigStrategy(prefix='STORMPATH'),
            # 7. Configuration provided through the SDK client
            #    constructor.
            ExtendConfigStrategy(extend_with=client_config)
        ]
        post_processing_strategies = [
            LoadAPIKeyFromConfigStrategy(),
            MoveAPIKeyToClientAPIKeyStrategy()
        ]
        validation_strategies = [ValidateClientConfigStrategy()]

        cl = ConfigLoader(
            load_strategies,
            post_processing_strategies,
            validation_strategies)
        config = cl.load()

        self.assertTrue('baseUrl' in config['client'])

    def test_api_key_file_from_config_with_lesser_loading_order(self):
        """Let's say we load the default configuration, and then
        stormpath.yml file with client.apiKey.file key. Then we provide
        API key ID and secret through environment variables - which
        have greater loading order than the stormpath.yml.
        """
        os.environ["STORMPATH_CLIENT_APIKEY_ID"] = "greater order id"
        os.environ["STORMPATH_CLIENT_APIKEY_SECRET"] = "greater order secret"

        load_strategies = [
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
            ExtendConfigStrategy(extend_with={})
        ]
        post_processing_strategies = [
            LoadAPIKeyFromConfigStrategy(),
            MoveAPIKeyToClientAPIKeyStrategy()
        ]
        validation_strategies = [ValidateClientConfigStrategy()]

        cl = ConfigLoader(
            load_strategies,
            post_processing_strategies,
            validation_strategies)
        config = cl.load()

        self.assertEqual(
            config['client']['apiKey']['id'], 'greater order id')
        self.assertEqual(
            config['client']['apiKey']['secret'], 'greater order secret')
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
            LoadFileConfigStrategy('default_config.yml', must_exist=True),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            # 3. We load stormpath.yml file with client.apiKey.file
            LoadFileConfigStrategy('apiKeyApiKey.json'),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            LoadEnvConfigStrategy(prefix='STORMPATH'),
            # 7. Configuration provided through the SDK client
            #    constructor.
            ExtendConfigStrategy(extend_with=client_config)
        ]
        post_processing_strategies = [
            LoadAPIKeyFromConfigStrategy(),
            MoveAPIKeyToClientAPIKeyStrategy()
        ]
        validation_strategies = [ValidateClientConfigStrategy()]

        cl = ConfigLoader(
            load_strategies,
            post_processing_strategies,
            validation_strategies)
        config = cl.load()

        self.assertEqual(
            config['client']['apiKey']['id'], 'CLIENT_CONFIG_API_KEY_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'],
            'CLIENT_CONFIG_API_KEY_SECRET')


class EnrichClientFromRemoteConfigStrategyTest(TestCase):
    def setUp(self):
        self.stormpath_app = Application(
            'Stormpath',
            'https://api.stormpath.com/v1/applications/stormpath')
        self.application = Application(
            'My named application',
            'https://api.stormpath.com/v1/applications/a')

    def test_enrich_client_from_remote_config_app_by_invalid_href(self):
        def _create_client_from_config(config):
            return Client([self.application])

        config = {
            'application': {
                'href': 'invalid'
            }
        }

        ecfrcs = EnrichClientFromRemoteConfigStrategy(
            client_factory=_create_client_from_config)

        with self.assertRaises(Exception):
            ecfrcs.process(config)

    def test_enrich_client_from_remote_config_app_by_href(self):
        def _create_client_from_config(config):
            return Client([self.application])

        config = {
            'application': {
                'href': 'https://api.stormpath.com/v1/applications/a'
            }
        }

        ecfrcs = EnrichClientFromRemoteConfigStrategy(
            client_factory=_create_client_from_config)

        ecfrcs.process(config)
        self.assertEqual(config['application'], self.application)

    def test_enrich_client_from_remote_config_app_by_invalid_name(self):
        def _create_client_from_config(config):
            return Client([self.application])

        config = {
            'application': {
                'name': 'invalid'
            }
        }

        ecfrcs = EnrichClientFromRemoteConfigStrategy(
            client_factory=_create_client_from_config)

        with self.assertRaises(Exception):
            ecfrcs.process(config)

    def test_enrich_client_from_remote_config_app_by_name(self):
        def _create_client_from_config(config):
            return Client([self.application])

        config = {
            'application': {
                'name': 'My named application'
            }
        }

        ecfrcs = EnrichClientFromRemoteConfigStrategy(
            client_factory=_create_client_from_config)

        ecfrcs.process(config)
        self.assertEqual(config['application'], self.application)

    def test_enrich_client_from_remote_config_default_app_no_app(self):
        def _create_client_from_config(config):
            return Client([self.stormpath_app])

        config = {
            'application': {}
        }

        ecfrcs = EnrichClientFromRemoteConfigStrategy(
            client_factory=_create_client_from_config)

        with self.assertRaises(Exception):
            ecfrcs.process(config)

    def test_enrich_client_from_remote_config_default_app_many_apps(self):
        def _create_client_from_config(config):
            return Client(
                [self.stormpath_app, self.application, self.application])

        config = {
            'application': {}
        }

        ecfrcs = EnrichClientFromRemoteConfigStrategy(
            client_factory=_create_client_from_config)

        with self.assertRaises(Exception):
            ecfrcs.process(config)

    def test_enrich_client_from_remote_config_default_app(self):
        def _create_client_from_config(config):
            return Client([self.stormpath_app, self.application])

        config = {
            'application': {}
        }

        ecfrcs = EnrichClientFromRemoteConfigStrategy(
            client_factory=_create_client_from_config)
        ecfrcs.process(config)

        self.assertEqual(config['application'], self.application)
