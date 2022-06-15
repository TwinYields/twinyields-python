import tomli
from pathlib import Path

class Config(object):

    database = "TwinYields"

    def __init__(self):
        cfg_file = Path.home() / ".twinyields/config.toml"
        self._config = tomli.load(open(cfg_file, "rb"))

    @property
    def userconfig(self):
        return self._config

