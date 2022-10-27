import farmingpy as fp
import numpy as np

class Sowing(object):

    def __init__(self, taskfile, min_area=1000):
        z, f, tl = self.extract_zones(taskfile, min_area)
        self.tl = tl
        self.zones = z
        self.field = f
        self.fieldname = tl.field
        self.products = tl.products

    def extract_zones(self, taskfile, min_area):
        tl = fp.TimeLogData(taskfile)
        idata = tl.rasterize_rates()
        zones = fp.unique_zones(idata, min_area=min_area)
        p1 = sorted(tl.products.keys())
        fdf = fp.unique_zones(idata[p1].where(np.isnan, 1))
        fdf = fdf.to_crs("epsg:4326")
        return zones, fdf, tl




