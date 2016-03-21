from unittest import TestCase

from stormpath_config.strategies import EnrichIntegrationConfigStrategy


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
