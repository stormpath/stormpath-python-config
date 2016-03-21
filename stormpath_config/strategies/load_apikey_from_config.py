from .load_apikey_config import LoadAPIKeyConfigStrategy


class LoadAPIKeyFromConfigStrategy(object):
    """Represents a strategy that loads an API key specified in config
    into the configuration.
    """
    def process(self, config=None):
        if config is None:
            config = {}

        api_key_file = config.get('client', {}).get('apiKey', {}).get('file')
        if api_key_file:
            lakcs = LoadAPIKeyConfigStrategy(api_key_file, True)
            config = lakcs.process(config)
            del config['client']['apiKey']['file']

        return config
