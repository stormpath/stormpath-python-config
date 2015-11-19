import codecs
import flatdict
import os
import yaml


def _load_properties(fname):
    props = {}
    if not fname or not os.path.isfile(fname):
        return props

    try:
        with codecs.open(fname, 'r', encoding='utf-8') as fd:
            for line in fd:
                line = line.strip()
                if line.startswith('#') or '=' not in line:
                    continue

                k, v = line.split('=', 1)
                props[k.strip()] = v.strip()

        return props
    except UnicodeDecodeError:
        return {}


class LoadFileConfigStrategy(object):
    """Represents a strategy that loads configuration from either a
    JSON or YAML file into the configuration.
    """
    def __init__(self, file_path, must_exist=False):
        self.file_path = os.path.expanduser(file_path)
        self.must_exist = must_exist

    def process(self, config=None):
        if config is None:
            config = {}

        if not os.path.exists(self.file_path):
            if self.must_exist:
                raise Exception(
                    "Config file '" + self.file_path + "' doesn't exist.")
            return config

        f = open(self.file_path, 'r')
        try:
            loaded_config = yaml.load(f.read())
        except Exception as e:
            raise Exception(
                "Error parsing file %s.\nDetails: %s" % (
                    self.file_path, e.message))

        config.update(loaded_config)
        return config


class LoadAPIKeyConfigStrategy(object):
    """Represents a strategy that loads API keys from a .properties
    file into the configuration.
    """

    def __init__(self, file_path, must_exist=False):
        self.file_path = os.path.expanduser(file_path)
        self.must_exist = must_exist

    def process(self, config=None):
        if config is None:
            config = {}

        if not os.path.exists(self.file_path):
            if self.must_exist:
                raise Exception(
                    "Config file %s doesn't exist." % self.file_path)
            return config

        try:
            properties_config = _load_properties(self.file_path)
        except Exception as e:
            raise Exception(
                "Error parsing config %s.\nDetails: %s" % (
                    self.file_path, e.message))

        if not self.must_exist and len(properties_config.items()) == 0:
          return config

        api_key_id = properties_config.get('apiKey.id')
        api_key_secret = properties_config.get('apiKey.secret')

        if not (api_key_id and api_key_secret):
          raise Exception(
              'Unable to read properties file: %s' % self.file_path)

        config.setdefault('client', {})
        config['client'].setdefault('apiKey', {})
        config['client']['apiKey'].setdefault('id', None)
        config['client']['apiKey'].setdefault('secret', None)
        config['client']['apiKey']['id'] = api_key_id
        config['client']['apiKey']['secret'] = api_key_secret

        return config


class LoadEnvConfigStrategy(object):
    """Represents a strategy that loads configuration variables from
    the environment into the configuration.
    """

    def __init__(self, prefix, aliases=None):
        self.prefix = prefix

        if aliases is None:
            aliases = {}
        self.aliases = aliases

    def process(self, config):
        config = flatdict.FlatDict(config, delimiter='_')
        environ_config = {}

        for key in config.keys():
            env_key = '_'.join([self.prefix, key.upper()])
            env_key = self.aliases.get(env_key, env_key)
            value = os.environ.get(env_key)
            if value:
                if isinstance(config[key], int):
                    value = int(value)
                environ_config[key] = value
        config.update(environ_config)

        config = config.as_dict()
        return config


class ExtendConfigStrategy(object):
    """Represents a strategy that extends the configuration."""
    def __init__(self, extend_with):
        self.extend_with = extend_with

    def process(self, config):
        if config is None:
            config = {}

        config.update(self.extend_with)
        return config


class LoadAPIKeyFromConfigStrategy(object):
    """Represents a strategy that loads an API key specified in config
    into the configuration.
    """
    def process(self, config):
        api_key_file = config.get('client', {}).get('apiKey', {}).get('file')
        if api_key_file:
            lakcs = LoadAPIKeyConfigStrategy(api_key_file, True)
            return lakcs.process(config)

        return config


class MoveAPIKeyToClientAPIKeyStrategy(object):
    """Represents a strategy that moves an API key from apiKey to
    client.apiKey.
    """

    def process(self, config):
        apiKey = config.get('apiKey', {})

        if apiKey:
            config.setdefault('client', {})
            config['client'].setdefault('apiKey', {})
            config['client']['apiKey'] = apiKey

        return config


class ValidateClientConfigStrategy(object):
    """Represents a strategy that validates the configuration
    (post loading).
    """

    def process(self, config):
        if not config:
            raise ValueError('Configuration not instantiated.')

        client = config.get('client')
        if not client:
            raise ValueError('Client cannot be empty.')

        apiKey = client.get('apiKey')
        if not apiKey:
            raise ValueError('API key cannot be empty.')

        if not apiKey.get('id') or not apiKey.get('secret'):
            raise ValueError('API key ID and secret is required.')

        application = config.get('application')
        if not application:
            raise ValueError('Application cannot be empty.')

        href = application.get('href')
        if href and '/applications/' not in href:
            raise ValueError(
                'Application HREF %s is not a valid Stormpath Application '
                'HREF.' % href)

        return config
