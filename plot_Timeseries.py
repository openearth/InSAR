import pandas as pd
import matplotlib.pyplot as plt
import os
from netCDF4 import Dataset,num2date,date2num
import numpy as np
#
# dir_input = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output'))
# file_list = [i for i in os.listdir(dir_input) if i.endswith('.nc')]
# file_list = [i for i in file_list if i.startswith('coh')]
#
# df = pd.DataFrame()
# fp = os.path.join(dir_input, file_list[0])
# input_nc = Dataset(fp, 'r', format='NetCDF4')
# lat = input_nc.variables['latitude']
# lon = input_nc.variables['longitude']
#
#
# #
# # df = pd.read_csv('TimeSeries.csv')
# # df['date'] = pd.to_datetime(df['Unnamed: 0'], format='%Y-%m-%d' )
# # df.drop(['Unnamed: 0'], axis=1, inplace=True)
# # df.drop(['Date'], axis=1, inplace=True)
# # df.set_index('date', inplace=True)
# # df = df.loc['2017-05-08':'2019-01-10']
# # # df = df[df.columns[0:30]]
# # print(df.shape, 'old')
# # df.plot()
# #
# # plt.savefig('timeseries_orig.png')
# # plt.close()
#

df = pd.read_csv('locations.csv')
print(df.shape)
"""for shoulder:"""
df = df[df['lons'] <= -44.121]
df = df[df['lons'] >= -44.122]
df = df[df['lats'] <= -20.1169]
df = df[df['lats'] >= -20.1185]
shoulder_locs_j = np.array(df['j'])
shoulder_locs_i = np.array(df['i'])


#
# """for center:"""
# df = df[df['lons'] <= -44.120]
# df = df[df['lons'] >= -44.122]
# df = df[df['lats'] <= -20.119]
# df = df[df['lats'] >= -20.120]
# center_locs_j = np.array(df['j'])
# center_locs_i = np.array(df['i'])







df = pd.read_csv('Timeseries_of_LOS_Motion.csv')

print(df.shape, 'new')
df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d' )
df.set_index('date', inplace=True)
# df = df.dropna(axis=1, how='any')
# df = df[df.columns[0:30]]
# df = df[df.columns[0::2]]
for cn in list(df):
    print(cn)
    j = int(cn.split('_')[1])
    i = int(cn.split('_')[2])

    if j in shoulder_locs_j:
        if i in shoulder_locs_i:
            print(j,i)
            df[cn].plot()
            plt.ylim(-0.6,0.05)
            plt.title('shoulder points')
            plt.savefig('shoulder.png')
        #     print('*******************************')
            # plt.close()
#
# plt.savefig('timeseries_new.png')
# locations = list(df)
# location_j = [int(l.split('_')[1]) for l in locations]
# location_i = [int(l.split('_')[2]) for l in locations]
#
# locations = list(zip(location_j, location_i))
# df = pd.DataFrame()
# LON = []
# LAT = []
# JJ = []
# II = []
# for v in locations:
#     JJ.append(v[0])
#     II.append(v[1])
#     LON.append(lon[v[0], v[1]])
#     LAT.append(lat[v[0], v[1]])
#
# df['j'] = JJ
# df['i'] = II
# df['lons'] = LON
# df['lats'] = LAT
#
#
# df.to_csv('locations.csv')





