import mock
import os
from unittest import TestCase
from path import Path

from .base import *
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
        self.assertEqual(original, {'a': 1, 'c': 3, 'b': {'A': 1, 'B': 3, 'C': 4}})


class LoadFileConfigStrategyTest(TestCase):
    def test_load_file_config(self):
        lfcs = LoadFileConfigStrategy('tests/assets/default_config.yml')
        config = lfcs.process()

        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 300)

    def test_load_file_config_with_existing_config(self):
        lfcs = LoadFileConfigStrategy('tests/assets/stormpath.yml', must_exist=False)
        existing_config = {'application': {'name': 'App Name'}, 'key': 'value'}
        config = lfcs.process(existing_config)

        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 301)
        self.assertEqual(config['application']['name'], 'MY_APP')
        self.assertEqual(config['key'], 'value')

    def test_load_non_existent_file_config_with_existing_config(self):
        lfcs = LoadFileConfigStrategy('tests/assets/i-do-not-exist.yml', must_exist=False)
        existing_config = {'application': {'name': 'App Name'}, 'key': 'value'}
        config = lfcs.process(existing_config)

        self.assertEqual(config['application']['name'], 'App Name')
        self.assertEqual(config['key'], 'value')

    def test_load_file_json_config_with_existing_config(self):
        config = {'application': {'name': 'App Name'}, 'key': 'value'}
        lfcs = LoadFileConfigStrategy('tests/assets/stormpath.json')
        config = lfcs.process(config)

        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 302)
        self.assertEqual(config['client']['apiKey']['id'], 'MY_JSON_CONFIG_API_KEY_ID')
        self.assertEqual(config['client']['apiKey']['secret'], 'MY_JSON_CONFIG_API_KEY_SECRET')
        self.assertEqual(config['client']['connectionTimeout'], None)
        self.assertEqual(config['application']['name'], 'MY_JSON_APP')
        self.assertEqual(config['key'], 'value')


class LoadAPIKeyConfigStrategyTest(TestCase):
    def test_load_api_key_config(self):
        lapcs = LoadAPIKeyConfigStrategy('tests/assets/apiKey.properties')
        config = lapcs.process()

        self.assertEqual(config['client']['apiKey']['id'], 'API_KEY_PROPERTIES_ID')
        self.assertEqual(config['client']['apiKey']['secret'], 'API_KEY_PROPERTIES_SECRET')

    def test_load_empty_api_key_config(self):
        lapcs = LoadAPIKeyConfigStrategy('tests/assets/empty_apiKey.properties')
        config = lapcs.process()

        self.assertEqual(config, {})

    def test_load_empty_api_key_config_must_exist(self):
        lapcs = LoadAPIKeyConfigStrategy('tests/assets/empty_apiKey.properties', must_exist=True)

        with self.assertRaises(Exception):
            lapcs.process()

    def test_load_empty_api_key_config_must_exist_no_home_env(self):
        path = '~/tests/assets/empty_apiKey.properties'

        with mock.patch.object(Path, 'abspath', return_value=path):
            lapcs = LoadAPIKeyConfigStrategy(path, must_exist=True)
            try:
                lapcs.process()
            except Exception as e:
                self.assertEqual(str(e), 'Unable to load "%s". Environment home not set.' % path)
            else:
                self.fail('Loading config without environment home didn\'t throw any exception.')

    def test_api_key_properties_file_after_default_config(self):
        lfcs = LoadFileConfigStrategy('tests/assets/default_config.yml')
        config = lfcs.process()
        lapcs = LoadAPIKeyConfigStrategy('tests/assets/apiKey.properties')
        returned_config = lapcs.process(config)

        self.assertEqual(returned_config, config)
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 300)
        self.assertEqual(config['client']['apiKey']['id'], 'API_KEY_PROPERTIES_ID')
        self.assertEqual(config['client']['apiKey']['secret'], 'API_KEY_PROPERTIES_SECRET')

    def test_empty_api_key_properties_file_after_default_config(self):
        lfcs = LoadFileConfigStrategy('tests/assets/default_config.yml')
        config = lfcs.process()
        lapcs = LoadAPIKeyConfigStrategy('tests/assets/empty_apiKey.properties')
        returned_config = lapcs.process(config)

        self.assertEqual(returned_config, config)
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 300)
        self.assertIsNone(config['client']['apiKey']['id'])
        self.assertIsNone(config['client']['apiKey']['secret'])


class LoadEnvConfigStrategyTest(TestCase):
    @mock.patch.dict(os.environ, {
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

    @mock.patch.dict(os.environ, {
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

    @mock.patch.dict(os.environ, {
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


class EnrichClientFromRemoteConfigStrategyTest(TestCase):
    def setUp(self):
        self.stormpath_app = Application('Stormpath', 'https://api.stormpath.com/v1/applications/stormpath')
        self.application = Application('My named application', 'https://api.stormpath.com/v1/applications/a')

    def test_enrich_client_from_remote_config_app_by_invalid_href(self):
        def _create_client_from_config(config):
            return Client([self.application])

        config = {
            'application': {
                'href': 'invalid'
            }
        }

        ecfrcs = EnrichClientFromRemoteConfigStrategy(client_factory=_create_client_from_config)
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

        ecfrcs = EnrichClientFromRemoteConfigStrategy(client_factory=_create_client_from_config)

        ecfrcs.process(config)
        self.assertIsInstance(config['application'], dict)
        self.assertEqual(config['application'], {
            'href': 'https://api.stormpath.com/v1/applications/a',
            'name': 'My named application'
        })

    def test_enrich_client_from_remote_config_app_by_invalid_name(self):
        def _create_client_from_config(config):
            return Client([self.application])

        config = {
            'application': {
                'name': 'invalid'
            }
        }

        ecfrcs = EnrichClientFromRemoteConfigStrategy(client_factory=_create_client_from_config)
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

        ecfrcs = EnrichClientFromRemoteConfigStrategy(client_factory=_create_client_from_config)
        ecfrcs.process(config)

        self.assertIsInstance(config['application'], dict)
        self.assertEqual(config['application'], {
            'href': 'https://api.stormpath.com/v1/applications/a',
            'name': 'My named application',
        })

    def test_enrich_client_from_remote_config_default_app_no_app(self):
        def _create_client_from_config(config):
            return Client([self.stormpath_app])

        config = {'application': {}}
        ecfrcs = EnrichClientFromRemoteConfigStrategy(client_factory=_create_client_from_config)

        with self.assertRaises(Exception):
            ecfrcs.process(config)

    def test_enrich_client_from_remote_config_default_app_many_apps(self):
        def _create_client_from_config(config):
            return Client([self.stormpath_app, self.application, self.application])

        config = {'application': {}}
        ecfrcs = EnrichClientFromRemoteConfigStrategy(client_factory=_create_client_from_config)

        with self.assertRaises(Exception):
            ecfrcs.process(config)

    def test_enrich_client_from_remote_config_default_app(self):
        def _create_client_from_config(config):
            return Client([self.stormpath_app, self.application])

        config = {'application': {}}

        ecfrcs = EnrichClientFromRemoteConfigStrategy(client_factory=_create_client_from_config)
        ecfrcs.process(config)

        self.assertIsInstance(config['application'], dict)
        self.assertEqual(config['application'], {
            'href': 'https://api.stormpath.com/v1/applications/a',
            'name': 'My named application',
        })


class EnrichIntegrationConfigStrategyTest(TestCase):
    def test_enrich_client_from_integration_config_empty_user_config(self):
        config = {'website': True, 'api': True, 'client': {'k': 'v'}}
        eics = EnrichIntegrationConfigStrategy({})
        eics.process(config)

        self.assertEqual(config, {
            'website': True,
            'api': True,
            'client': {'k': 'v'},
            'web': {
                'register': {'enabled': True},
                'login': {'enabled': True},
                'logout': {'enabled': True},
                'me': {'enabled': True},
                'oauth2': {'enabled': True},
            },
        })

    def test_enrich_client_from_integration_config_with_user_config_web(self):
        config = {'website': True, 'client': {'k': 'v'}}
        user_config = {'web': {}}

        eics = EnrichIntegrationConfigStrategy(user_config)
        eics.process(config)

        self.assertEqual(config, {
            'website': True,
            'client': {'k': 'v'},
            'web': {
                'register': {'enabled': True},
                'login': {'enabled': True},
                'logout': {'enabled': True},
                'me': {'enabled': True},
            },
        })

    def test_enrich_client_from_integration_config_user_config_feature(self):
        config = {'website': True, 'client': {'k': 'v'}}
        user_config = {'web': {'register': {'enabled': True}}}

        eics = EnrichIntegrationConfigStrategy(user_config)
        eics.process(config)

        self.assertEqual(config, {
            'website': True,
            'client': {'k': 'v'},
            'web': {
                'login': {'enabled': True},
                'logout': {'enabled': True},
                'me': {'enabled': True},
            },
        })

    def test_enrich_client_from_integration_config_user_config_data(self):
        config = {'website': True, 'client': {'k': 'v'}}
        user_config = {
            'web': {
                'register': {'enabled': False}
            }
        }

        eics = EnrichIntegrationConfigStrategy(user_config)
        eics.process(config)

        self.assertEqual(config, {
            'website': True,
            'client': {'k': 'v'},
            'web': {
                'login': {'enabled': True},
                'logout': {'enabled': True},
                'me': {'enabled': True},
            },
        })


class EnrichIntegrationFromRemoteConfigStrategyTest(TestCase):
    def setUp(self):
        self.application = Application('My named application', 'https://api.stormpath.com/v1/applications/a')

    def test_enrich_client_from_remote_config(self):
        def _create_client_from_config(config):
            return Client([self.application])

        config = {
            'application': {
                'href': 'https://api.stormpath.com/v1/applications/a'
            }
        }

        ecfrcs = EnrichIntegrationFromRemoteConfigStrategy(client_factory=_create_client_from_config)
        config = ecfrcs.process(config)

        self.assertTrue('oAuthPolicy' in config['application'])
        self.assertEqual(config['application']['oAuthPolicy'], {
            'href': 'https://api.stormpath.com/v1/oAuthPolicies/a',
            'accessTokenTtl': 3600.0,
            'refreshTokenTtl': 5184000.0,
            'spHttpStatus': 200,
        })
        self.assertEqual(config['passwordPolicy'], {
            'minSymbol': 0,
            'minUpperCase': 1,
            'minLength': 8,
            'spHttpStatus': 200,
            'minNumeric': 1,
            'minLowerCase': 1,
            'minDiacritic': 0,
            'maxLength': 100
        })
        self.assertEqual(config['web']['social'], {
            'google': {
                'providerId': 'google',
                'clientId': 'id',
                'clientSecret': 'secret',
                'enabled': True,
                'spHttpStatus': 200,
                'uri': '/callbacks/google',
                'redirectUri': 'https://myapplication.com/authenticate'
            }
        })
        self.assertEqual(config['web'], {
            'social': {
                'google': {
                    'providerId': 'google',
                    'clientId': 'id',
                    'clientSecret': 'secret',
                    'enabled': True,
                    'spHttpStatus': 200,
                    'uri': '/callbacks/google',
                    'redirectUri': 'https://myapplication.com/authenticate'
                }
            },
            'changePassword': {'enabled': True},
            'forgotPassword': {'enabled': True},
            'verifyEmail': {'enabled': False},
        })


class DebugConfigStrategyTest(TestCase):
    def test_debug_config_strategy(self):
        with mock.patch('stormpath_config.strategies.log') as log_mock:
            dcs = DebugConfigStrategy(section='test')
            config = dcs.process({'abc': '123'})

            log_mock.debug.assert_called_with('test:\n{\n    "abc": "123"\n}\n')
            self.assertEqual(config, {'abc': '123'})

    def test_debug_config_strategy_without_section(self):
        with mock.patch('stormpath_config.strategies.log') as log_mock:
            dcs = DebugConfigStrategy()
            config = dcs.process({'abc': '123'})

            log_mock.debug.assert_called_with('{\n    "abc": "123"\n}\n')
            self.assertEqual(config, {'abc': '123'})

    def test_debug_config_strategy_with_custom_logger(self):
        logger = logging.getLogger('my.custom.logger')
        with mock.patch.object(logger, 'debug') as mock_debug:
            dcs = DebugConfigStrategy(logger='my.custom.logger', section='sec')
            config = dcs.process({'abc': '123'})

            mock_debug.assert_called_with('sec:\n{\n    "abc": "123"\n}\n')
            self.assertEqual(config, {'abc': '123'})
