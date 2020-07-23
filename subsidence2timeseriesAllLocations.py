import os
from netCDF4 import Dataset,num2date,date2num
from math import cos, asin, sqrt
from shapely.geometry import Point, MultiPoint
from shapely.ops import nearest_points
import pandas as pd
import json
from shapely.geometry import shape
import numpy as np
import matplotlib.pyplot as plt
from itertools import accumulate

def createTimeseries():
    dir_input = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output'))
    file_list = [i for i in os.listdir(dir_input) if i.endswith('.nc')]

    DATE = []

    fp = os.path.join(dir_input, file_list[0])
    input_nc = Dataset(fp, 'r', format='NetCDF4')
    lat = input_nc.variables['latitude']
    lon = input_nc.variables['longitude']


    df = pd.DataFrame()
    firstread = True
    for j in range(0, lat.shape[0]-1):
        for i in range(0, lat.shape[1]-1):
            VM = [] #empty list for vertical motion
            for f in file_list:
                fp = os.path.join(dir_input, f)
                input_nc = Dataset(fp, 'r', format='NetCDF4')
                DATE.append(f.split('_')[2][0:8])
                vh = input_nc.variables['displacement_coh'][:]
                VM.append(vh[j,i])
            if firstread: #if reading the all files for the first time, extract the dates
                df['datestring'] = DATE
                df['date'] = pd.to_datetime(df['datestring'], format='%Y%m%d' )
                df.drop(['datestring'], axis=1, inplace=True)
                df.set_index('date', inplace=True)
                firstread = False

            df['LOSMotion_%i_%i' %(j,i)] = VM
    df1 = df.loc[:, df.isnull().mean() <= .10] ##remove column if more than 10 percent of the values are NaN
    if not df1.empty:
        print('DataFrame is not empty!')
        df1 = df1.cumsum() ##calculate the cumulative value
        fn = os.path.join(dir_input, 'Timeseries_of_LOS_Motion.csv' )
        df1.to_csv(fn)
    else:
        print('df is empty')


createTimeseries()




