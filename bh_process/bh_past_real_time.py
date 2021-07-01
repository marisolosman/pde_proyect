import sys
sys.path.append('/home/osman/proyectos/pde_proyect/lib/')
from class_operativa import class_operativa
from class_bhora import class_bhora
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import xarray as xr
# Datos INPUT
# carpeta = '/home/osman/proyectos/pde_proyect/datos/datos_op/resistencia/20081203/'
estacion = 'resistencia'
tipo_bh = 'profundo'
cultivo = 'S1-VII'
carpeta_output = '/home/osman/proyectos/pde_proyect/pde_salidas/' + estacion + '/forecast_bh/'

start_times = []
valid_times = []
alm_calibrated = []
alm_uncalibrated = []
alm_observed = []
for j in range(2011, 2012):
        fech = dt.datetime(j, 12, 1)
        while (fech <= dt.datetime(j, 12, 7)):
            if (fech.weekday()==0) | (fech.weekday()==3):
                a = class_operativa(estacion, fech.strftime('%Y%m%d'), True, 'GG')
#               b = class_operativa(estacion, fecha, True, 'EG')
#               c = class_operativa(estacion, fecha, True, 'Multi-Shift')
                d = class_operativa(estacion, fech.strftime('%Y%m%d'), False)
                for i in range(0, 16, 4):
                    a.radsup[0, i: i + 4] = a.radsup[0, i]
                    d.radsup[0, i: i + 4 ] = d.radsup[0, i]
                    a.etp[0, i: i + 4] = a.etp[0, i]
                    d.etp[0, i: i + 4 ] = d.etp[0, i]
                aa = class_bhora(a, cultivo, tipo_bh)
                dd = class_bhora(d, cultivo, tipo_bh)
                start_times.append(fech)
                valid_times.append(aa.dtimes)
                alm_calibrated.append(aa.ALMR)
                alm_uncalibrated.append(dd.ALMR)
                period = [i for i, e in enumerate(aa.fecha_obs) if e in set(aa.dtimes)]
                alm_observed.append(aa.almr_obs[period])
            fech += dt.timedelta(hours=24)

alm_calibrated = np.array(alm_calibrated)
alm_uncalibrated = np.array(alm_uncalibrated)
valid_times = np.array(valid_times)
alm_observed = np.array(alm_observed)

#ind = pd.MultiIndex.from_product((x, y), names=('anios', 'fec'))
#ds_obs = ds_obs.assign(time=ind).unstack('time')

ds = xr.Dataset({'alm_calibrated': (('start_date', 'step', 'ensemble'), alm_calibrated),
                 'alm_uncalibrated': (('start_date', 'step', 'ensemble'), alm_uncalibrated),
                 'alm_observed': (('start_date', 'step'), alm_observed),
                'valid_date': (('start_date', 'step'), valid_times)},
               coords={
                   'start_date': start_times,
                   'step':np.arange(-1, 30, 1),
                   'ensemble': np.arange(1, 17)})

ds.to_netcdf('prueba.nc')


