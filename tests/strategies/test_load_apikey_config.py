from unittest import TestCase

from mock import patch
from path import Path

from stormpath_config.strategies import LoadAPIKeyConfigStrategy, LoadFileConfigStrategy


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

        with patch.object(Path, 'abspath', return_value=path):
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
