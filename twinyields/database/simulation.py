import pandas as pd
from pymongo import MongoClient

"""Copy APSIM simulation from sqlite to MongoDB collection"""
def copy_simulation(simdb):
    df = pd.read_sql_table("Report", "sqlite:///" + simdb)
    sim_dict = df.to_dict(orient="records")
    client = MongoClient()
    db = client.TwinYields
    db.drop_collection("Simulation")
    col = db.Simulation
    col.insert_many(sim_dict)
    print("Data copied to collection: TwinYields.Simulation")


