from .database import TwinDataBase
from ..eo import Sentinel2
from ..config import Config
import datetime
import os
from pathlib import Path

class EOUpdater(object):

    def __init__(self):
        self.db = TwinDataBase()
        self.name = "Sentinel2"

    def update(self):
        fields = self.db["Fields"].find()
        for f in fields:
            self.update_field(f["name"])

    def update_field(self, field=None):
        col = self.db.get_collection(self.name)
        last = list(col.find({"field_name": field}).sort("time", -1).limit(1))
        if not last:
            startdate = Config.Simulation.start_date
            print("No S2 data, starting from", startdate)
        else:
            startdate = (last[0]["time"] + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            print("Updating S2 data, starting from", startdate)
        enddate = datetime.datetime.now().strftime("%Y-%m-%d")
        field, zones = self.db.get_field(field)
        s2 = Sentinel2()
        ret = s2.get_data(field, startdate, enddate, zones=zones)
        if ret:
            #s2.get_zones(zones)
            s2_table = s2.zone_indices()
            self.db.save_dataframe(s2_table, self.name)
            rasters = s2.to_rasters(os.path.join(Config.Simulation.path, "rasters/sentinel2"))
            print("Writing rasters to MongoDB")
            for rfile in rasters:
                self.db.save_raster(rfile, "Sentinel2Rasters")
            print("Done")



