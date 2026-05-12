from .database import TwinDataBase
from ..eo import Sentinel2
from ..config import Config
import datetime
import os
from pathlib import Path
from farmingpy import eo
import re
import numpy as np
import xarray as xr
import polars_h3 as plh3
import polars as pl
from pyproj import Transformer
import pymongoarrow as pma

class EOUpdater(object):

    def __init__(self):
        self.db = TwinDataBase()
        self.collection = self.db.get_collection("S2Biophys")
        
        self.fields = None
        self.client = None
        self.fields = self.db.read_geo_dataframe("Parcels")
        self.biopars = ["LAI", "FCOVER", "FAPAR", "LAI_Cab", "LAI_Cw"]
        self.config = Config()
        self.path = Path(self.config.Simulation.path) / "eodata"
        os.makedirs(self.path / "s2data", exist_ok=True)
        os.makedirs(self.path / "biophys", exist_ok=True)
        self.h3_resolution = 12

    def update(self):
        for i in range(self.fields.shape[0]):
            self.update_field(self.fields.iloc[[i]])

    def download_s2(self, parcel, start_date, end_date):
        self.client = eo.S2CDSE(parcel)
        self.client.get_data(start_date, end_date)
        return self.client.data
    
    def compute_biophys(self, ds):
        pars = []
        for par in self.biopars:
            biopar = eo.BioPhysS2tbx(par)
            par_ds = ds.groupby("time").apply(biopar)
            #pardict[par] = par_ds
            pars.append(par_ds)
        return xr.concat(pars, dim="band")
    

    def ds_to_h3(self, ds, par, resolution=None):
        if resolution is None:
            resolution = self.h3_resolution
        transformer = Transformer.from_crs(ds.rio.crs, "epsg:4326")
        N = len(ds.time)
        dfs = []
        for tidx in range(N):
            tds = ds.sel(band=par).isel(time=tidx)
            df = tds.to_dataframe("value").reset_index().dropna()
            lat, lon = transformer.transform(df["x"], df["y"])
            df["lat"] = lat
            df["lon"] = lon

            df = pl.DataFrame(df).with_columns(
                        plh3.latlng_to_cell(
                            "lat",
                            "lon",
                            resolution=resolution,
                            return_dtype=pl.Utf8,
                        ).alias("h3cell")
                    )
            sdf = df.group_by(["h3cell", "band", "time"]).agg(pl.mean("value"))
            coords = sdf.select(plh3.cell_to_latlng("h3cell"))
            locations = [{"type" : "Point", "coordinates" :  c} for c in coords["h3cell"].to_list()]
            sdf = sdf.with_columns(geometry = pl.Series(locations))
            dfs.append(sdf)
        return pl.concat(dfs)
    
    def save_h3_biophys(self, ds, parcel):
        for par in self.biopars:
            df = self.ds_to_h3(ds, par)
            df = df.with_columns(parcel = pl.lit(parcel) )
            count = pma.api.write(self.collection, df)
            print(parcel, par, count)

    def save_daily_dataset(self, ds, type, parcel):
        N = len(ds.time)
        if type == "s2":
            out_path = self.path / "s2data"
        elif type == "biophys":
            out_path = self.path / "biophys"
        else:
            raise Exception("Unkown type")
        for tidx in range(N):
            tds = ds.isel(time=tidx)
            fname = out_path /  (f"{parcel}_{tds.time.values}".split(".")[0].replace(":", "") + ".nc")
            tds.to_netcdf(fname)

    def update_field(self, parcel=None, year=None):
        parcel_name = parcel["name"].iloc[0]
        last = list(self.collection.find({"parcel": parcel_name}).sort("time", -1).limit(1))
        if year is None:
            year = datetime.datetime.now().year

        if not last or last[0]["time"].year != year:
            startdate = datetime.date(year, 5, 1)
            #print("No S2 data, starting from", startdate)
        else:
            startdate = (last[0]["time"] + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            #print("Updating S2 data, starting from", startdate)
        
        edate = max(datetime.datetime.now().date(), datetime.date(year, 9, 30))
        enddate = edate.strftime("%Y-%m-%d")

        print(f"Updating {parcel_name}: {startdate} - {enddate}")
        print("Downloading S2 data")
        ds = self.download_s2(parcel, startdate, enddate)
        if ds:
            self.save_daily_dataset(ds, "s2", parcel_name)
            par_ds = self.compute_biophys(ds)
            self.save_daily_dataset(ds, "biophys", parcel_name)

            print("Saving H3 aggregation to DB")
            self.save_h3_biophys(par_ds, parcel_name)
        else:
            print("No new data")
            
        
        





