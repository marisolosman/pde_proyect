import sys
sys.path.append('/home/osman/proyectos/pde_proyect/lib/')
from class_operativa import class_operativa
from class_bhora import class_bhora
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import xarray as xr
import os
import multiprocessing as mp
from pathos.multiprocessing import ProcessingPool as Pool

CORES = mp.cpu_count()

# Datos INPUT
tipo_bh = 'profundo'

df = pd.read_csv('../datos/estaciones.txt', sep=';')

def CreateNetcdf(i):
    #for i in rows[0:2]:
    if i['cultivo'][0] == 'S' and i['nom_est'] != "gral_pico":
        estacion = i['nom_est']
        cultivo = i['cultivo']
        start_times = []
        valid_times = []
        var_calibrated = []
        var_uncalibrated = []
        alm_observed = []
        print(estacion, cultivo)
        for j in range(2011, 2022):
                fech = dt.datetime(j, 12, 1)
                while (fech <= dt.datetime(j + 1, 5, 1)):
                    if (fech.weekday()==0) | (fech.weekday()==3):
                        print(fech.strftime('%Y-%m-%d'))
                        try:
                            if fech < dt.datetime(2021, 2, 24):
                                a = class_operativa(estacion, fech.strftime('%Y%m%d'), True, 'EG')
                                d = class_operativa(estacion, fech.strftime('%Y%m%d'), False)
                            else:
                                fecha = fech - dt.timedelta(hours=24)
                                a = class_operativa(estacion, fecha.strftime('%Y%m%d'), True, 'EG')
                                d = class_operativa(estacion, fecha.strftime('%Y%m%d'), False)
                            if cultivo[0] == 'S' and fech.month <= 7:
                                ini_camp = fech.year - 1
                            else:
                                ini_camp = fech.year

                            for i in range(0, 16, 4):
                                a.radsup[0, i: i + 4] = a.radsup[0, i]
                                d.radsup[0, i: i + 4 ] = d.radsup[0, i]
                                a.etp[0, i: i + 4] = a.etp[0, i]
                                d.etp[0, i: i + 4 ] = d.etp[0, i]
                            start_times.append(fech)
                            var_calibrated.append(a)
                            var_uncalibrated.append(d)
                        except:
                            print('missing date: ', fech.strftime('%Y-%m-%d'))
                    fech += dt.timedelta(hours=24)
#
        try:
            pp = np.array([i.precip for i in var_calibrated])
            tmax = np.array([i.tmax for i in var_calibrated])
            tmin = np.array([i.tmin for i in var_calibrated])
            velviento = np.array([i.velviento for i in var_calibrated])
            hrmean = np.array([i.hrmean for i in var_calibrated])
            pp_uncalibrated = np.array([i.precip for i in var_uncalibrated])
            tmax_uncalibrated = np.array([i.tmax for i in var_uncalibrated])
            tmin_uncalibrated = np.array([i.tmin for i in var_uncalibrated])
            velviento_uncalibrated = np.array([i.velviento for i in var_uncalibrated])
            hrmean_uncalibrated = np.array([i.hrmean for i in var_uncalibrated])

            start_times = np.array(start_times)
            print(pp.shape, start_times)
            ds = xr.Dataset({'pp_calibrated': (('start_date', 'step', 'ensemble'), pp),
                            'tmax_calibrated': (('start_date', 'step', 'ensemble'), tmax),
                             'tmin_calibrated': (('start_date', 'step', 'ensemble'), tmin),
                            'hrmean_calibrated': (('start_date', 'step', 'ensemble'), hrmean),
                             'velviento_calibrated': (('start_date', 'step', 'ensemble'), velviento),
                            'pp_uncalibrated': (('start_date', 'step', 'ensemble'), pp_uncalibrated),
                            'tmax_uncalibrated': (('start_date', 'step', 'ensemble'), tmax_uncalibrated),
                             'tmin_uncalibrated': (('start_date', 'step', 'ensemble'), tmin_uncalibrated),
                            'hrmean_uncalibrated': (('start_date', 'step', 'ensemble'), hrmean_uncalibrated),
                             'velviento_uncalibrated': (('start_date', 'step', 'ensemble'), velviento_uncalibrated),
                                },
                                coords={
                                    'start_date': start_times,
                                    'step':np.arange(0, 30, 1),
                                    'ensemble': np.arange(1, 17)})
            carpeta_output = '/home/osman/proyectos/pde_proyect/pde_salidas/forecast_bh/'
            os.system("mkdir -p " + carpeta_output)

            ds.to_netcdf(carpeta_output + estacion + '_variables_' + \
                             '2011_2022_forecasts.nc')
            print('fin - ' + estacion)

        except:
            print('error - ' + estacion)

pool = mp.Pool(CORES)

rows = [row for index, row in df.loc[0: 22].iterrows()]

rows = [i for i in rows if i['cultivo'][0] == 'S']

results = [pool.map(CreateNetcdf, rows)]
pool.close()

