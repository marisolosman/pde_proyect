#!/usr/bin/env python
# coding: utf-8

# In[1]:


"""This code takes Reforecast CFS for all variables participating in the hydric balance and select domain over argentina and step 1-32.
Computes: HR with T2m, pressfc and Q2m. Wind speed from wind10m. accumulated daily precip. Daily net incoming radiation from dswsfc. """


# In[2]:


get_ipython().run_line_magic('matplotlib', 'inline')
import os
import glob
import datetime as dt
import dask
from dask.distributed import Client
import numpy as np
import pandas as pd
import xarray as xr
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'


# In[3]:


latitude = [-20, -60]
longitude = [360 - 80, 360 - 50]
def my_fun(a):
    return a.integrate('step', '6h')

def seleccionar_dominio_radsup(ds, lat=latitude, lon=longitude):
    try:
        ds = ds.sel(latitude=slice(lat[0], lat[1]), longitude=slice(lon[0], lon[1]))
        ds = ds.isel(step=range(32 * 4))
        ds['step'] = ds.valid_time.values - np.timedelta64(3, 'h')
        ds = ds.groupby("step.dayofyear").map(my_fun)
        ds = ds * 6 * 60 * 60 * 1e-6  #Mj/m2
        ds = ds.rename({'dayofyear': 'step'})
        ds['step'] = np.arange(len(ds['step'])).astype('timedelta64[D]')
        return ds       
    except:
        pass
def seleccionar_dominio_temps(ds, lat=latitude, lon=longitude):
    try:
        ds = ds.sel(latitude=slice(lat[0], lat[1]), longitude=slice(lon[0], lon[1]))
        ds = ds.isel(step=range(32 * 4))
        ds['step'] = ds.step.values - np.timedelta64(3, 'h')
        ds = ds.resample(step='D').mean()
        ds = ds.isel(step=range(31))
        return ds       
    except:
        pass
def seleccionar_dominio_tmax(ds, lat=latitude, lon=longitude):
    try:
        ds = ds.sel(latitude=slice(lat[0], lat[1]), longitude=slice(lon[0], lon[1]))
        ds = ds.isel(step=range(32 * 4))
        ds['step'] = ds.step.values - np.timedelta64(3, 'h')
        ds = ds.resample(step='D').max()
        ds = ds.isel(step=range(31))
        return ds       
    except:
        pass
def seleccionar_dominio_tmin(ds, lat=latitude, lon=longitude):
    try:
        ds = ds.sel(latitude=slice(lat[0], lat[1]), longitude=slice(lon[0], lon[1]))
        ds = ds.isel(step=range(32 * 4))
        ds['step'] = ds.step.values - np.timedelta64(3, 'h')
        ds = ds.resample(step='D').min()
        ds = ds.isel(step=range(31))
        return ds       
    except:
        pass

def seleccionar_dominio_precip(ds, lat=latitude, lon=longitude):
    try:
        ds = ds.sel(latitude=slice(lat[0], lat[1]), longitude=slice(lon[0], lon[1]))
        ds = ds.isel(step=range(32 * 4))
        ds['step'] = ds.step.values - np.timedelta64(3, 'h')
        ds = ds.resample(step='24H', closed='left', base=9).sum(skipna=True)
        ds = 6.*60.*60. * ds
        ds['step'] = np.arange(len(ds['step'])).astype('timedelta64[D]')
        ds = ds.isel(step=range(31))
        return ds
    except:
        pass
def seleccionar_dominio(ds, lat=latitude, lon=longitude):
    try:
        ds = ds.sel(latitude=slice(lat[0], lat[1]), longitude=slice(lon[0], lon[1]))
        ds = ds.isel(step=range(32 * 4))
        ds['step'] = ds.step.values - np.timedelta64(3, 'h')
        return ds
    except:
        pass
def seleccionar_dominio_viento(ds, lat=latitude, lon=longitude):
    try:
        nvars = list(ds.data_vars.keys())
        if len(nvars)>=2:
            ds = ds.sel(latitude=slice(lat[0], lat[1]), longitude=slice(lon[0], lon[1]))
            ds = ds.isel(step=range(32 * 4))
            ds['step'] = ds.step.values - np.timedelta64(3, 'h')
            ds = np.sqrt(np.power(ds[nvars[0]], 2) + np.power(ds[nvars[1]], 2)) 
            ds = ds.resample(step='1D').mean()
            ds['step'] = ds['step'].dt.floor('D')
            ds = ds.rename('velviento')
            return ds
        else:
            pass
    except:
        pass

def check_var(ds):
    try:
        if ds.values.shape[0]>0:
            return True
    except:
        return False
def check_wind(ds):
    try:
        nvars = list(ds.data_vars.keys())
        if len(nvars >= 2):
            return True
        else:
            return False
    except:
        return False
def calcular_hr(psf, q2f, t2f):
    '''
    Calculate Relative Humidity (HR), using the three
    pandas Series obtained from get_data_from_grib function
    Also change the values of Index from hours of initial date
    to easy-use of resample pandas function.
    '''
    # Formula to calculate HR
    T0 = 273.16
    av0 = np.divide(t2f - T0, t2f - 29.65)
    av1 = np.exp(17.63 * av0)
    av2 = np.power(av1, -1)
    hrs = 0.263 * psf * q2f * av2
    return hrs


# In[4]:


client = Client()
client


# In[9]:


PATH = '/pikachu/datos2/CFSReana/'
variables = {
    "tmax" : {
    "name" : "tmax",
    "atributos" : 'Maximum temperature',
    "file": "tmax"
  },  
    "tmin" : {
    "name" : "tmin",
    "atributos" : 'Minimum temperature',
    "file": "tmin"
  },
    "prate" : {
    "name": 'prate',
    "atributos" :'Precipitation rate',
    "file": "precip"
  }, 
    "dswsfc" : {
    "name" : "dswrf",
    "atributos" : 'Downward short-wave radiation flux',
    "file": "radsup"
  },
    "tmp2m" : {
    "name" : "t2m",
    "atributos" : '2 metre temperature',
    "file": "hrmean"
  },
    "q2m" : {
    "name" : "q",
    "atributos" : 'Specific humidity',
    "file": "hrmean",
  },
    "pressfc" : {
    "name" : "sp",
    "atributos" : 'Surface pressure',
    "file": "hrmean"
  },
    "wnd10m" : {
    "name": 'u10',
    "atributos" :'10 metre zonal wind',
    "file": "velviento"
    }
}
tiempos = np.arange(np.datetime64('1999-01-01').astype('datetime64[ns]'), np.datetime64('2011-01-01').astype('datetime64[ns]'),
                                np.timedelta64(6, 'h')).astype('datetime64[ns]')


# In[10]:


for idx, k in enumerate(variables.keys()):
    if not(os.path.isfile("datafinal_" + variables[k]['name'] + '_1999-2010_arg.nc')):
        if k != "wnd10m":
            open_kwargs = dict(decode_cf=True, engine='cfgrib', backend_kwargs={'filter_by_keys':{'name':variables[k]['atributos']}})
        else:
            open_kwargs = dict(decode_cf=True, engine='cfgrib')
        for i in np.arange(1999, 2011):
            for j in range(1, 13):
                if not(os.path.isfile(k + '_' + str(i) + '_' + '{:02d}'.format(j) + '_arg.nc')):
                    file_names = sorted(glob.glob(PATH + k + '/' + str(i) + '/' + k + '_f.01.' + str(i) + '{:02d}'.format(j) + '*.grb2'))
                    open_tasks = [dask.delayed(xr.open_dataset)(f, **open_kwargs) for f in file_names]
                    if k == 'prate':
                        tasks = [dask.delayed(seleccionar_dominio_precip)(task) for task in open_tasks]
                        concat = True
                    elif k == 'dswsfc':
                        tasks = [dask.delayed(seleccionar_dominio_radsup)(task) for task in open_tasks]
                        concat = True
                    elif k == 'wnd10m':
                        tasks = [dask.delayed(seleccionar_dominio_viento)(task) for task in open_tasks]
                        concat = True
                    elif np.logical_or(k == 'q2m', np.logical_or(k == 'tmp2m', k == 'pressfc')):
                        tasks = [dask.delayed(seleccionar_dominio)(task) for task in open_tasks]
                        concat = False
                    elif k == 'tmax':
                        tasks = [dask.delayed(seleccionar_dominio_tmax)(task) for task in open_tasks]
                        concat = True
                    elif k == 'tmin':
                        tasks = [dask.delayed(seleccionar_dominio_tmin)(task) for task in open_tasks]
                        concat = True
                    datasets = dask.compute(tasks)  # get a list of xarray.Datasets
                    bien = [v for v in datasets[0] if v]
                    if k != "wnd10m":
                        bien = [v for v in bien if check_var(v[variables[k]['name']])]
                    else:
                        bien = [v for v in bien if check_wind(v)]
                    combined = xr.combine_nested([f for f in bien if f ], concat_dim='time', data_vars="minimal", coords="minimal", combine_attrs='drop',
                                                 compat="override")
                    combined.to_netcdf(k + '_' + str(i) + '_' + '{:02d}'.format(j) + '_arg.nc')
                    bien = []
                    combined = []
                    datasets = []
        if concat:
            files = glob.glob(k + '_*_arg.nc')
            for f in files:
                if os.path.getsize(f) < 2 * 1024:   #set file size in kb
                    os.remove(fullpath)
            ds = xr.open_mfdataset(k + '_*.nc', combine='nested', concat_dim='time', parallel=True)
            ds = ds.chunk(chunks={'step':int(len(ds.step)), 'time':int(len(ds.time)/10)})
            ds = ds.isel(step=range(31))
            ds = ds.reindex(time=tiempos)
            ds.to_netcdf('data_final_' + variables[k]['name'] + '_1999-2010_arg.nc')
            ds = []
       


# In[26]:


# hrmean
for j in range(1999, 2011):
    timess = np.arange(np.datetime64(str(j) + '-01-01').astype('datetime64[ns]'), np.datetime64(str(j + 1) + '-01-01').astype('datetime64[ns]'),
                       np.timedelta64(6, 'h')).astype('datetime64[ns]')
    temp = xr.open_mfdataset('tmp2m_' + str(j) + '_*_arg.nc', combine='nested', concat_dim='time', parallel=True)
    q = xr.open_mfdataset('q2m_' + str(j) + '_*_arg.nc', combine='nested', concat_dim='time', parallel=True)
    press = xr.open_mfdataset('pressfc_' + str(j) + '_*_arg.nc', combine='nested', concat_dim='time', parallel=True)
    temp = temp.reindex(time=timess)
    q = q.reindex(time=timess)
    q = q.isel(step=range(128))
    press = press.reindex(time=timess)
    press = press.isel(step=range(128))
    hr = calcular_hr(press.sp, q.q, temp.t2m)
    hr['step'] = hr.step.values - np.timedelta64(3, 'h')
    hr = hr.chunk({'time': int(len(hr.time)/10), 'step':128})
    ds = hr.resample(step='D').mean()
    ds = ds.isel(step=range(31))
    ds.to_netcdf('hrmean_' + str(j) +'.nc')
ds = xr.open_mfdataset('hrmean_*.nc', combine='nested', concat_dim='time', parallel=True)
ds = ds.isel(time= np.unique(ds.time, return_index=True)[1])
ds = ds.reindex(time=tiempos)
ds = ds.rename({'_xarray_dataarray_variable_': 'hrmean'})
ds = ds.chunk(chunks={'step':int(len(ds.step)), 'time':int(len(ds.time)/10)})
ds.to_netcdf('data_final_hrmean_1999-2010_arg.nc')


# In[ ]:




