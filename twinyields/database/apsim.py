import pandas as pd
import os
import datetime

"""Query Farmiaisti data and write APSIM file"""
def farmiaisti_to_met(data, weatherfile, device, location):
    # radn from station is W/m^2 / 15 min
    # radn in APSIM is MJ/m^2
    # coversion: 15 min = 900s  / 1MJ = 1000000J
    # radiation in MJ/m^2 / 15min
    # rain from station is units mm/h for 15 mins -->

    data['date'] = data["time"].dt.floor("D")
    data['radiation'] = data['radiation'].apply(lambda x: x*1.0E-6*900).values
    data_mean = data.groupby(['date']).mean()
    data_max = data.groupby(['date'], as_index=False).max()
    data_min = data.groupby(['date']).min()
    data_sum = data.groupby(['date']).sum()
    df = pd.DataFrame(columns = ['year','day','radn','maxt','mint','rain','pan','vp','code'])
    df['maxt'] = data_max['temp_up'].values
    df['mint'] = data_min['temp_down'].values
    df['vp'] = data_mean['vapor pressure'].apply(lambda x: x * 10).values
    df['rain'] = data_max['rainfall(counter)'].values - data_min['rainfall(counter)'].values
    df['radn'] = data_sum['radiation'].values
    df['year'] = data_max['date'].dt.to_pydatetime()

    df['day'] = df['year'].dt.date.apply(lambda x: (x - datetime.datetime(x.year, 1, 1).date()).days + 1).values
    df['year'] = df['year'].dt.date.apply(lambda x: x.year).values
    df['pan'] = 0
    df['code'] = 0
    df = df[['year', 'day', 'radn', 'maxt', 'mint', 'rain', 'pan', 'vp', 'code']]
    df = df.fillna(0)
    df = df.round(1)
    df_to_met(weatherfile, df, device, location)

def df_to_met(weatherfile, df, device, location):
    os.makedirs(os.path.split(weatherfile)[0], exist_ok=True)

    annual_average = str(4.48)
    annual_amplitude = str(50.49)
    f = open(weatherfile, "w")
    f.write("[weather.met.weather]\n")
    f.write(f"!station number = {device}\n")
    f.write("!station name = JOKIOINEN\n")
    f.write("latitude = ")
    f.write(location[0:9])
    f.write( " (DECIMAL DEGREES)\n")
    f.write("longitude = ")
    f.write(location[10:19])
    f.write( " (DECIMAL DEGREES)\n")
    f.write("tav =  ")
    f.write(annual_average)
    f.write(" (oC) ! annual average ambient temperature\n")
    f.write("amp =  ")
    f.write(annual_amplitude)
    f.write(" (oC) ! annual amplitude in mean monthly temperature\n")
    f.write("!File created on ")
    f.write(datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
    f.write("\n")
    f.write("!\n")
    f.write("year  day radn  maxt   mint  rain  pan    vp      code\n")
    f.write(" ()   () (MJ/m^2) (oC) (oC)  (mm)  (mm)   (hPa)     ()\n")
    f.write(df.to_string(header=False, index=False))
    f.write('\n')
    f.close()




