from datetime import timedelta

from ..helpers import _extend_dict, to_camel_case


def _resolve_application(client, config):
    """
    Given a Stormpath Client, and a fully populated Stormpath configuration,
    find and retrieve the Stormpath Application.

    :param obj client: The Stormpath Client object.
    :param dict config: The fully populated Stormpath configuration.
    :rtype: obj
    :returns: The Stormpath Application that was specified in the configuration.
    """
    application = client.applications.get(config['application']['href'])
    if not (application and hasattr(application, 'href') and
            hasattr(application, 'account_store_mappings') and
            hasattr(application, 'oauth_policy')):
        raise Exception('Unable to resolve a Stormpath application.')

    return application


def _enrich_with_oauth_policy(application, config):
    """
    Given a Stormpath Application, and a fully populated Stormpath
    configuration, find and retrieve the Stormpath Application's OAuth Policy
    settings.

    :param obj application: The Stormpath Application.
    :param dict config: The fully populated Stormpath configuration.
    :rtype: dict
    :returns: The OAuth Policy rules for the given Stormpath Application as a
        dict.
    """
    oauth_policy_dict = {}

    for k, v in dict(application.oauth_policy).items():
        if isinstance(v, timedelta):
            v = v.total_seconds()

        if k not in ['created_at', 'modified_at']:
            oauth_policy_dict[to_camel_case(k)] = v

    return oauth_policy_dict


def _resolve_directory(application):
    """
    Given a Stormpath Application, find and return the Application's default
    Account Store, or None.

    :param obj application: The Stormpath Application.
    :rtype: obj or None
    :returns: The Stormpath resource that is the Application's default Account
        Store, or None.
    """
    try:
        dac = application.default_account_store_mapping.account_store
    except Exception:
        return None

    # If this account store is Group object, get its directory.
    if hasattr(dac, 'directory'):
        dac = dac.directory

    return dac


def _enrich_with_directory_policies(directory, config):
    """
    Given a Stormpath Directory, and a fully populated Stormpath configuration,
    find and retrieve the Stormpath Directory's Policies.

    :param obj application: The Stormpath Application.
    :param dict config: The fully populated Stormpath configuration.
    :rtype: dict or None
    :returns: The OAuth Policy rules for the given Stormpath Application as a
        dict.
    """
    if not directory:
        return None

    def is_enabled(status):
        return status == 'ENABLED'

    # Enrich config with password policies
    # Remove the href property from the Strength Resource, we don't
    # want this to clutter up our nice passwordPolicy configuration
    # dictionary!
    strength = dict(directory.password_policy.strength)
    del strength['href']
    strength = {to_camel_case(k): v for k, v in strength.items()}

    reset_email = is_enabled(directory.password_policy.reset_email_status)
    ac_policy = directory.account_creation_policy

    return {
        'passwordPolicy': strength,
        'web': {
            'forgotPassword': {'enabled': reset_email},
            'changePassword': {'enabled': reset_email},
            'verifyEmail': {
                'enabled': is_enabled(ac_policy.verification_email_status)
            }
        }
    }


def _enrich_with_social_providers(application, config):
    """
    Given a Stormpath Application, and a fully populated Stormpath
    configuration, find and retrieve the Stormpath Application's social
    Directory configuration.

    :param obj application: The Stormpath Application.
    :param dict config: The fully populated Stormpath configuration.
    :rtype: dict or None
    :returns: The OAuth Policy rules for the given Stormpath Application as a
        dict.
    """
    social_config = {
        'web': {
            'social': {}
        }
    }

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

            local_provider = social_config['web']['social'].get(provider_id, {})
            if 'uri' not in local_provider:
                local_provider['uri'] = '/callbacks/%s' % provider_id

            _extend_dict(local_provider, remote_provider)
            social_config['web']['social'][provider_id] = local_provider

    return social_config


class EnrichIntegrationFromRemoteConfigStrategy(object):
    """Retrieves Stormpath settings from the API service, and ensures
    the local configuration object properly reflects these settings.
    """
    def __init__(self, client_factory):
        self.client_factory = client_factory

    def process(self, config):
        if config.get('skipRemoteConfig'):
            return config

        client = self.client_factory(config)

        if 'href' in config.get('application', {}):
            application = _resolve_application(client, config)
            config['application']['oAuthPolicy'] = _enrich_with_oauth_policy(application, config)
            social_config = _enrich_with_social_providers(application, config)
            _extend_dict(config, social_config)
            directory = _resolve_directory(application)
            policy_config = _enrich_with_directory_policies(directory, config)
            _extend_dict(config, policy_config)

        return config
