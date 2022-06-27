# Sentinel2 code under folders aws_cog, biophys and common
# originally extracted from
# https://github.com/ollinevalainen/satellitetools
# commit 8bb622a50744745c5a6a08c544e1f884e2f30e22
# License MIT
# the copied version was not installable via pip

from . import biophys
from .common.classes import AOI, RequestParams
from .common.sentinel2 import S2_BANDS_10_20_COG
from .common.wrappers import get_s2_qi_and_data
import rioxarray
import pandas as pd

class Sentinel2(object):

    def __init__(self):
        self.data = None
        self.zone_data = {}

    def get_data(self, field, datestart, dateend, zones=None, qi_threshold=0.1, crs="EPSG:4326"):
        aoi = AOI(field.iloc[0]["name"], field.iloc[0].geometry, field.crs)
        datasource = "aws_cog"
        request = RequestParams(
            datestart,
            dateend,
            datasource=datasource,
            bands=S2_BANDS_10_20_COG,
            target_gsd=10.0)
        aoi.qi, aoi.data = get_s2_qi_and_data(aoi, request, qi_threshold=qi_threshold)
        self.data = aoi.data
        self.compute_indices()
        self.data = self.data.rio.write_crs(self.data.crs)
        if zones is not None:
            self.get_zones()

    def get_zones(self, zones):
        zones = zones.to_crs(self.data.rio.crs)
        self.zone_data = {}
        for i, z in zones.iterrows():
            print("Processing " + z.zone)
            zdata = self.data.rio.clip([z.geometry])
            self.zone_data[z.zone] = zdata

    def _zone_index(self, z, name):
        return pd.DataFrame({
            "zone": name,
            "field_name": z.name,
            "time": z.time,
            "LAI": z.lai.mean(("x", "y")).data,
            "FAPAR": z.fapar.mean(("x", "y")).data,
            "NDVI": z.ndvi.mean(("x", "y")).data
        })

    def zone_indices(self):
        return pd.concat([self._zone_index(z, name) for (name, z) in self.zone_data.items()])

    def compute_indices(self):
        self.data = biophys.run_snap_biophys(self.data, "LAI")
        self.data = biophys.run_snap_biophys(self.data, "FAPAR")
        self.data = biophys.compute_ndvi(self.data)
