"""
09/03/2020 Creado por Felix Carrasco

This script is made to perform the extraction of data
necessary to do:
    - 16 ensemble members (EM)
    - Each of the EM contains a 30 day forecast values
     to all variables that are needed to made a Hidryc Balance
     forecast (tmax, tmin, radsup, hr, velviento and precip). 
"""
import sys
import os
import numpy as np
import pandas as pd
import datetime as dt
import glob
import time
import xarray as xr

from grib_func import get_files_o

def calc_radsup(r_sup):
    '''
    This function calculates for an array_like with 4 values
    the integrated value of Surface Radiation
    '''
    x = np.array([0., 3., 9., 15., 21., 23.]) * 60. * 60. # segundos
    y = np.array(r_sup)
    y = np.insert(y, 0, 0.)
    y = np.append(y, 0.)
    tot_rad = np.trapz(y, x) * 1.e-6  #Mj/m2
    return tot_rad


# --------------------------------------------
start_time = time.time()
# ############################################
folder = '/datos2/CFSReana/'
var    = sys.argv[1]  # Segundo argumento variable
print(var)
# Other options: tmax, tmin, dswsfc,
#                hr, wnd10m
if var == 'hrmean':  # Si se calcula HR hay que elegir que calcular:
    var = 'hr'
    operacion = 'mean'  # programados: 'min', 'max' y 'mean'
elif var == 'hrmin':
    var = 'hr'
    operacion = 'min'
elif var == 'hrmax':
    var = 'hr'
    operacion = 'max'
#
# Lat-Lon Resistencia: -27.45/-59.05 (SMN)
# Lat-Lon Junin: -34.55/-60.92 (SMN)
lat_e = [-27.45]
lon_e = [-59.05]
n_est = ['resistencia']

outfolder = '../pde_salidas/operativo/'
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

fecha = dt.datetime(2009,11,23)  # Test inicio de periodo por deficit.
print(' --- Generando pronosticos para el: ' + fecha.strftime('%d-%m-%Y') + ' --- ')
i_fecha = fecha + dt.timedelta(days=1)
f_fecha = fecha + dt.timedelta(days=30)
dic['idate'] = i_fecha
dic['fdate'] = f_fecha
print(dic)
fval = pd.date_range(start=i_fecha, end=f_fecha, freq='D').to_pydatetime().tolist()
ens = 0
archivos = []
while len(archivos) <= 16:
    d1 = i_fecha - dt.timedelta(hours=6*ens)
    #print(ens+1, d1)
    str_d = d1.strftime('%Y%m%d%H')
    aux_f = glob.glob(folder+var+'/'+str(d1.year)+'/*'+str_d+'.grb2')
    if aux_f:
        archivos.append(aux_f[0])
        #print(aux_f[0])
    ens += 1

for arch in archivos[0:1]:
    grbs = xr.open_dataset(arch, engine='pynio')#, chunks={'lon_0':20, 'lat_0':20})
    nvar = list(grbs.data_vars.keys())[0]
    
    xe   = np.array(dic['lon_e']) % 360
    ye   = dic['lat_e']
    data = grbs[nvar].sel(lon_0=xe, lat_0=ye, method='nearest')
    aux_d = data.to_pandas()
    new_index = (i_fecha + aux_d.index).tz_localize('UTC')  # Horas UTC
    new_index = new_index.tz_convert('America/Argentina/Buenos_Aires')
    datos = pd.Series(index=new_index, data=aux_d.array, dtype='float32')
    if var == 'wnd10m':
        nvar1 = list(grbs.data_vars.keys())[1]
        data1 = grbs[nvar1].sel(lon_0=xe, lat_0=ye, method='nearest')
        aux_d1 = data1.to_pandas()
        datos1 = pd.Series(index=new_index, data=aux_d1.array, dtype='float32')
        spd = (datos1**2 * datos**2).apply(np.sqrt)
        print(spd.resample('1D').mean())
    #print(datos.index)
    #print(datos.resample('1D').apply(calc_radsup))
    
    

print("--- %s seconds ---" % (time.time() - start_time))

