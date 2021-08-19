#!/usr/bin/env python
# coding: utf-8
from dask.distributed import Client
import xarray as xr
import os
import numpy as np
import dask
import glob
import pandas as pd
import datetime as dt
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'

# In[194]:

latitude = [-20, -60]
longitude = [360 - 80, 360 - 20]

def seleccionar_dominio(ds, lat=latitude, lon=longitude):
    ds = ds.sel(latitude=slice(lat[0], lat[1]), longitude=slice(lon[0], lon[1]), method='nearest')
    ds = ds.isel(step=range(32 * 4))
    ds['step'] = ds.step.values - np.timedelta64(3, 'h')
    nvars = list(ds.data_vars.keys())
    if len(nvars >= 2):
        ds = np.sqrt(np.power(ds[nvars[0]], 2) + np.power(ds[nvars[1]], 2)) 
        ds = ds.resample(step='1D').mean()
        ds['step'] = ds['step'].dt.floor('D')
        ds = ds.rename('velviento')
        return ds
    else:
        pass
def modify(ds, lat=latitude, lon=longitude):
    try:
        ds = ds.sel(latitude=slice(lat[0], lat[1]), longitude=slice(lon[0], lon[1]), method='nearest')
        ds = ds.isel(step=range(32 * 4))
        ds['step'] = ds.step.values - np.timedelta64(3, 'h')
        nvars = list(ds.data_vars.keys())
        if len(nvars)>=2:
            ds = np.sqrt(np.power(ds[nvars[0]], 2) + np.power(ds[nvars[1]], 2)) 
            ds = ds.resample(step='1D').mean()
            ds['step'] = ds['step'].dt.floor('D')
            ds = ds.rename('velviento')
            return ds
        else:
            pass
    except:
        pass
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

var_name = 'velviento'
variable = 'wnd10m'
PATH = '/datos2/CFSReana/'
for i in np.arange(1999, 2011):
    for j in range(1, 13):
        if not(os.path.isfile(var_name + '_' + str(i) + '_' + '{:02d}'.format(j) + '_arg.nc')):
            try: 
                ds = xr.open_mfdataset(PATH + variable + '/' + str(i) + '/' + variable + '_f.01.' + str(i) + '{:02d}'.format(j) + '*.grb2',
                                       engine='cfgrib', combine='nested', concat_dim='time', parallel=True,
                                       data_vars='minimal', coords='minimal', compat='override',
                                       preprocess=seleccionar_dominio)
                ds = ds.chunk({'time':len(ds.time), 'step':len(ds.step)})
                ds = ds.load()
                ds.to_netcdf(var_name + '_' + str(i) + '_' + '{:02d}'.format(j) + '.nc')
            except:
                # this is basically what open_mfdataset does
                open_kwargs = dict(decode_cf=True, engine='cfgrib')
                file_names = sorted(glob.glob(PATH + variable + '/' + str(i) + '/' + variable + '_f.01.' + str(i) + '{:02d}'.format(j) + '*.grb2'))
                open_tasks = [dask.delayed(xr.open_dataset)(f, **open_kwargs) for f in file_names]
                tasks = [dask.delayed(modify)(task) for task in open_tasks]
                datasets = dask.compute(tasks)  # get a list of xarray.Datasets
                datasets = [f for f in datasets[0] if f is not None]
                combined = xr.combine_nested(datasets, concat_dim='time', compat='no_conflicts',
                                            coords='minimal')
                combined.to_netcdf(var_name + '_' + str(i) + '_' + '{:02d}'.format(j) + '_arg.nc')

ds = xr.open_mfdataset(var_name + '*_arg.nc', combine='nested', concat_dim='time', parallel=True, data_vars='minimal', coords='minimal', compat='override')
ds = ds.isel(step=range(31))
ds = ds.chunk({'time':int(len(ds.time)/2), 'step':len(ds.step)})
ds = ds.load()
ds.to_netcdf('velviento_1999-2010_arg.nc')
#ds = ds.isel(time= np.unique(ds.time, return_index=True)[1])
#tiempos = np.arange(np.datetime64('1999-01-01').astype('datetime64[ns]'), np.datetime64('2011-01-01').astype('datetime64[ns]'), np.timedelta64(6, 'h')).astype('datetime64[ns]')
#ds = ds.reindex(time=tiempos)
#ds = ds.velviento.to_numpy()
#ds = np.reshape(ds.velviento.values, [int(len(tiempos)/4), 4, 31])
#ds[:, 3, 0] = np.nan
#tiempos = np.arange(np.datetime64('1999-01-01').astype('datetime64[ns]'), np.datetime64('2011-01-01').astype('datetime64[ns]'), np.timedelta64(1, 'D')).astype('datetime64[ns]')
#for i in range(31):
#    df = create_summary_file(var_name, tiempos, ds[:, :, i], i)
#    sel_col = list(df)[1::]
#    df[sel_col] = df[sel_col].apply(pd.to_numeric, errors='ignore')
#    n_file = 'data_final_' + var_name + '_' + "{:02d}".format(i) + '.txt' 
#    df.to_csv(n_file, sep=';', float_format='%.2f', decimal=',',
#                        date_format='%Y-%m-%d')


