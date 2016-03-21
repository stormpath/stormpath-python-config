from datetime import timedelta

from .helpers import _extend_dict, to_camel_case


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
            if isinstance(v, timedelta):
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
                remote_provider = {to_camel_case(k): v for k, v in remote_provider.items()}

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
