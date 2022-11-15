import glob
import sys
from . import database
from .config import Config
import os
import subprocess
from pathlib import Path
import argparse
import os
from . import operations
import shutil

"""
This class takes care of running and initializing Digital Twin
sensor updates and simulation
"""
class DigitalTwin(object):

    def __init__(self):
        self.db = database.TwinDataBase()
        self.twinconsole = os.path.join(Config.Simulation.path, "TwinConsole/TwinConsole")
        self.sim_updater = database.SimulationUpdater()

    def init(self):
        os.makedirs(Config.Simulation.path, exist_ok=True)
        os.makedirs(Config.Simulation.path + "/prototypes", exist_ok=True)
        protos = glob.glob(os.path.dirname(__file__) + "/resources/*.apsimx")
        for p in protos:
            shutil.copy(p, Config.Simulation.path + "/prototypes/" + os.path.basename(p))

        self.db.drop_collection("Farms")
        self.db.drop_collection("Fields")
        self.db["Farms"].insert_one({"name": "Jokioinen SmartFarm"})

        # Init from sowing tasks
        tasks = glob.glob(os.path.join(Config.Simulation.path + "tasks/sowing/*"))
        print("Found tasks:", tasks)
        print("Processing task data")
        for task in tasks:
            tfile = f"{task}/TASKDATA.XML"
            s = operations.Sowing(tfile)
            self.db.save_field(s.field, s.fieldname, s.products, s.zones)
        subprocess.run([self.twinconsole, "init"], cwd=Config.Simulation.path)
        # Get historical weather data for site
        print("Getting historical weather from Nasa Power")
        ns = database.NasaPowerUpdater()
        ns.update_history()
        print("Done! You can run the model using twinyields -r")

    def update_sensors(self):
        su = database.SoilScoutUpdater()
        su.update()
        fa = database.FarmiaistiUpdater()
        fa.update()

    def update_eo(self):
        eo = database.EOUpdater()
        eo.update()

    def update_model_inputs(self):
        # TODO support different MET file for different fields
        wf = os.path.join(Config.Simulation.path, "weatherfiles", "Jokioinen.met")
        device = Config.Farmiaisti.devices[0]
        self.db.get_metfile(wf, device)

    def run(self):
        print("Updating weather data")
        self.sim_updater.clean_dbs()
        self.update_model_inputs()
        subprocess.run([self.twinconsole, "run"], cwd=Config.Simulation.path)
        print("Copying to database")
        self.sim_updater.update()

"""Command line interface"""
def twinyields(*, init=False, run=False, update_sensors=False, update_eo=False):
    twin = DigitalTwin()
    if init:
        twin.init()
    if update_sensors:
        twin.update_sensors()
    if update_eo:
        twin.update_eo()
    if run:
        twin.run()

def twinyields_cli():
    parser = argparse.ArgumentParser(description='Control TwinYields digital twin')
    parser = argparse.ArgumentParser(prog="twinyields", description='Control TwinYields digital twin')
    parser.add_argument('-i', '--init', action='store_true',
                        default=False, help="Initialize the digital twin")
    parser.add_argument('-s', '--update-sensors', action='store_true',
                        default=False, help="Fetch updated sensor data")
    parser.add_argument('-e', '--update-eo', action='store_true',
                        default=False, help="Fetch updated satellite data")
    parser.add_argument('-r', '--run', action='store_true',
                        default=False, help="Run the simulation model")

    if len(sys.argv) == 1:
        parser.print_help()
    else:
        args = parser.parse_args()
        twinyields(**vars(args))
