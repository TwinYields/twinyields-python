#!/usr/bin/env python
# coding: utf-8

import panel as pn
import numpy as np
import pandas as pd
import xarray as xr
import time
from datetime import datetime, date, timedelta
from suntime import Sun, SunTimeException
import holoviews as hv
import hvplot
from hvplot import pandas
#hvplot.extension('bokeh')
import hvplot.xarray
import rasterio
from rasterio.plot import show
import bokeh
from bokeh.models.formatters import DatetimeTickFormatter
formatter = DatetimeTickFormatter(months='%b %Y')
import folium
from shapely import wkt
from shapely.geometry import Polygon
from twinyields import database

class TwinUI(object):

    def __init__(self):
        self.db = database.TwinDataBase()


        self.today = datetime.fromisoformat("2022-07-20T00:00:00")
        self.starttime = datetime.fromisoformat("2022-05-15T00:00:00")
        #delta = timedelta(days=100)
        #self.starttime = self.today - delta

        print(self.starttime, self.today)
        self.timefilter = {"$gt" : self.starttime, "$lt" : self.today }

    # Map with folium
    def basemap(self):
        # Read field polygon from database and add it to the basemap
        field = self.db["Fields"]
        data_field = pd.DataFrame(list(field.find()))
        longitude, latitude = data_field["location"][0]["coordinates"]

        m = folium.Map(location=[latitude, longitude], zoom_start=15)
        poly = data_field['geometry'][0]
        folium.GeoJson(data=poly, style_function=lambda x: {'fillColor': 'blue'}).add_to(m)

        # Add Soilscout positions to the map
        folium.Marker(
            [60.847659,23.470389], popup="<i>SoilScout 15812</i>", tooltip="SoilScout"
        ).add_to(m)
        folium.Marker(
            [60.847635,23.472858], popup="<i>SoilScout 15800</i>", tooltip="SoilScout"
        ).add_to(m)
        folium.Marker(
            [60.846779,23.470297], popup="<i>SoilScout 15803</i>", tooltip="SoilScout"
        ).add_to(m)
        folium.Marker(
            [60.845016,23.470126], popup="<i>SoilScout 15798</i>", tooltip="SoilScout"
        ).add_to(m)
        folium.Marker(
            [60.847578,23.467154], popup="<i>SoilScout 15807</i>", tooltip="SoilScout"
        ).add_to(m)
        folium.Marker(
            [60.865946,23.434051], popup="<i>Weather station</i>", tooltip="Weather station", icon=folium.Icon(color="red")
        ).add_to(m)

        #Read zone polygon from database and add to map
        for z in data_field['zones'][0]:
            folium.GeoJson(z["geometry"]).add_to(m)

        return m

    # Read Soilscout data from database and make plot to be used in Panel
    def soilscout(self):
        col = self.db["SoilScout"]

        data = pd.DataFrame(list(col.find(
            filter={"timestamp": self.timefilter}).sort("timestamp", 1)))

        mds = hv.Dataset(data, ["timestamp", "device"], ["moisture"])
        mplot = mds.to(hv.Curve).overlay("device").opts(legend_position="bottom_left")

        soilscout_plot = data.hvplot(x = 'timestamp', y='temperature', by='device',
                xformatter=formatter).opts(xlabel = 'Time', ylabel = 'Temperature (C)', legend_position='top')
        return soilscout_plot, mplot

    # Read weather station data from database and make plot to be used in Panel
    def farmiaisti(self):
        col2 = self.db["Farmiaisti"]
        data2 = pd.DataFrame(list(col2.find(filter={"time": self.timefilter}).sort("time", -1)))

        # Save current temperature in variable
        data2_last = pd.DataFrame(list(col2.find().sort("time", -1).limit(1)))
        tmp = str(data2_last[['temp_up']]).split()
        last_weather = tmp[-1]
        farmiaisti_plot = data2.hvplot('time','temp_up',
            xformatter=formatter).opts(xlabel = 'Time',ylabel = 'Temperature (C)')
        return farmiaisti_plot

    def simulation(self):
        simdata = self.db.get_simulation_data()

        yield_ds = hv.Dataset(simdata, ["ClockToday", "Zone"], ["Yield"])
        p1 = yield_ds.to(hv.Scatter).overlay("Zone").opts(width=700, height = 400, legend_position="left")

        lai_ds = hv.Dataset(simdata, ["ClockToday", "Zone"], ["WheatLAI"])
        p2 = lai_ds.to(hv.Scatter).overlay("Zone").opts(width=700, height = 400, legend_position="left")

        #data_zone = self.db.get_simulation_data()
        #Read simulation data from database and make plot to be used in Panel
        #data_zone['Zone'] = pd.to_numeric(data_zone['Zone'].str.replace('zone_', ''))
        #p1 = data_zone.hvplot('ClockToday','Yield', by = "Zone" ,
        #    xformatter=formatter).opts(legend_position='top', xlabel='Time',fontsize = {"legend" : 10}, title='Yield', legend_cols = 2)
        #p2 = data_zone.hvplot('ClockToday','WheatAboveGroundWt', by = "Zone",
        #    xformatter=formatter).opts(legend_position='top', xlabel='Time', fontsize = {"legend" : 10}, title='WheatAboveGroundWt')

        return p1, p2

    def s2_rasters(self):
        # Read Sentine-2 data from database and prepare plots for Panel
        col4 = self.db["Sentinel2Rasters"]
        docs = col4.find({"field": "RVIII", "time" : self.timefilter} ).sort("time", -1).limit(1)
        levels = np.linspace(0, 1, 10).tolist()
        rasters = []
        i = 0
                #There seem to be some issues with MemoryFile (occasional crashes) at least on Windows
        for doc in docs:
            with rasterio.MemoryFile(doc["raster"]) as raster:
                with raster.open() as r:
                    ds = xr.open_rasterio(r, cache=True)
                    ds["time"] = doc["time"]
                    rasters.append(ds.copy(deep=True))

                ds = ds.sortby("x").sortby("y")
                ds_lai = ds.sel(band=11)
                ds_vegetation_index = ds.sel(band=13)
                ds_moisture_index = (ds[7]-ds[10])/(ds[7]+ds[10])

        raster_plot = ds_vegetation_index.hvplot.contourf(title = "NDVI" + "  " + str(pd.to_datetime(ds_vegetation_index.time.values)),aspect='equal',cmap = 'viridis').opts(xlabel = 'Latitude', ylabel = 'Longitude', xticks = [(0,' ')], yticks = [(0,' ')],color_levels = levels)
        raster_plot2 = ds_moisture_index.hvplot.contourf(title = "Normalized moisture index" + "  " + str(pd.to_datetime(ds_moisture_index.time.values)),aspect='equal').opts(xlabel = 'Latitude', ylabel = 'Longitude', xticks = [(0,' ')], yticks = [(0,' ')],color_levels = levels)
        raster_plot3 = ds_lai.hvplot.contourf()
        return raster_plot, raster_plot2, raster_plot3

    def s2_curves(self):
        s2 = self.db.get_s2({"time" : self.timefilter})
        s2["date"] = s2.time.dt.date

        #lai_ds = hv.Dataset(s2, ["time", "zone"], ["LAI"])
        #p1 = lai_ds.to(hv.Scatter).overlay("zone").opts(legend_position="left")
        #n_ds = hv.Dataset(s2, ["time", "zone"], ["NDVI"])
        #p2 = n_ds.to(hv.Scatter).overlay("zone").opts(legend_position="left")

        p1 = hv.BoxWhisker(s2, ["date"], 'LAI').opts(xrotation=45)
        p2 = hv.BoxWhisker(s2, ["date"], 'NDVI').opts(xrotation=45)
        return p1, p2

    def html_panes(self):
        # Get local time and sunrise / sunset times
        sun = Sun(latitude, longitude)
        abd = pd.Timestamp.today()
        date = datetime.strptime(str(abd), '%Y-%m-%d %H:%M:%S.%f')
        abd_date = date.strftime("%d/%m/%Y")
        abd_time = date.strftime("%I:%M:%S")
        abd_sr = sun.get_local_sunrise_time(abd).time()
        abd_ss = sun.get_local_sunset_time(abd).time()

        # Prepare HTML-palnels
        html_pane = pn.pane.HTML("""
        <b>Our Digital Twin is based on APSIM (Agricultural Production Systems sIMulator) simulation software, standard Farm Management Information System (FMIS) farming plans, sensor data obtained through APIs and publicly available remote sensing data.</b>
        """)

        html_pane2 = pn.pane.HTML(f"""
        <b>Jokioinen, Finland (60.8042,23.4861)</b><br>
        Temperature: {last_weather} &#8451;<br>
        Date: {abd_date}<br>
        Local time: {abd_time}<br>
        Sunrise: {abd_sr}<br>
        Sunset: {abd_ss}<br><br>
        Treatment zones, Soilscout sensors (blue) and weather station (red) are shown on the map.
        """)

        return html_pane, html_pane2

    def layout(self):
        #Layout using Template
        bootstrap = pn.template.BootstrapTemplate(title='TwinYields')

        rp1, rp2, rp3 = self.s2_rasters()
        rp1.opts(width=500, height=400)
        rp2.opts(width=500, height=400)
        rp3.opts(width=500, height=400)

        rc1, rc2 = self.s2_curves()
        rc1.opts(width=500, height=400)
        rc2.opts(width=500, height=400)

        m = self.basemap()
        folium_panel = pn.pane.plot.Folium(m, height=400, width=1000)

        sp1, sp2 = self.simulation()
        sp1.opts(width=500, height=400)
        sp2.opts(width=500, height=400)

        scT, sc_moisture  = self.soilscout()
        sc_moisture.opts(width=500, height=400)

        fa = self.farmiaisti()


        print("\tSetting layout")
        p1 = pn.Column(
            pn.FlexBox(rp3, rp1, rp2, rc1, rc2, sc_moisture, flex_direction="row"),
            sizing_mode='stretch_width', max_width=1600
        )

        p2 = pn.Column(folium_panel,
                       pn.FlexBox(sp1, sp2),
                       sizing_mode='stretch_width')

        p3 = pn.FlexBox(scT, fa)

        tabs = pn.Tabs(("Field Status", p1),
                ("Simulation", p2),
                ("Sensors", p3),
                 dynamic = True)
        bootstrap.main.append(tabs)
        return bootstrap

if "bokeh_app" in __name__:
    ui = TwinUI()
    app = ui.layout()
    app.servable()
