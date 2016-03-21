from yaml import load

from ..helpers import _extend_dict
from .load_file_path import LoadFilePathStrategy


class LoadFileConfigStrategy(LoadFilePathStrategy):
    """Represents a strategy that loads configuration from either a
    JSON or YAML file into the configuration.
    """
    def _process_file_path(self, config):
        f = open(self.file_path, 'r')
        try:
            loaded_config = load(f.read())
        except Exception as e:
            raise Exception('Error parsing file "%s".\nDetails: %s' % (self.file_path, e.message))

        return _extend_dict(config, loaded_config)
