import pymongo
from bson import json_util
import geopandas as gpd

class TwinDataBase(object):

    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client.get_database("TwinYields")

    def get_collection(self, col):
        return self.db.get_collection(col)

    def get_field(self, filter={}):
        col = self.db.get_collection("Fields")
        fld = col.find_one(filter)
        features = [{
            'geometry': fld["geometry"],
            'properties': {'name': fld['name']}
        }]
        field_df = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")

        fcol = {"type": "FeatureCollection", "features": []}
        for zone in fld["zones"]:
            fcol["features"].append({
                'id': zone['name'],
                'geometry': zone["geometry"],
                'properties': {'field_name': fld['name'], 'zone': zone['name'], 'rate': zone['rates'][0]}
            })
        zone_df = gpd.GeoDataFrame.from_features(fcol, crs="EPSG:4326")
        return field_df, zone_df

    def save_dataframe(self, df, col_name, drop=False):
        data_dict = df.to_dict(orient="records")
        if drop:
            self.db.drop_collection(col_name)
        col = self.get_collection(col_name)
        col.insert_many(data_dict)

