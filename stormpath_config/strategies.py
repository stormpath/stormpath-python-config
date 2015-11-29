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


def _extend_dict(original, extend_with):
    for key, value in extend_with.items():
        if key in original and isinstance(value, dict):
            _extend_dict(original[key], value)
        else:
            original[key] = value
    return original


class LoadFilePathStrategy(object):
    """Base class for all strategies that load configuration from a
    file.
    """
    def __init__(self, file_path, must_exist=False):
        self.file_path = os.path.expanduser(file_path)
        self.must_exist = must_exist

    def _process_file_path(self, config):
        raise NotImplementedError('Subclasses must implement this method.')

    def process(self, config=None):
        if config is None:
            config = {}

        if not os.path.exists(self.file_path):
            if self.must_exist:
                raise Exception(
                    "Config file '" + self.file_path + "' doesn't exist.")
            return config

        return self._process_file_path(config)


class LoadFileConfigStrategy(LoadFilePathStrategy):
    """Represents a strategy that loads configuration from either a
    JSON or YAML file into the configuration.
    """
    def _process_file_path(self, config):
        f = open(self.file_path, 'r')
        try:
            loaded_config = yaml.load(f.read())
        except Exception as e:
            raise Exception(
                "Error parsing file %s.\nDetails: %s" % (
                    self.file_path, e.message))

        return _extend_dict(config, loaded_config)


class LoadAPIKeyConfigStrategy(LoadFilePathStrategy):
    """Represents a strategy that loads API keys from a .properties
    file into the configuration.
    """
    def _process_file_path(self, config):
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

    def process(self, config=None):
        if config is None:
            config = {}

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
        _extend_dict(config, environ_config)

        config = config.as_dict()
        return config


class ExtendConfigStrategy(object):
    """Represents a strategy that extends the configuration."""
    def __init__(self, extend_with):
        self.extend_with = extend_with

    def process(self, config=None):
        if config is None:
            config = {}

        return _extend_dict(config, self.extend_with)


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


class MoveAPIKeyToClientAPIKeyStrategy(object):
    """Represents a strategy that moves an API key from apiKey to
    client.apiKey.
    """
    def process(self, config=None):
        if config is None:
            config = {}

        apiKey = config.get('apiKey', {})

        if apiKey:
            config.setdefault('client', {})
            config['client'].setdefault('apiKey', {})
            config['client']['apiKey'] = apiKey
            del config['apiKey']

        return config


class ValidateClientConfigStrategy(object):
    """Represents a strategy that validates the configuration
    (post loading).
    """

    def process(self, config=None):
        if config is None:
            config = {}

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


class EnrichClientFromRemoteConfigStrategy(object):
    """Retrieves Stormpath settings from the API service, and ensures
    the local configuration object properly reflects these settings.
    """
    def __init__(self, client_factory):
        self.client_factory = client_factory

    def _resolve_application_by_href(self, client, config, href):
        """Finds and returns an Application object given an Application
        HREF.  Will return an error if no Application is found."""
        try:
            app = client.applications.get(href)
            app.name
        except Exception as e:
            if hasattr(e, 'status') and e.status == 404:
                raise Exception(
                    'The provided application could not be found. '
                    'The provided application href was: %s' % href)
            else:
                raise
        config['application'] = app
        return app

    def _resolve_application_by_name(self, client, config, name):
        """Finds and returns an Application object given an Application
        name.  Will return an error if no Application is found.
        """
        try:
            app = client.applications.query(name=name)[0]
            app.name
        except IndexError:
            raise Exception(
                'The provided application could not be found. '
                'The provided application name was: %s' % name)
        config['application'] = app
        return app


    def _resolve_default_application(self, client, config):
        """If there are only two applications and one of them is the
        Stormpath application, then use the other one as default.
        """
        default_app = None
        message = """Could not automatically resolve a Stormpath Application.
        Please specify your Stormpath Application in your configuration."""

        for app in client.applications:
            if app.name != 'Stormpath':
                if default_app is not None:
                    raise Exception(message)
                default_app = app

        if default_app is None:
            raise Exception(message)

        config['application'] = default_app
        return default_app

    def process(self, config):
        if config.get('skipRemoteConfig'):
            return config

        application = config.get('application', {})
        client = self.client_factory(config)

        href, name = application.get('href'), application.get('name')

        if href:
            self._resolve_application_by_href(client, config, href)
        elif name:
            self._resolve_application_by_name(client, config, name)
        else:
            self._resolve_default_application(client, config)

        return config
