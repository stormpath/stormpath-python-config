import codecs
import datetime
import flatdict
import json
import logging
import os
import yaml


log = logging.getLogger(__name__)


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


def to_camel_case(name):
    if '_' not in name:
        return name

    head, tail = name.split('_', 1)
    tail = tail.title().replace('_', '')

    return head + tail


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

        if self.file_path.startswith('~'):
            if self.must_exist:
                raise Exception(
                    'Unable to load "%s" . Environment home not set.' %
                    self.file_path)
            return config

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

        web_spa = config.get('web', {}).get('spa', {})
        if web_spa and web_spa.get('enabled') and web_spa.get('view') is None:
            raise ValueError(
                "SPA mode is enabled but stormpath.web.spa.view isn't "
                "set. This needs to be the absolute path to the file "
                "that you want to serve as your SPA entry."
            )

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
            raise Exception(
                'Exception was raised while trying to resolve an application. '
                'The provided application href was: %s. '
                'Exception message was: %s' % (href, e.message))

        config['application']['name'] = app.name
        return app

    def _resolve_application_by_name(self, client, config, name):
        """Finds and returns an Application object given an Application
        name.  Will return an error if no Application is found.
        """
        try:
            app = client.applications.query(name=name)[0]
        except IndexError:
            raise Exception(
                'The provided application could not be found. '
                'The provided application name was: %s' % name)
        except Exception as e:
            raise Exception(
                'Exception was raised while trying to resolve an application. '
                'The provided application name was: %s. '
                'Exception message was: %s' % (name, e.message))

        config['application']['href'] = app.href
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
                # Check if we have already found non-Stormpath app.
                # If there is more than one non-Stormpath app, we can't
                # resolve any of them as default application.
                if default_app is not None:
                    raise Exception(message)
                default_app = app

        if default_app is None:
            raise Exception(message)

        config['application']['name'] = default_app.name
        config['application']['href'] = default_app.href
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


class EnrichIntegrationConfigStrategy(object):
    """Represents a strategy that enriches the configuration (post
    loading).
    """
    def __init__(self, user_config):
        self.user_config = user_config

    def process(self, config):
        web_features_to_enable = set()

        # If a user enables a boolean configuration option named
        # `website`, this means the user is building a website and we
        # should automatically enable certain features in the library
        # meant for users developing websites.  This is a simpler way
        # of handling configuration than forcing users to specify all
        # nested JSON configuration options themselves.
        if config.get('website'):
            web_features_to_enable.update(
                ['register', 'login', 'logout', 'me'])

        # If a user enables a boolean configuration option named `api`,
        # this means the user is building an API service, and we should
        # automatically enable certain features in the library meant
        # for users developing API services -- namely, our OAuth2 token
        # endpoint (/oauth/token).  This allows users building APIs to
        # easily provision OAuth2 tokens without specifying any nested
        # JSON configuration options.
        if config.get('api'):
            web_features_to_enable.add('oauth2')

        user_configured_features = {
            feature for feature, definition in
            self.user_config.get('web', {}).items()
            if 'enabled' in definition
        }
        web_features = {
            feature: {'enabled': True}
            for feature in (web_features_to_enable - user_configured_features)
        }

        _extend_dict(config, {'web': web_features})
        return config


class EnrichIntegrationFromRemoteConfigStrategy(object):
    """Retrieves Stormpath settings from the API service, and ensures
    the local configuration object properly reflects these settings.
    """
    def __init__(self, client_factory):
        self.client_factory = client_factory

    def _resolve_application(self, client, config):
        application = client.applications.get(config['application']['href'])
        if not (
                application and hasattr(application, 'href') and
                hasattr(application, 'account_store_mappings') and
                hasattr(application, 'oauth_policy')):
            raise Exception('Unable to resolve a Stormpath application.')

        return application

    def _enrich_with_oauth_policy(self, config, application):
        # Returns the OAuth policy of the Stormpath Application.
        oauth_policy_dict = {}
        for k, v in dict(application.oauth_policy).items():
            if isinstance(v, datetime.timedelta):
                v = v.total_seconds()
            if k not in ['created_at', 'modified_at']:
                oauth_policy_dict[to_camel_case(k)] = v
        config['application']['oAuthPolicy'] = oauth_policy_dict

    def _enrich_with_social_providers(self, config, application):
        """Iterate over all account stores on the given Application,
        looking for all Social providers.  We'll then create a
        config.providers array which we'll use later on to dynamically
        populate all social login configurations.
        """
        if 'web' not in config:
            config['web'] = {}
        if 'social' not in config['web']:
            config['web']['social'] = {}

        for account_store_mapping in application.account_store_mappings:
            # Iterate directories
            if not hasattr(account_store_mapping.account_store, 'provider'):
                continue

            remote_provider = dict(account_store_mapping.account_store.provider)
            provider_id = remote_provider['provider_id']

            # If the provider isn't a Stormpath, AD, or LDAP directory
            # it's a social directory.
            if provider_id not in ['stormpath', 'ad', 'ldap']:
                # Remove unnecessary properties that clutter our config.
                del remote_provider['href']
                del remote_provider['created_at']
                del remote_provider['modified_at']
                remote_provider['enabled'] = True
                remote_provider = {
                    to_camel_case(k): v for k, v in remote_provider.items()
                }

                local_provider = config['web']['social'].get(provider_id, {})
                if 'uri' not in local_provider:
                    local_provider['uri'] = '/callbacks/%s' % provider_id

                _extend_dict(local_provider, remote_provider)
                config['web']['social'][provider_id] = local_provider

    def _resolve_directory(self, application):
        # Finds and returns an Application's default Account Store
        # (Directory) object. If one doesn't exist, nothing will
        # be returned.
        try:
            dac = application.default_account_store_mapping.account_store
        except Exception:
            return None

        # If this account store is Group object, get its' directory
        if hasattr(dac, 'directory'):
            dac = dac.directory

        return dac

    def _enrich_with_directory_policies(self, config, directory):
        # Pulls down all of a Directory's configuration settings, and
        # applies them to the local configuration.
        if not directory:
            return None

        def is_enabled(status):
            return status == 'ENABLED'

        reset_email = is_enabled(directory.password_policy.reset_email_status)
        ac_policy = directory.account_creation_policy
        extend_with = {
            'web': {
                'forgotPassword': {'enabled': reset_email},
                'changePassword': {'enabled': reset_email},
                'verifyEmail': {
                    'enabled': is_enabled(ac_policy.verification_email_status)
                }
            }
        }
        _extend_dict(config, extend_with)

        # Enrich config with password policies
        strength = dict(directory.password_policy.strength)

        # Remove the href property from the Strength Resource, we don't
        # want this to clutter up our nice passwordPolicy configuration
        # dictionary!
        del strength['href']
        strength = {to_camel_case(k): v for k, v in strength.items()}
        config['passwordPolicy'] = strength

    def process(self, config):
        if config.get('skipRemoteConfig'):
            return config

        client = self.client_factory(config)

        if 'href' in config.get('application', {}):
            application = self._resolve_application(client, config)
            self._enrich_with_oauth_policy(config, application)
            self._enrich_with_social_providers(config, application)
            directory = self._resolve_directory(application)
            self._enrich_with_directory_policies(config, directory)

        return config


class DebugConfigStrategy(object):
    """Represents a strategy that when used dumps the config to the
    provided logger.
    """
    def __init__(self, logger=None, section=None):
        self.section = section
        if logger is None:
            self.log = log
        else:
            self.log = logging.getLogger(logger)

    def process(self, config):
        message = ''
        if self.section is not None:
            message = '%s:\n' % self.section

        message = "%s%s\n" % (
            message,
            json.dumps(
                config, sort_keys=True, indent=4, separators=(',', ': ')))
        self.log.debug(message)

        return config
