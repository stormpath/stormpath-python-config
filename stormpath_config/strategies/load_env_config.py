from os import environ

from flatdict import FlatDict

from .helpers import _extend_dict


class LoadEnvConfigStrategy(object):
    """Represents a strategy that loads configuration variables from
    the environment into the configuration.
    """

    def __init__(self, prefix, aliases=None):
        self.prefix = prefix
        self.aliases = aliases if aliases is not None else {}

    def process(self, config=None):
        if config is None:
            config = {}

        config = FlatDict(config, delimiter='_')
        environ_config = {}

        for key in config.keys():
            env_key = '_'.join([self.prefix, key.upper()])
            env_key = self.aliases.get(env_key, env_key)
            value = environ.get(env_key)

            if value:
                if isinstance(config[key], int):
                    value = int(value)

                environ_config[key] = value

        _extend_dict(config, environ_config)
        config = config.as_dict()

        return config
