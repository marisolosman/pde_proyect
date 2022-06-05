#!/usr/bin/env python
""" takes info about station (name, lat, lon) and create reforecast data to use to calibrate
forecast
M Osman and Felix Carrasco 2021
"""
# coding: utf-8
from dask.distributed import Client
import xarray as xr
import os
import sys
import time
import numpy as np
import dask
import pandas as pd
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'

# In[194]:

def create_summary_file(var, fval, fmat, leadtime):
    """
    Function to create a summary file to save the results
    """
    columnas = ['fecha']
    columnas.extend([var + '_' + hr for hr in ['00', '06', '12', '18']])
    df = pd.DataFrame(columns=columnas)
    df['fecha'] = [i + np.timedelta64(leadtime, 'D') for i in fval]
    df[columnas[1::]] = fmat
    return df
# In[195]:
# =======================================================================
start_time = time.time()
file_name = ['velviento', 'tmin', 'tmax', 'hrmean', 'radsup', 'precip']
var_name = ['velviento', 'tmin', 'tmax', 'hrmean', 'dswrf', 'prate']

#n_est    = sys.argv[1]  # Segundo argumento variable
#lat_e  = [np.float(sys.argv[2])]
#lon_e = [np.float(sys.argv[3])]

# Lat-Lon Resistencia: -27.45/-59.05 (SMN)
# Lat-Lon Junin: -34.55/-60.92 (SMN)
#lat_e = [-34.55, -27.45, -31.3, -33.11667, -35.966667, -33.666667,
#         -31.783333, -29.9, -29.8833]
lat_e = [-37.2333, -38.333333]
lon_e = [-59.25, -60.25]
n_est = ['tandil', 'tres_arroyos']
#lon_e = [-60.92,  -59.05, -58.016667, -64.233333, -62.73333, -61.966667,
#         -60.483333, -63.683333, -61.95]
#n_est = ['junin', 'resistencia', 'concordia', 'rio_cuarto',
#         'trenque_lauquen', 'venado_tuerto', 'parana', 'vmrs', 'ceres']
folder = '/datos/osman/datos_pde_project/'

# Abrimos una carpeta y guardamos los archivos ahi
for ii in range(len(n_est)):
    # Diccionario con datos generales
    dic = {'dfolder':folder, 'lat_e':lat_e[ii], 'lon_e':lon_e[ii],
           'n_est':n_est[ii]}
    cpta_salida = '../datos/datos_hist/modelo/' + dic['n_est'] + '/' 
    os.makedirs(cpta_salida, exist_ok=True)
    dic['ofolder'] = cpta_salida

    tiempos = np.arange(np.datetime64('1999-01-01').astype('datetime64[ns]'),
                        np.datetime64('2011-01-01').astype('datetime64[ns]'), 
                        np.timedelta64(1, 'D')).astype('datetime64[ns]')
    for idx, v  in enumerate(file_name):
        ds = xr.open_dataset(dic['dfolder'] + 'data_final_' + v + '_1999-2010_arg.nc',
                             chunks={'time':1000, 'step':31})
        ds = ds.sel(latitude=dic['lat_e'], longitude=360 + dic['lon_e'], method='nearest')
        ds = ds.transpose("time", "step")
        ds = np.reshape(ds[var_name[idx]].values, [int(len(ds.time.values)/4), 4, 31])
        ds[:, 2::, 0] = np.nan
        for i in range(31):
            df = create_summary_file(v, tiempos, ds[:, :, i], i)
            sel_col = list(df)[1::]
            df[sel_col] = df[sel_col].apply(pd.to_numeric, errors='ignore')
            n_file = dic['ofolder'] + 'data_final_' + v + '_' + "{:02d}".format(i) + '.txt'
            df.to_csv(n_file, sep=';', float_format='%.2f', decimal=',',
                      date_format='%Y-%m-%d')

print("--- %s seconds ---" % (time.time() - start_time))
