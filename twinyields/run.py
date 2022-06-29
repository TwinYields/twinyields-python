import sys
from . import database
from .config import Config
import os
import subprocess
from pathlib import Path
import argparse

"""
This class takes care of running and initializing Digital Twin 
sensor updates and simulation 
"""
class DigitalTwin(object):

    def __init__(self):
        self.db = database.TwinDataBase()
        self.twinconsole = (Path.home() / "DigitalTwin/TwinConsole/TwinConsole").as_posix()

    def init(self):
        subprocess.run([self.twinconsole, "init"], cwd=Config.Simulation.path)

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

    def collect_simulation_data(self):
        su = database.SimulationUpdater()
        su.update()

    def run(self):
        self.update_model_inputs()
        subprocess.run([self.twinconsole, "run"], cwd=Config.Simulation.path)
        self.collect_simulation_data()


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
