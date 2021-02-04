import os
import pandas as pd
import numpy as np
import netCDF4 as nc
import sys
from oramdb_func import *
from procesa_historicos import crea_variable_estacion



carpeta = '../datos/datos_hist/obs/'
os.makedirs(carpeta, exist_ok=True)
nomvar = 'ALMR'
unid = 'mm'

archivo = '../datos/bhora_init/balance_RESIS_FL40-45_S1-VII_NORTE.xls'
df = pd.read_excel(archivo, sheet_name='DatosDiarios')
almr_obs = df['alm real'].to_numpy()
fobs = df['Fecha'].dt.to_pydatetime()
ifecha = np.logical_and(fobs >= dt.datetime(1999,1,1),
                        fobs <=dt.datetime(2010,12,31) )
datos = almr_obs[ifecha]
d1 = dt.datetime.strptime('1999-01-01', '%Y-%m-%d')
d2 = dt.datetime.strptime('2010-12-31', '%Y-%m-%d')
time_unit = 'days since 1999-01-01 00:00:00'
calendar_u = 'proleptic_gregorian'
namefile = carpeta + nomvar + '_' + d1.strftime('%Y%m') +\
       '_' + d2.strftime('%Y%m') + '.nc'
print('Generando Archivo: ' + namefile)
f = nc.Dataset(namefile, 'w', format='NETCDF4')
f.createDimension('time', None)
# Variable tiempo
tiempos = f.createVariable('time', 'u8', ('time',))
tiempos.units = time_unit
tiempos.calendar = calendar_u
tiempos.axis = 'T'
f.variables['time'][:] = nc.date2num(fobs[ifecha],
                                     units=time_unit,
                                     calendar=calendar_u)
# ALMR
# Datos para todas las fechas entre 01/01/1999 - 31/12/2010
datos_e = get_data_estacion_mdb('107')
datos_e['nombre_variable'] = 'resistencia'
datos_e['datos'] = datos
datos_e['units'] = unid
#
crea_variable_estacion(f, datos_e)

f.close()
