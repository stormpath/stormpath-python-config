import datetime

from stormpath.resources.base import DictMixin


class StormpathError(RuntimeError):
    def __init__(self, msg, http_status=None):
        super(RuntimeError, self).__init__(msg)
        self.status = http_status
        self.message = msg


class OauthPolicy(DictMixin):
    def _ensure_data(self):
        pass

    def __init__(self):
        self.href = 'https://api.stormpath.com/v1/oAuthPolicies/a'
        self.access_token_ttl = datetime.timedelta(0, 3600)
        self.refresh_token_ttl = datetime.timedelta(60)
        self.sp_http_status = 200
        self.created_at = datetime.datetime(2015, 6, 25, 20, 52, 18)
        self.modified_at = datetime.datetime(2015, 6, 25, 20, 52, 18)


class Strength(DictMixin):
    def _ensure_data(self):
        pass

    def __init__(self):
        self.href = 'href'
        self.min_symbol = 0
        self.min_upper_case = 1
        self.min_length = 8
        self.sp_http_status = 200
        self.min_numeric = 1
        self.min_lower_case = 1
        self.min_diacritic = 0
        self.max_length = 100


class AccountCreationPolicy(object):
    def __init__(self):
        self.strength = Strength()
        self.verification_email_status = 'DISABLED'


class PasswordPolicy(object):
    def __init__(self):
        self.strength = Strength()
        self.reset_email_status = 'ENABLED'


class AccountStore(object):
    def __init__(self):
        self.password_policy = PasswordPolicy()
        self.account_creation_policy = AccountCreationPolicy()
        self.provider = Provider()


class Provider(DictMixin):
    def _ensure_data(self):
        pass

    def __init__(self):
        self.href = 'href'
        self.provider_id = 'google'
        self.client_id = 'id'
        self.client_secret = 'secret'
        self.enabled = True
        self.sp_http_status = 200
        self.redirect_uri = 'https://myapplication.com/authenticate'
        self.created_at = datetime.datetime(2015, 6, 25, 20, 52, 18)
        self.modified_at = datetime.datetime(2015, 6, 25, 20, 52, 18)


class AccountStoreMapping(object):
    def __init__(self):
        self.account_store = AccountStore()


class AccountStoreMappings(object):
    def __init__(self, asms):
        self.asms = asms

    def __iter__(self):
        for a in self.asms:
            yield a


class Application(DictMixin):
    name = ''
    href = ''

    def _ensure_data(self):
        pass

    def __init__(self, name, href):
        self.name = name
        self.href = href
        self.account_store_mappings = AccountStoreMappings([AccountStoreMapping()])
        self.oauth_policy = OauthPolicy()
        self.default_account_store_mapping = AccountStoreMapping()


class Applications(object):
    def __init__(self, apps):
        self.apps = apps

    def get(self, href):
        for app in self.apps:
            if app.href == href:
                return app

        raise StormpathError('I don\'t exist.', http_status=404)

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
