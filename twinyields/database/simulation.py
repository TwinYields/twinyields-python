import pandas as pd
from pymongo import MongoClient
from .database import TwinDataBase
from .. import Config
import os

class SimulationUpdater(object):

    def __init__(self):
        self.db = TwinDataBase()

    def update(self):
        simulations = self.db.get_simfiles()
        for idx, row in simulations.iterrows():
            dbpath = os.path.splitext(os.path.join(Config.Simulation.path, row.path))[0] + ".db"
            self.copy_simulation(dbpath.replace("\\", "/"), row.field)

    """Copy APSIM simulation from sqlite to MongoDB collection"""
    def copy_simulation(self, simdb, field):
        print(simdb)
        df = pd.read_sql_table("Report", "sqlite:///" + simdb)
        df["field"] = field
        sim_dict = df.to_dict(orient="records")
        client = MongoClient()
        db = client.TwinYields
        db.drop_collection("SimulationData")
        col = db.SimulationData
        col.insert_many(sim_dict)
        print(f"Copied to from {simdb}")


