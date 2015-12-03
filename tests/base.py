class StormpathError(RuntimeError):
    def __init__(self, msg, http_status=None):
        super(RuntimeError, self).__init__(msg)
        self.status = http_status
        self.message = msg


class Application(object):
    name = ''
    href = ''

    def __init__(self, name, href):
        self.name = name
        self.href = href


class Applications(object):
    def __init__(self, apps):
        self.apps = apps

    def get(self, href):
        for app in self.apps:
            if app.href == href:
                return app

        raise StormpathError("I don't exist", http_status=404)

    def query(self, name):
        for app in self.apps:
            if app.name == name:
                return [app]

        return []

    def __iter__(self):
        for a in self.apps:
            yield a


class Client(object):
    def __init__(self, apps):
        self.apps = apps

    @property
    def applications(self):
        return Applications(self.apps)
