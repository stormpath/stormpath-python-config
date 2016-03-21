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
            raise ValueError('API key ID and secret are required.')

        application = config.get('application')
        if not application:
            raise ValueError('Application cannot be empty.')

        href = application.get('href')
        if href and '/applications/' not in href:
            raise ValueError('Application HREF "%s" is not a valid Stormpath Application HREF.' % href)

        web_spa = config.get('web', {}).get('spa', {})
        if web_spa and web_spa.get('enabled') and web_spa.get('view') is None:
            raise ValueError('SPA mode is enabled but stormpath.web.spa.view isn\'t '
                'set. This needs to be the absolute path to the file '
                'that you want to serve as your SPA entry.')

        return config
