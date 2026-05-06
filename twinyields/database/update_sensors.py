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


DEFAULT_STARTDATE = datetime.datetime(2020, 4, 1)

class SoilScoutUpdater(object):

    def __init__(self, devices = None, active = True):
        self.client = pymongo.MongoClient()
        self.db = self.client.get_database(Config.database)
        self.collection = self.db.get_collection("SoilScout")
        sc = SoilScoutAPI()
        if devices is None:
            self.all_devices = sc.devices()
        else:
            self.all_devices = devices
        
        devices = [d for d in self.all_devices if d["last_seen"] is not None and d["device_type"] == "hydra"]

        # Only update devices that have been active this year
        if active:
            year = datetime.datetime.now().year
            devices = [d for d in devices if d["last_seen"].split("-")[0] == str(year)]
       
        self.devices = [d["id"] for d in devices]
        self._since_time = DEFAULT_STARTDATE
        #Ask at most 180 days at a time, API seems to error otherwise
        self.max_dates = datetime.timedelta(180)

    def update(self):
        dev_collection = self.db.get_collection("SoilScoutDevices")
        device_data = {"timestamp" : datetime.datetime.now(), "devices" : self.all_devices}
        dev_collection.insert_one(device_data)

        for device in self.devices:
            print("Updating SoilScout device", device)
            self.update_device(device)


    # Update until all data has been collected
    # start from earliest possible data and try until
    # last measurement data for the sensor is found
    def update_device(self, device):
        dt = 1
        self._since_time = DEFAULT_STARTDATE
        first_request  = True
        attempt_count = 0
        while dt > 0:
            dt = self._update_device(device, first_request)
            first_request = False
            time.sleep(1) #Not sure if there are API limits
            attempt_count += 1
            if attempt_count > 20:
                break
        print("Done!")

    # Updates max 180 days
    def _update_device(self, device, first_request = True):
        device_info = [d for d in self.all_devices if d["id"] == device][0]
        try:
            last_measurement = datetime.datetime.fromisoformat(
                device_info["last_measurement"]["timestamp"].split("+")[0])
        except:
            print(f"No measurements for device {device}")
            print(device_info)
            return 0

        last = list(self.collection.find({"device": device}).sort("timestamp", -1).limit(1))
        if last:
            last_t = last[0]["timestamp"]
            dt = (last_measurement - last_t).total_seconds()
            if dt < 30:
                return 0
        
        if last and first_request:
            # Try once to query from last DB date
            since_time = last_t  + datetime.timedelta(seconds=10)
            self._since_time = since_time
            print("Found last measurement, starting from", since_time)
        else:
            since_time = self._since_time


        sc = SoilScoutAPI()
        #Ask at most 180 days at a time, API seems to error otherwise
        year_dt = since_time + self.max_dates
        now = datetime.datetime.now()
        until_time = min(year_dt, now)
        
        since = since_time.strftime("%Y-%m-%dT%H:%M:%S")
        until = until_time.strftime("%Y-%m-%dT%H:%M:%S")

        print("Updating from ", since, "until", until, 
              "last_measurement", last_measurement.date)
    
        measurements = sc.measurements(since=since, until=until, device=device)
        
        if measurements[0]:
            for m in measurements:
                self.collection.insert_many(m)
            return (now-until_time).total_seconds()
        elif (last_measurement - until_time).days > 0:
            self._since_time = self._since_time + self.max_dates
            return 1
        else:
            return 0

class FarmiaistiUpdater(object):

    def __init__(self):
        self.db = TwinDataBase()
        self.collection = self.db.get_collection("Farmiaisti")
        self.api = Farmiaisti(user=Config.Farmiaisti.user, password=Config.Farmiaisti.password)
        self.devices = self.api.get_devices()["devices"]

    def update(self):
        for device in self.devices:
            print(f"Updating Farmiaisti device: {device['id_val']}")
            self.update_device(device)

    def update_device(self, device):
        last = list(self.collection.find({"device": device["id_val"]}).sort("time", -1).limit(1))
        if not last:
            since_time = DEFAULT_STARTDATE
            print(f"No data for device {device['id_val']}, starting from", since_time)
        else:
            since_time = last[0]["Time"] + datetime.timedelta(minutes=5) #Measurement done every 15 minutes
            print(f"Updating device {device['id_val']}, starting from", since_time)
        now = datetime.datetime.now()
        df = self.api.get_measurements(since_time, now, device)

        if not df.empty:
            #print(df.time.max())
            df["device"] = device["id_val"]
            self.db.save_dataframe(df, "Farmiaisti")
            N = df.shape[0]
            print(f"Wrote {N} new measurements to database")
        else:
            print("Nothing to update")





