
class ConfigLoader(object):
    """Represents a configuration loader that loads a configuration
    through a list of strategies.
    """
    def __init__(self, strategies):
        self.strategies = strategies

    def load(self):
        config = dict()
        for strategy in self.strategies:
            config = strategy.process(config)
        return config

