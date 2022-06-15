import toml
from pathlib import Path

class Config(object):

    database = "TwinYields"

    def __init__(self):
        cfg_file = Path.home() / ".twinyields/config.toml"
        self._config = toml.load(cfg_file)

    @property
    def userconfig(self):
        return self._config

