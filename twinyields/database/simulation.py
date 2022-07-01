import pandas as pd
from pymongo import MongoClient
from .database import TwinDataBase
from ..config import Config
import os

class SimulationUpdater(object):

    def __init__(self):
        self.db = TwinDataBase()

    def update(self):
        self.db.drop_collection("SimulationData")
        simulations = self.db.get_simfiles()
        for idx, row in simulations.iterrows():
            dbpath = os.path.splitext(os.path.join(Config.Simulation.path, row.path))[0] + ".db"
            self.copy_simulation(dbpath.replace("\\", "/"), row.field)

    """Copy APSIM simulation from sqlite to MongoDB collection"""
    def copy_simulation(self, simdb, field):
        df = pd.read_sql_table("Report", "sqlite:///" + simdb)
        df["field"] = field
        df = df.rename(mapper=lambda x: x.replace(".", ""), axis=1)
        sim_dict = df.to_dict(orient="records")
        col = self.db["SimulationData"]
        col.insert_many(sim_dict)
        print(f"Copied to MongoDB from {simdb}")


