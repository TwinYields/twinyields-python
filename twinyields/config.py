import tomli
from pathlib import Path
import dataclasses
from dataclasses import dataclass
import datetime

@dataclass
class Simulation:
    start_date: str = f"{datetime.datetime.now().year}-05-01"
    path: str = Path.home().as_posix() + "/DigitalTwin/"

@dataclass
class SoilScout:
    user: str = None
    password: str = None
    devices: list = dataclasses.field(default_factory=list)

@dataclass
class Farmiaisti:
    user: str = None
    password: str = None
    devices: list = dataclasses.field(default_factory=list)

@dataclass
class Database:
    db: str = "mongo"
    table: str = "TwinYields"
    user: str = None
    password: str = None

class Config(object):

    config = {}
    Simulation = Simulation()
    SoilScout = SoilScout()
    Farmiaisti = Farmiaisti()

    def __init__(self):
        cfg_file = Path.home() / ".twinyields/config.toml"
        cfg = tomli.load(open(cfg_file, "rb"))
        Config.config = cfg
        if "Simulation" in cfg:
            Config.Simulation = Simulation(**cfg["Simulation"])
        if "SoilScout" in cfg:
            Config.SoilScout = SoilScout(**cfg["SoilScout"])
        if "Farmiaisti" in cfg:
            Config.Farmiaisti = Farmiaisti(**cfg["Farmiaisti"])
        if "database" in cfg:
            Config.DataBase = Database(**cfg["database"])

_cfg = Config()
