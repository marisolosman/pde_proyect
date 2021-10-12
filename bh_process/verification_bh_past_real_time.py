""" this code takes bh forecast from 2011-2020 period and verify it against obs
 metrics: - BIAS
          - RMSE
          - Talgrand diagram
total, filter by month, filter by IC SM, filtered by MJO, filtered by SIS phase
"""
import numpy as np
import pandas as pd
import datetime as dt
import xarray as xr
import matplotlib.pyplot as plt

# DATOS INPUT
estacion = 'resistencia'

FILE = '/datos/osman/datos_pde_project/' + estacion + '_2011_2020_bh_forecasts.nc'


ds = xr.open_dataset(FILE)

#all dates
# BIAS

bias_calibrated = ds.alm_observed - ds.alm_calibrated.mean(dim='ensemble', skipna=True)
bias_calibrated = bias_calibrated[1:].mean(dim='start_date', skipna=True)

bias_uncalibrated = ds.alm_observed - ds.alm_uncalibrated.mean(dim='ensemble', skipna=True)
bias_uncalibrated = bias_uncalibrated[1:].mean(dim='start_date', skipna=True)

# NRMSE

sd_observed = np.power(ds.alm_observed - ds.alm_observed.mean(dim='start_date', skipna=True), 2)
sd_observed = np.sqrt(sd_observed.mean(dim='start_date', skipna=True))

rmse_calibrated = np.power(ds.alm_observed - ds.alm_calibrated.mean(dim='ensemble', skipna=True), 2)
rmse_calibrated = np.sqrt(rmse_calibrated.mean(dim='start_date', skipna=True))
nrmse_calibrated = 1 - np.divide(rmse_calibrated, sd_observed)

rmse_uncalibrated = np.power(ds.alm_observed - ds.alm_uncalibrated.mean(dim='ensemble',
                                                                        skipna=True), 2)
rmse_uncalibrated = np.sqrt(rmse_uncalibrated.mean(dim='start_date', skipna=True))
nrmse_uncalibrated = 1 - np.divide(rmse_uncalibrated, sd_observed)



# month when forecast is initialized
bias_calibrated_month = ds.alm_observed - ds.alm_calibrated.mean(dim='ensemble', skipna=True)
bias_calibrated_month = bias_calibrated_month.groupby('start_date.month').mean(dim='start_date', skipna=True)

bias_uncalibrated_month = ds.alm_observed - ds.alm_uncalibrated.mean(dim='ensemble', skipna=True)
bias_uncalibrated_month = bias_uncalibrated_month.groupby('start_date.month').mean(dim='start_date', skipna=True)

sd_observed = ds.alm_observed.groupby('start_date.month').std(dim='start_date', skipna=True)

rmse_calibrated_month = np.power(ds.alm_observed - ds.alm_calibrated.mean(dim='ensemble', skipna=True), 2)
rmse_calibrated_month = np.sqrt(rmse_calibrated_month.groupby('start_date.month').mean(dim='start_date', skipna=True))
nrmse_calibrated_month = 1 - np.divide(rmse_calibrated_month, sd_observed)

rmse_uncalibrated_month = np.power(ds.alm_observed - ds.alm_uncalibrated.mean(dim='ensemble', skipna=True), 2)
rmse_uncalibrated_month = np.sqrt(rmse_uncalibrated_month.groupby('start_date.month').mean(dim='start_date', skipna=True))
nrmse_uncalibrated_month = 1 - np.divide(rmse_uncalibrated_month, sd_observed)


