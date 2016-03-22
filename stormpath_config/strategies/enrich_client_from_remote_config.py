def _resolve_application_by_href(client, config, href):
    """
    Finds and returns an Application object given an Application href.  Will
    raise an error if no Application is found.
    """
    try:
        app = client.applications.get(href)
        app.name
    except Exception as e:
        if hasattr(e, 'status') and e.status == 404:
            raise Exception('The provided application could not be found.  The provided application href was: "%s".' % href)

        raise Exception('Exception was raised while trying to resolve an application. '
            'The provided application href was: "%s". '
            'Exception message was: "%s".' % (href, e.message))

    return app.name


def _resolve_application_by_name(client, config, name):
    """
    Finds and returns an Application object given an Application name.  Will
    return an error if no Application is found.
    """
    try:
        app = client.applications.query(name=name)[0]
    except IndexError:
        raise Exception('The provided application could not be found. '
            'The provided application name was: "%s".' % name)
    except Exception as e:
        raise Exception('Exception was raised while trying to resolve an application. '
            'The provided application name was: "%s". '
            'Exception message was: "%s".' % (name, e.message))

    return app.href


def _resolve_default_application(client, config):
    """
    If there are only two Applications and one of them is the Stormpath
    Application, then use the other one as default.
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

    return (default_app.name, default_app.href)


class EnrichClientFromRemoteConfigStrategy(object):
    """Retrieves Stormpath settings from the API service, and ensures
    the local configuration object properly reflects these settings.
    """
    def __init__(self, client_factory):
        self.client_factory = client_factory

    def process(self, config):
        if config.get('skipRemoteConfig'):
            return config

        application = config.get('application', {})
        client = self.client_factory(config)

        href, name = application.get('href'), application.get('name')

        if href:
            config['application']['name'] = _resolve_application_by_href(client, config, href)
        elif name:
            config['application']['href'] = _resolve_application_by_name(client, config, name)
        else:
            config['application']['name'], config['application']['href'] = _resolve_default_application(client, config)

        return config
