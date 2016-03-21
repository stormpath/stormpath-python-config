from .helpers import _extend_dict


class ExtendConfigStrategy(object):
    """Represents a strategy that extends the configuration."""
    def __init__(self, extend_with):
        self.extend_with = extend_with

    def process(self, config=None):
        if config is None:
            config = {}

        return _extend_dict(config, self.extend_with)
