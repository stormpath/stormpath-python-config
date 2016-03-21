from path import Path


class LoadFilePathStrategy(object):
    """Base class for all strategies that load configuration from a
    file.
    """
    def __init__(self, file_path, must_exist=False):
        self._file_path = Path(file_path).expand()
        self.file_path = self._file_path.abspath()
        self.must_exist = must_exist

    def _process_file_path(self, config):
        raise NotImplementedError('Subclasses must implement this method.')

    def process(self, config=None):
        if config is None:
            config = {}

        if self.file_path.startswith('~'):
            if self.must_exist:
                raise Exception('Unable to load "%s". Environment home not set.' % self.file_path)

            return config

        if not self._file_path.exists():
            if self.must_exist:
                raise Exception('Config file "' + self.file_path + '" doesn\'t exist.')

            return config

        return self._process_file_path(config)
