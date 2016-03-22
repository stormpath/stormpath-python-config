"""Tests for the DebugConfigStrategy class."""


from logging import getLogger
from unittest import TestCase

from mock import patch

from stormpath_config.strategies import DebugConfigStrategy


class DebugConfigStrategyTest(TestCase):
    def test_debug_config_strategy(self):
        with patch('stormpath_config.strategies.debug_config.log') as log_mock:
            dcs = DebugConfigStrategy(section='test')
            config = dcs.process({'abc': '123'})

            self.assertEqual(config, {'abc': '123'})
            log_mock.debug.assert_called_with('test:\n{\n    "abc": "123"\n}\n')

    def test_debug_config_strategy_without_section(self):
        with patch('stormpath_config.strategies.debug_config.log') as log_mock:
            dcs = DebugConfigStrategy()
            config = dcs.process({'abc': '123'})

            log_mock.debug.assert_called_with('{\n    "abc": "123"\n}\n')
            self.assertEqual(config, {'abc': '123'})

    def test_debug_config_strategy_with_custom_logger(self):
        logger = getLogger('my.custom.logger')

        with patch.object(logger, 'debug') as log_mock:
            dcs = DebugConfigStrategy(logger='my.custom.logger', section='sec')
            config = dcs.process({'abc': '123'})

            log_mock.assert_called_with('sec:\n{\n    "abc": "123"\n}\n')
            self.assertEqual(config, {'abc': '123'})
