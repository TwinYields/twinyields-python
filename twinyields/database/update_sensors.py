import pymongo
from ..sensors import SoilScoutAPI
from .. import Config
import datetime
import time

class SoilScoutUpdater(object):

    def __init__(self, devices = None):
        client = pymongo.MongoClient()
        db = client.get_database(Config.database)
        self.collection = db.get_collection("SoilScout")
        if devices is None:
            self.devices = Config().userconfig["SoilScout"]["devices"]
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




