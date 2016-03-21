from unittest import TestCase

from stormpath_config.strategies import EnrichClientFromRemoteConfigStrategy

from ..base import Application, Client


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
