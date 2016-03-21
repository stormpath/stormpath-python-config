from unittest import TestCase

from stormpath_config.strategies import EnrichIntegrationFromRemoteConfigStrategy

from ..base import Application, Client


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
