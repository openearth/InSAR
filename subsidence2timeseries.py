import os
from netCDF4 import Dataset,num2date,date2num
from math import cos, asin, sqrt
# from shapely.geometry import Point, MultiPoint
# from shapely.ops import nearest_points
import pandas as pd
# import json
# from shapely.geometry import shape
# import numpy as np
import matplotlib.pyplot as plt
# from itertools import accumulate
from gplearn.genetic import SymbolicRegressor
from scipy.optimize import curve_fit
from scipy import interpolate
import numpy as np

def plotVerticalMotion():
    dir_input = os.path.abspath(os.path.join(os.path.dirname(__file__), 'output'))
    file_list = [i for i in os.listdir(dir_input) if i.endswith('.nc')]
    file_list = [i for i in file_list if i.startswith('Masked')] #get those netcdf files that contain the coherence and the displacement

    i = 0

    DATE = []

    fp = os.path.join(dir_input, file_list[0])
    input_nc = Dataset(fp, 'r', format='NetCDF4')
    lat = input_nc.variables['latitude']
    lon = input_nc.variables['longitude']

    df = pd.DataFrame()
    firstread = True
    for j in range(280, 281):
        print(j)
        print('********')
        for i in range(458, 459 ):
            VM = [] #empty list for vertical motion
            for f in file_list:
                fp = os.path.join(dir_input, f)
                input_nc = Dataset(fp, 'r', format='NetCDF4')

                DATE.append(f.split('_')[3][0:8])
                vh = input_nc.variables['displacement_coh'][:]
                lia = input_nc.variables['localIncidenceAngle'][:]
                VM.append(vh[j,i]*cos(lia[j,i]))
            if firstread: #if reading the all files for the first time, extract the dates
                df['datestring'] = DATE
                df['date'] = pd.to_datetime(df['datestring'], format='%Y%m%d')
                df.drop(['datestring'], axis=1, inplace=True)
                df.set_index('date', inplace=True)
                firstread = False

            df['Vertical_Motion_%i_%i' %(j,i)] = VM
    df1 = df.loc[:, df.isnull().mean() <= .10] ##remove column if more than 10 percent of the values are NaN
    if not df1.empty:
        print('DataFrame is not empty!')
        df1 = df1.cumsum() ##calculate the cumulative value
        y = df1.values
        x = np.array([i for i in range(1,len(df1)+1)])
        tck = interpolate.splrep(x, y, s=0.5)
        xnew = np.arange(1, len(df1), len(df1) / 50)
        ynew = interpolate.splev(xnew, tck, der=0)
        # plt.plot(xnew, ynew, 'b')
        # plt.plot(x,y,'g')
        # plt.savefig('a.png')


        fig, ax = plt.subplots(1, 1)
        # ax.plot(x, y, 'bo', label='Data Point')
        # ax.plot(arr, s(arr), 'k-', label='Cubic Spline', lw=1)
        # plt.legend()
        # plt.savefig('spline.png')
        idx = pd.date_range('2019-08-11', '2020-06-30',freq="H")

        df1 = df1.reindex(idx, fill_value=np.NaN)

        df1['interpolated'] = df1.interpolate()
        x = np.array([i for i in range(1, len(df1) + 1)])
        y = df1['interpolated'].values
        tck = interpolate.splrep(x, y, s=0.5)
        xnew = np.arange(1, len(df1)+1, 1)
        ynew = interpolate.splev(xnew, tck, der=0)
        print(len(df1), ynew.shape)
        df1['spline-fit'] = ynew



        plt.figure()
        df1.to_csv('Timeseries_of_LOS_Motion.csv')
        ax = df1['Vertical_Motion_280_458'].plot(marker='o')
        df1['interpolated'].plot(ax = ax)
        df1['spline-fit'].plot(ax = ax)
        plt.legend()
        plt.ylabel('cumulative vertical motion [m]')


        plt.savefig('vertical_motion_with_splines.png')
        #
        # # Training samples
        #
        # y_train = df1['interpolated'].values[0::2]
        # y_test = df1['interpolated'].values[1::2]
        # X_all = np.array([i for i in range(1,len(df1['interpolated'])+1)])
        # X_train  = X_all[0::2].reshape(-1,1)
        # X_test = X_all[1::2].reshape(-1,1)
        #
        #
        #
        # # # Testing samples
        #
        # est_gp = SymbolicRegressor(population_size=5000,
        #                    generations=20, stopping_criteria=0.0001)
        # est_gp.fit(X_train, y_train)
        # y_predict = est_gp.predict(X_test)
        # plt.figure()
        # plt.plot(y_predict)
        # plt.plot(y_test)
        # plt.savefig('gplearn.png')
        # print(est_gp._program)
        # df1['symbolicRegression'] = y_predict
        # df1.plot()
        # plt.savefig('test4.png')
        # print(est_gp._program)
        # endtime = time.time() - starttime
        # print('---%s seconds ---' % endtime)
        #
        # dot_data = est_gp._program.export_graphviz()
        # graph = graphviz.Source(dot_data)
        # graph.render('test')
    else: print('df is empty')


plotVerticalMotion()





