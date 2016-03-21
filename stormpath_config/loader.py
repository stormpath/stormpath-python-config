"""Configuration Loader."""


class ConfigLoader(object):
    """
    Represents a configuration loader that loads configuration through a list
    of strategies.

    :param list load_strategies: List of Strategies that load configuration data.
    :param post_processing_strategies: List of Strategies that will be performed
        after each load strategy.
    :param validation_strategies: List of strategies that will be performed after
        the load and post processing strategies are finished.
    """
    def __init__(self, load_strategies=None, post_processing_strategies=None, validation_strategies=None):
        if load_strategies is None:
            load_strategies = []

        if post_processing_strategies is None:
            post_processing_strategies = []

        if validation_strategies is None:
            validation_strategies = []

        self.load_strategies = load_strategies
        self.post_processing_strategies = post_processing_strategies
        self.validation_strategies = validation_strategies

    def load(self):
        config = dict()

        for strategy in self.load_strategies:
            config = strategy.process(config)

            for strategy in self.post_processing_strategies:
                config = strategy.process(config)

        for strategy in self.validation_strategies:
            config = strategy.process(config)

        return config
