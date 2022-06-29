import pymongo
from ..sensors import SoilScoutAPI
from ..config import Config
import datetime
import time
from .database import TwinDataBase
try:
    from farmiaisti import Farmiaisti
except:
    print("Install private library farmiaisti to access Farmiaisti weather station data")

class SoilScoutUpdater(object):

    def __init__(self, devices = None):
        client = pymongo.MongoClient()
        db = client.get_database(Config.database)
        self.collection = db.get_collection("SoilScout")
        if devices is None:
            self.devices = Config.SoilScout.devices
        else:
            self.devices = devices

    def update(self):
        for device in self.devices:
            print("Updating device", device)
            self.update_device(device)

    # Update until all data has been collected
    def update_device(self, device):
        dt = 1
        while dt > 0:
            dt = self._update_device(device)
            time.sleep(5) #Not sure if there are API limits
        print("Done!")

    # Updates max 180 days
    def _update_device(self, device):
        last = list(self.collection.find({"device": device}).sort("timestamp", -1).limit(1))
        #print(last)
        if not last:
            since_time = datetime.datetime(2020, 1, 1)
            print("No data, starting from", since_time)
        else:
            since_time = last[0]["timestamp"] + datetime.timedelta(seconds=10)

        #Ask at most 180 days at a time, API seems to error otherwise
        year_dt = since_time + datetime.timedelta(days=180)
        now = datetime.datetime.now()
        until_time = min(year_dt, now)
        since = since_time.strftime("%Y-%m-%dT%H:%M:%S")
        until = until_time.strftime("%Y-%m-%dT%H:%M:%S")

        print("Updating from ", since, "until", until)
        sc = SoilScoutAPI()
        measurements = sc.measurements(since=since, until=until, device=device)
        if measurements[0]:
            for m in measurements:
                self.collection.insert_many(m)
            return (now-until_time).total_seconds()
        else:
            return 0

class FarmiaistiUpdater(object):

    def __init__(self):
        self.db = TwinDataBase()
        self.collection = self.db.get_collection("Farmiaisti")

    def update(self):
        for device in Config.Farmiaisti.devices:
            print(f"Updating Farmiaisti device: {device}")
            self.update_device(device)

    def update_device(self, device):
        fa = Farmiaisti(user=Config.Farmiaisti.user, password=Config.Farmiaisti.password)
        last = list(self.collection.find({"device": device}).sort("time", -1).limit(1))
        if not last:
            since_time = datetime.datetime(2020, 1, 1)
            print("No data, starting from", since_time)
        else:
            since_time = last[0]["time"] + datetime.timedelta(minutes=5) #Measurement done every 15 minutes
        now = datetime.datetime.now()
        df = fa.get_measurements(since_time, now, device)
        if not df.empty:
            #print(df.time.max())
            self.db.save_dataframe(df, "Farmiaisti")
            N = df.shape[0]
            print(f"Wrote {N} new measurements to database")
        else:
            print("Nothing to update")

    def update_description(self, device):
        fa = Farmiaisti(user=Config.Farmiaisti.user, password=Config.Farmiaisti.password)
        info = fa.get_deviceinfo(device)
        col = self.db.get_collection("FarmiaistiStations")
        col.insert_one(info)




