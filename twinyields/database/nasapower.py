import datetime
import json
import requests
import pandas as pd
from . import TwinDataBase


class NasaPowerUpdater(object):

    def __init__(self):
        self.db = TwinDataBase()

    def get_met_dataframe(self, latitude, longitude, start, end):
        url = "https://power.larc.nasa.gov/api/temporal/daily/point?parameters="
        # From apsimx R package
        params = "T2M,T2M_MAX,T2M_MIN,ALLSKY_SFC_SW_DWN,PRECTOTCORR,RH2M,WS2M,EVPTRNS,GWETROOT,GWETTOP"

        query = "&community=AG&longitude={longitude}&latitude={latitude}&start={start}&end={end}&format=JSON&time-standard=LST"
        api_request_url = url + params + query.format(longitude=longitude, latitude=latitude, start=start,
                                                           end=end)
        response = requests.get(url=api_request_url, verify=True, timeout=30.00)
        content = json.loads(response.content.decode('utf-8'))
        if content["messages"]:
            print(content["messages"])
        data = content["properties"]["parameter"]
        df = pd.DataFrame.from_dict(data, orient="columns")
        df["date"] = [pd.Timestamp(x) for x in df.index]
        #df["year"] = df["date"].dt.year
        df["day"] = df["date"].dt.dayofyear
        df = df[["date", "day", "ALLSKY_SFC_SW_DWN", "T2M", "T2M_MAX", "T2M_MIN", 
                 "PRECTOTCORR", "RH2M", "WS2M", "EVPTRNS", "GWETROOT", "GWETTOP"]]
        # GWE = soil wetness
        df.columns = ["date", "day", "radn", "meant", "maxt", "mint", "rain", "rh", "windspeed", "ET0", "swroot", "swtop"]
        df["latitude"] = latitude
        df["longitude"] = longitude
        return df

    def update_met_db(self, latitude, longitude, start, end):
        #TODO only request new values
        self.db.drop_collection("NasaPowerDaily")
        self.db.drop_collection("NasaPowerDailyMean")
        df = self.get_met_dataframe(latitude, longitude, start, end)
        # daily means to use as forecast
        df_mean = df.groupby(["day"], as_index=False).mean()
        self.db.save_dataframe(df, "NasaPowerDaily")
        self.db.save_dataframe(df_mean, "NasaPowerDailyMean")

    def update_history(self, years=20):
        s = datetime.datetime.now().year - 1 - years
        e = datetime.datetime.now().year - 1
        lon, lat = self.db.read_geo_dataframe("Parcels").union_all().centroid.xy
        self.update_met_db(round(lat[0], 3), round(lon[0], 3), f"{s}0101", f"{e}1231")






