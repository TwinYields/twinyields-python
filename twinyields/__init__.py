import tomli
from pathlib import Path
import dataclasses
from dataclasses import dataclass
import datetime

@dataclass
class Simulation:
    start_date: str = f"{datetime.datetime.now().year}-05-01"
    path: str = Path.home().as_posix() + "/twinyields/digitaltwin/"

@dataclass
class SoilScout:
    user: str = None
    password: str = None
    devices: list = dataclasses.field(default_factory=list)

class Config(object):
    database = "TwinYields"
    config = {}
    Simulation = Simulation()
    SoilScout = SoilScout()

    def __init__(self):
        cfg_file = Path.home() / ".twinyields/config.toml"
        cfg = tomli.load(open(cfg_file, "rb"))
        Config.config = cfg
        if "Simulation" in cfg:
            Config.Simulation = Simulation(**cfg["Simulation"])
        if "SoilScout" in cfg:
            Config.SoilScout = SoilScout(**cfg["SoilScout"])


_cfg = Config()
