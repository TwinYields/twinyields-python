# Sentinel2 code extracted from
# https://github.com/ollinevalainen/satellitetools
# commit 8bb622a50744745c5a6a08c544e1f884e2f30e22
# Folders: aws_cog, biophys and common
# License MIT
# the copied version was not installable via pip


from . import biophys
from .common.classes import AOI, RequestParams
from .common.sentinel2 import S2_BANDS_10_20_COG
from .common.wrappers import get_s2_qi_and_data

class Sentinel2(object):

    def __init__(self):
        self.data = None

    def get_data(self, geometry, datestart, dateend, qi_threshold=0.1, crs="EPSG:4326"):
        aoi = AOI("A", geometry, crs)
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

    def compute_indices(self):
        self.data = biophys.run_snap_biophys(self.data, "LAI")
        self.data = biophys.run_snap_biophys(self.data, "FAPAR")
        self.data = biophys.compute_ndvi(self.data)

