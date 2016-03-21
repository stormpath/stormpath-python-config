from .helpers import _load_properties
from .load_file_path import LoadFilePathStrategy


class LoadAPIKeyConfigStrategy(LoadFilePathStrategy):
    """Represents a strategy that loads API keys from a .properties
    file into the configuration.
    """
    def _process_file_path(self, config):
        try:
            properties_config = _load_properties(self.file_path)
        except Exception as e:
            raise Exception('Error parsing config "%s".\nDetails: %s' % (self.file_path, e.message))

        if not self.must_exist and len(properties_config.items()) == 0:
            return config

        api_key_id = properties_config.get('apiKey.id')
        api_key_secret = properties_config.get('apiKey.secret')

        if not (api_key_id and api_key_secret):
            raise Exception('Unable to read properties file: "%s"' % self.file_path)

        config.setdefault('client', {})
        config['client'].setdefault('apiKey', {})
        config['client']['apiKey'].setdefault('id', None)
        config['client']['apiKey'].setdefault('secret', None)
        config['client']['apiKey']['id'] = api_key_id
        config['client']['apiKey']['secret'] = api_key_secret

        return config
