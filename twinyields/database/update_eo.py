from .database import TwinDataBase
from ..eo import Sentinel2
from ..config import Config
import datetime
import os
from pathlib import Path
from farmingpy import eo

class EOUpdater(object):

    def __init__(self):
        self.db = TwinDataBase()
        self.name = "Sentinel2"
        self.fields = None
        self.client = None
        self.fields = self.db.read_geo_dataframe("Parcels")


    def update(self):
        for i in self.fields.shape[0]:
            self.update_field(self.fields.iloc[[i]])

    def download_s2(self, parcel, start_date, end_date):
        self.client = eo.S2CDSE(parcel)
        self.client.get_data(start_date, end_date)
        return self.client.data
        
    def update_field(self, parcel=None):
        col = self.db.get_collection(self.name)
        parcel = parcel["name"].iloc[0]

        last = list(col.find({"field_name": parcel}).sort("time", -1).limit(1))
        if not last:
            startdate = Config.Simulation.start_date
            print("No S2 data, starting from", startdate)
        else:
            startdate = (last[0]["time"] + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            print("Updating S2 data, starting from", startdate)
        enddate = datetime.datetime.now().strftime("%Y-%m-%d")
        ds = self.download_s2(startdate, enddate)
        # TODO Saving to database as h3?

        
        #s2 = Sentinel2()
        #ret = s2.get_data(field, startdate, enddate, zones=zones)
        #if ret:
        #    #s2.get_zones(zones)
        #    s2_table = s2.zone_indices()
        #    self.db.save_dataframe(s2_table, self.name)
        #    rasters = s2.to_rasters(os.path.join(Config.Simulation.path, "rasters/sentinel2"))
        #    print("Writing rasters to MongoDB")
        #    for rfile in rasters:
        #        self.db.save_raster(rfile, "Sentinel2Rasters")
        #    print("Done")



