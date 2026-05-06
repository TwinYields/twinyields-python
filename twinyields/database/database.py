import pandas as pd
import pymongo
import rioxarray
from bson import json_util
import geopandas as gpd
import pandas as pd
import rasterio
import datetime
import tempfile
import pyet
from . import apsim
import numpy as np

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
            feats = {
                'id': zone['name'],
                'geometry': zone["geometry"],
                'properties': {'field_name': fld['name'], 'zone': zone['name']}
            }
            for r in range(len(zone["rates"])):
                feats["properties"][f"rate{r}"] =  zone["rates"][r]
                feats["properties"][f"product{r}"] = zone["products"][r]
            fcol["features"].append(feats)

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

    def get_farmiaisti(self, device, filter = {}):
        col = self.db.get_collection("Farmiaisti")
        filter.update({"Device name" : device})
        data = col.find(filter)
        return pd.DataFrame.from_records(data, exclude=["_id"])
    
    def get_daily_weather(self, starttime, endtime=None):
        """Get daily weather by combining data from two weather stations"""
        if endtime == None:
            endtime = datetime.datetime.now()
        timefilter = {"Time" : {"$gt" : starttime, "$lte" : endtime}}
        d1 = self.get_farmiaisti("WS11-1", filter=timefilter)
        d2 = self.get_farmiaisti("WS6-13", filter=timefilter)

        d1["date"] = d1["Time"].dt.date
        d1["Radiation"] = d1["Radiation (W/m²)"]*1.0E-6*900
        daily1 = d1.groupby("date", as_index=False).agg(rad=("Radiation",  "sum"), 
                    T = ("Temperature (°C)", "mean"),
                    Tmin = ("Temperature (°C)", "min"),
                    Tmax = ("Temperature (°C)", "max"),
                    wind = ("Wind speed (m/s)", "mean"),
                    vpa = ("Vapor pressure (kPa)", "mean"),
                    hpa = ("Air-pressure (hPa)", "mean")
                    )
        d2["date"] = d2["Time"].dt.date
        d2["rain"] = [float(r) if r is not None else 0.0 for r in d2["Daily rain (mm)"]]

        daily2 = d2.groupby("date", as_index=False).agg(
            RH = ("Humidity (%)", "mean"),
            rain = ("rain", "max")
        )
        wdata = daily1.merge(daily2)
        # Index needed for pyet
        wdata = wdata.set_index(wdata["date"])
        lat = 63*np.pi/180
        
        et = pyet.pm(
               tmean = wdata["T"], 
               lat = lat,
               tmax=wdata["Tmax"], 
               tmin=wdata["Tmin"], 
               wind = wdata["wind"],
               rs = wdata["rad"],
               pressure=wdata["hpa"]/10, 
               elevation=100,
               rh=wdata["RH"])
        wdata["et0"] = et.to_numpy()

        return  wdata.reset_index(drop=True)
        


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

    def save_field(self, field, fieldname, products, zones):
        farm = self.db["Farms"].find_one()
        fdf = field.copy()
        fdf["location"] = fdf.centroid
        ft = fdf.iloc[[0]].__geo_interface__["features"][0]
        p = ft["properties"]
        loc = gpd.GeoSeries(p["location"]).__geo_interface__["features"][0]["geometry"]
        field = {"farmid": farm["_id"], "name": fieldname,
                 "location": loc, "geometry": ft["geometry"]}
        gdf = zones.copy()
        gdf = gdf.to_crs("epsg:4326")
        gdf["location"] = gdf.centroid
        zones = []
        prods = [products[k] for k in sorted(products.keys())]
        for idx in range(gdf.shape[0]):
            ft = gdf.iloc[[idx]].__geo_interface__["features"][0]
            p = ft["properties"]
            loc = gpd.GeoSeries(p["location"]).__geo_interface__["features"][0]["geometry"]
            zone = {"name": f"zone{p['zone']}", "location": loc, "geometry": ft["geometry"],
                    "rates": p["grp"], "products": prods
                    }
            zones.append(zone)
        field["zones"] = zones
        self.db["Fields"].insert_one(field)

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










