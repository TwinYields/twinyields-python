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
        params = "T2M_MAX,T2M_MIN,ALLSKY_SFC_SW_DWN,PRECTOTCORR,RH2M,WS2M"
        query = "&community=RE&longitude={longitude}&latitude={latitude}&start={start}&end={end}&format=JSON&time-standard=LST"
        api_request_url = url + params + query.format(longitude=longitude, latitude=latitude, start=start,
                                                           end=end)
        response = requests.get(url=api_request_url, verify=True, timeout=30.00)
        content = json.loads(response.content.decode('utf-8'))
        if content["messages"]:
            print(content["messages"])
        data = content["properties"]["parameter"]
        df = pd.DataFrame.from_dict(data, orient="columns")
        df["date"] = [pd.Timestamp(x) for x in df.index]
        df["year"] = df["date"].dt.year
        df["day"] = df["date"].dt.dayofyear
        df = df[["year", "day", "ALLSKY_SFC_SW_DWN", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "WS2M"]]
        df.columns = ["year", "day", "radn", "maxt", "mint", "rain", "rh", "windspeed"]
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
        del df_mean["year"]
        self.db.save_dataframe(df, "NasaPowerDaily")
        self.db.save_dataframe(df_mean, "NasaPowerDailyMean")

    def update_history(self, years=20):
        s = datetime.datetime.now().year - 1 - years
        e = datetime.datetime.now().year - 1
        f,z = self.db.get_field()
        self.update_met_db(f["latitude"].round(3)[0], f["longitude"].round(3)[0], f"{s}0101", f"{e}1231")






