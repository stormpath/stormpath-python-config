from unittest import TestCase

from stormpath_config.strategies import LoadFileConfigStrategy


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
