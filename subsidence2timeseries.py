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

def plotVerticalMotion(orig):
    dir_input = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output'))
    file_list = [i for i in os.listdir(dir_input) if i.endswith('.nc')]
    vertical_motion = [0]
    i = 0
    df = pd.DataFrame()
    DATE = []
    for f in file_list:
        DATE.append(f.split('_')[2][0:8])


        fp = os.path.join(dir_input, f)
        input_nc = Dataset(fp, 'r', format='NetCDF4')
        lat = input_nc.variables['lat'][:]
        lon = input_nc.variables['lon'][:]
        vh = input_nc.variables['displacement_VV'][:]
        LIA = input_nc.variables['localIncidenceAngle'][:]

        # vh = vh*np.cos(np.deg2rad(LIA))

        destination_list = zip(lon, lat)
        destinations = MultiPoint([Point(p) for p in destination_list])
        nearest_geoms = nearest_points(orig, destinations)
        x, y = np.meshgrid(lon, lat)
        coord_array = np.dstack((x,y))
        pt = np.array(nearest_geoms[1])
        idx = np.where((coord_array[:,:,0] == pt[0]) & (coord_array[:,:,1]==pt[1]))
        vertical_motion.append(vh[idx][0]+vertical_motion[i])
        i += 1
    df['datestring'] = DATE
    df['date'] = pd.to_datetime(df['datestring'], format='%Y%m%d' )

    df['verticalMotion'] = vertical_motion[1::]
    df.drop(['datestring'], axis=1, inplace=True)
    df.set_index('date', inplace=True)
    df.plot( color='green', marker='o')
    plt.title('coordinates: (-44.1201639, -20.1196056)')
    fp = os.path.join(dir_input,'LOSMotion.png')
    plt.savefig(fp)
    plt.close()



orig_pt = Point(-44.1201639, -20.1196056)
# orig_pt = Point(4.35, 51.9)

plotVerticalMotion(orig_pt)
