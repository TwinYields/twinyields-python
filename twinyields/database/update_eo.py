from .database import TwinDataBase
from ..eo import Sentinel2
from .. import Config
import datetime

class EOUpdater(object):

    def __init__(self):
        self.db = TwinDataBase()
        self.name = "Sentinel2"

    def update_field(self, field=None):
        # TODO check database for last processed date and get only new images
        startdate = Config().userconfig["Simulation"]["startdate"]
        enddate = datetime.datetime.now().strftime("%Y-%m-%d")
        field, zones = self.db.get_field()
        s2 = Sentinel2()
        s2.get_data(field, startdate, enddate)
        s2.get_zones(zones)
        s2_table = s2.zone_indices()
        self.db.save_dataframe(s2_table, self.name)
