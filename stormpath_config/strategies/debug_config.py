from json import dumps
from logging import getLogger

from .. import log


class DebugConfigStrategy(object):
    """Represents a strategy that when used dumps the config to the
    provided logger.
    """
    def __init__(self, logger=None, section=None):
        self.section = section
        if logger is None:
            self.log = log
        else:
            self.log = getLogger(logger)

    def process(self, config):
        message = ''
        if self.section is not None:
            message = '%s:\n' % self.section

        message = "%s%s\n" % (message, dumps(config, sort_keys=True, indent=4, separators=(',', ': ')))
        self.log.debug(message)

        return config
