"""
09/04/2019 Creado por Felix Carrasco

This script contains functions to read, extract data from
grib2 files, contained in Pikachu database.

The datafiles correspond to 1999-2009 period of CFS data
with 120 days of forecast between 6 hours.

The project considers a forecast to 30 days.

The functions programmed in this grib_func.py
allows to read for specific lat lon meteorological
station.
"""
import sys
import os
import numpy as np
import pandas as pd
import datetime as dt
import glob
import time

from grib_func import get_files_o
from grib_func import get_files_prate
from grib_func import get_daily_value
from grib_func import create_summary_file

# --------------------------------------------
start_time = time.time()
# ############################################
folder = '/datos2/CFSReana/'
yy     = sys.argv[1]
var    = sys.argv[2]
print(yy, var)
# Other options: tmax, tmin, dswsfc,
#                hr, wnd10m

lat_e = [-27.45]  # Test con estacion Resistencia (Chaco, SMN)
lon_e = [-59.05]
n_est = ['resistencia']

outfolder = '../pde_salidas/'
os.makedirs(outfolder, exist_ok=True)
it = 0
# Diccionario con datos generales
dic = {'ofolder':outfolder,
        'dfolder':folder, 'var':var,
        'lat_e':lat_e[it], 'lon_e':lon_e[it],
        'n_est':n_est[it]}

# -------------------------------------------------------
# MAIN CODE
# -------------------------------------------------------
print(' --- Extrayendo datos para: ' + yy + ' --- ')
i_fecha = yy+'-01-01'
f_fecha = yy+'-12-31'
fval = pd.date_range(start=i_fecha, end=f_fecha, freq='D').to_pydatetime().tolist()
fmat = np.empty((len(fval), 4))
fmat.fill(np.nan)
print(fmat.shape)

# Comenzamos a iterar en cada fecha
for idx, fecha in enumerate(fval):
    if fecha.day == 1:
        print('Trabajando en el mes: ' + fecha.strftime('%Y-%m') )
# --
    if var == 'hr':
        files = get_files_hr(fecha, dic)
    elif var == 'prate':
        files = get_files_prate(fecha, dic)
        valores = get_daily_value(files, fecha, dic)
        fmat[idx, :] = list(valores.values())
        files = None
        valores = None
    else:
        files = get_files_o(fecha, dic)
        valores = get_daily_value(files, fecha, dic)
        fmat[idx, :] = list(valores.values())
        files = None
        valores = None
# --
os.makedirs(outfolder + n_est[it], exist_ok=True)
n_file = outfolder + n_est[it] + '/data_' + var +'_' + str(fval[0].year) + '.txt'
if os.path.exists(n_file):
    os.remove(n_file)
df = create_summary_file(dic, fval, fmat)
sel_col = list(df)[1::]
df[sel_col] = df[sel_col].apply(pd.to_numeric, errors='ignore')
df.to_csv(n_file, sep=';', float_format='%.2f', decimal=',',
          date_format='%Y-%m-%d')
print("--- %s seconds ---" % (time.time() - start_time))
