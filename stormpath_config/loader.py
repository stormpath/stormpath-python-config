
class ConfigLoader(object):
    """Represents a configuration loader that loads a configuration
    through a list of strategies.

    :param load_strategies: List of strategies that load config
    :param post_processing_strategies: List of strategies that will be
        performed after each load strategy.
    :param validation_strategies: List of strategies that will be
        performed after load and post processing strategies are
        finished.
    """
    def __init__(self, load_strategies, post_processing_strategies,
                 validation_strategies):
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
