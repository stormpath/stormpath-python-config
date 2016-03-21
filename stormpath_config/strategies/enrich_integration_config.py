from ..helpers import _extend_dict


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
