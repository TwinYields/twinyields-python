import pandas as pd
import os
import datetime

"""Query Farmiaisti data and write APSIM file"""
def farmiaisti_to_met(data):
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
    #df = pd.DataFrame(columns = ['year','day','radn','maxt','mint','rain','pan' "rh",'vp','code'])
    df = pd.DataFrame()
    df['maxt'] = data_max['temp_up'].values
    df['mint'] = data_min['temp_down'].values
    #df['vp'] = data_mean['vapor pressure'].apply(lambda x: x * 10).values
    df['rain'] = data_max['rainfall(counter)'].values - data_min['rainfall(counter)'].values
    df['radn'] = data_sum['radiation'].values
    df['rh'] = data_mean["humidity"].values
    df["windspeed"] = data_mean["wind speed"].values
    df['year'] = data_max['date'].dt.to_pydatetime()

    df['day'] = df['year'].dt.date.apply(lambda x: (x - datetime.datetime(x.year, 1, 1).date()).days + 1).values
    df['year'] = df['year'].dt.date.apply(lambda x: x.year).values

    #df['pan'] = 0
    #df['code'] = 0
    #df = df[['year', 'day', 'radn', 'maxt', 'mint', 'rain', 'pan', 'vp', 'code']]
    df = df[['year', 'day', 'radn', 'maxt', 'mint', 'rain', "rh", "windspeed"]]
    df = df.fillna(0)
    df = df.round(1)
    return df


def df_to_met(weatherfile, df, device, latitude, longitude):
    os.makedirs(os.path.split(weatherfile)[0], exist_ok=True)

    annual_average = 4.48
    annual_amplitude = 24.5 #TODO calculate from historical data
    created = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    header = f"""
[weather.met.weather]
!station number = {device}
!station name = JOKIOINEN
latitude = {latitude} (DECIMAL DEGREES)
longitude = {longitude} (DECIMAL DEGREES)
tav = {annual_average} (oC) ! annual average ambient temperature
amp = {annual_amplitude} (oC) ! annual amplitude in mean monthly temperature
!File created on {created}
!
year day radn maxt mint rain rh wind_speed
 ()   () (MJ/m^2) (oC) (oC) (mm) (%) (m/s)
"""
    f = open(weatherfile, "w")
    f.write(header.lstrip())
    f.write(df.to_string(header=False, index=False) + "\n")
    f.close()





















