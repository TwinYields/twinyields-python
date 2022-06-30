import pandas as pd
import pymongo
import rioxarray
from bson import json_util
import geopandas as gpd
import pandas as pd
import rasterio
import datetime
import tempfile
from . import apsim

class TwinDataBase(object):

    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client.get_database("TwinYields")

    def __getitem__(self, item):
        return self.db[item]

    def get_collection(self, col):
        return self.db.get_collection(col)

    def drop_collection(self, col):
        self.db.drop_collection(col)

    def get_field(self, field=None):
        col = self.db.get_collection("Fields")
        if field is None:
            fld = col.find_one({})
        else:
            fld = col.find_one({"name": field})
        features = [{
            'geometry': fld["geometry"],
            'properties': {'name': fld['name'],
                           'longitude': fld["location"]["coordinates"][0],
                           'latitude' : fld["location"]["coordinates"][1] }
        }]
        field_df = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")

        fcol = {"type": "FeatureCollection", "features": []}
        for zone in fld["zones"]:
            fcol["features"].append({
                'id': zone['name'],
                'geometry': zone["geometry"],
                'properties': {'field_name': fld['name'], 'zone': zone['name'], 'rate': zone['rates'][0]}
            })
        zone_df = gpd.GeoDataFrame.from_features(fcol, crs="EPSG:4326")
        return field_df, zone_df

    def _find_df(self, collection, filter={}, fields={}):
        if fields:
            q = self.db[collection].find(filter, fields)
        else:
            q = self.db[collection].find(filter)
        return pd.DataFrame.from_records(list(q), exclude=["_id"])

    def get_s2(self, filter={}):
        return self._find_df("Sentinel2", filter)
        #col = self.db.get_collection("Sentinel2")
        #data = col.find(filter)
        #return pd.DataFrame.from_records(data, exclude=["_id"])

    def get_simfiles(self):
        col = self.db.get_collection("SimulationFiles")
        data = col.find()
        return pd.DataFrame.from_records(data, exclude=["_id"])

    def get_simulation_data(self, filter={}):
        col = self.db.get_collection("SimulationData")
        data = col.find(filter)
        return pd.DataFrame.from_records(data, exclude=["_id"])

    def get_farmiaisti(self, device):
        col = self.db.get_collection("Farmiaisti")
        data = col.find({"device": device})
        return pd.DataFrame.from_records(data, exclude=["_id"])

    def get_metfile(self, weatherfile, device):
        data = self.get_farmiaisti(device)
        #Filter out partial days
        if data.time.max().hour < 23:
            data = data[data.time < data.time.max().floor("D")]
        df = apsim.farmiaisti_to_met(data)
        year = datetime.datetime.now().year
        maxday = df[df["year"] == year].day.max()
        history_df = self.get_historical_met(maxday, year)

        info = self.db["FarmiaistiStations"].find_one({"description": device})
        lat, lon = info["location"].split(",")
        df = pd.concat([df, history_df])
        apsim.df_to_met(weatherfile, df, device, lat, lon)
        print(f"Weather data written to {weatherfile}")

    def get_historical_met(self, start, year):
        cols = ["year", "day", "radn", "maxt", "mint", "rain", "rh", "windspeed"]
        fields = {k: 1 for k in cols}
        history_df = self._find_df("NasaPowerDailyMean", filter={"day": {"$gt": int(start)}},
            fields=fields)
        history_df["year"] = year
        history_df = history_df[cols]
        return history_df.round(1)

    def save_dataframe(self, df, col_name, drop=False):
        data_dict = df.to_dict(orient="records")
        if drop:
            self.db.drop_collection(col_name)
        col = self.get_collection(col_name)
        col.insert_many(data_dict)

    """Save raster file to database"""
    def save_raster(self, rfile, col_name):
        data = open(rfile, "rb").read()
        r = rasterio.open(rfile)
        tags = r.tags()
        doc = {"raster": data, "field" : tags["field"],
            "time": datetime.datetime.strptime(tags["time"], "%Y-%m-%dT%H:%M:%S"),
            "path": rfile
        }
        col = self.db.get_collection(col_name)
        col.insert_one(doc)

    """Get Sentinel2 rasters for a field, use limit=1 to get only most recent
    """
    def get_s2_raster(self, field, limit=100):
        col = self.db.get_collection("Sentinel2Rasters")
        docs = col.find({"field": field}).sort("time", -1).limit(limit)
        rasters = []
        #There seem to be some issues with MemoryFile (occasional crashes) at least on Windows
        for doc in docs:
            with rasterio.MemoryFile(doc["raster"]) as raster:
                with raster.open() as r:
                    ds = rioxarray.open_rasterio(r, cache=True)
                    ds["time"] = doc["time"]
                    rasters.append(ds.copy(deep=True))
        return rasters


    """Get specific Sentinel2 bands for a field, use limit=1 to get only most recent"""
    def get_s2_band(self, field, band, limit=100):
        col = self.db.get_collection("Sentinel2Rasters")
        docs = col.find({"field": field}).sort("time", -1).limit(limit)
        bounds = []
        rasters = []
        times = []
        for doc in docs:
            rfile = rasterio.MemoryFile(doc["raster"])
            r = rfile.open()
            idx = r.indexes[r.descriptions.index(band)]
            rasters.append(r.read(idx))
            bounds.append(r.bounds)
            times.append(doc["time"])
            r.close()
        return rasters, bounds, times










