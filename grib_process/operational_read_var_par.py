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
from pytz import timezone
from grib_func import get_files_o
import multiprocessing as mp
from pathos.multiprocessing import ProcessingPool as Pool
CORES = mp.cpu_count()

folder = '/datos/osman/CFS_operational/'

def get_ens_file(nvar, i_date):
    '''
    This function obtains a list with the files to be used for
    prognostic
    '''
    if nvar == 'hr':
        print('Humedad relativa')
        variables = ['pressfc', 'q2m', 'tmp2m']
        archivos = {}
        for vr in variables:
            lfls = []
            if (i_date < dt.datetime(2021, 2, 23)):
                for i in range(4):
                    for ens in [0, 6, 12, 18]:
                        d1 = i_date - dt.timedelta(hours=24 * i) + dt.timedelta(hours=ens)
                        str_d = d1.strftime('%Y%m%d%H')
                        file_str = folder + vr + '/' + str(d1.year) + '/' + d1.strftime('%m') + '/' + \
                                vr + '.01.' + str_d + '*.grb2'
                        aux_f = glob.glob(file_str)
                        if aux_f:
                            lfls.append(aux_f[0])
                        else:
                            lfls.append('vacio')
                archivos[vr] = lfls
            else:
                for i in range(1, 5):
                    for ens in [0, 6, 12, 18]:
                        d1 = i_date + dt.timedelta(hours=ens)
                        str_d = d1.strftime('%Y%m%d%H')
                        file_str = folder + vr + '/' + str(d1.year) + '/' + d1.strftime('%m') + '/'  +\
                                vr + '.0' + str(i) + '.' + str_d + '*.grb2'
                        aux_f = glob.glob(file_str)
                        if aux_f:
                            lfls.append(aux_f[0])
                        else:
                            lfls.append('vacio')
                archivos[vr] = lfls
        if archivos:
            return archivos
        else:
            print('No hay archivos disponibles para la fecha indicada')
            exit()
    else:
        archivos = []
        #while len(archivos) <= 16:
        if ((i_date < dt.datetime(2021, 2, 23)) & (nvar != 'prate')) | ((nvar == 'prate') & (i_date < dt.datetime(2021, 6, 10))):
            for i in range(4):
                for ens in [0, 6, 12, 18]:
                    d1 = i_date - dt.timedelta(hours=24 * i) + dt.timedelta(hours=ens)
                    str_d = d1.strftime('%Y%m%d%H')
                    file_str = folder + nvar + '/' + str(d1.year) + '/' + d1.strftime('%m') + '/' + \
                            nvar + '.01.' + str_d + '*.grb2'
                    aux_f = glob.glob(file_str)
                    if aux_f:
                        archivos.append(aux_f[0])
                    else:
                        archivos.append('vacio')
        else:
        #print(ens+1, d1)
            for i in range(1, 5):
                for ens in [0, 6, 12, 18]:
                    d1 = i_date + dt.timedelta(hours=ens)
                    str_d = d1.strftime('%Y%m%d%H')
                    file_str = folder + nvar + '/' + str(d1.year) + '/' + d1.strftime('%m') + '/' + \
                           nvar + '.0' + str(i) + '.' + str_d + '*.grb2'
                    aux_f = glob.glob(file_str)
                    if aux_f:
                            archivos.append(aux_f[0])
                    else:
                        archivos.append('vacio')
        if archivos:
            return archivos
        else:
            print('No hay archivos disponibles para la fecha indicada')
        exit()

def get_data_from_grib(grb_file, xlat, xlon, fecha):
    '''
    extract a data from gribfile for specified xlat and xlon
    returns a pandas dataframe
    '''
    grbs = xr.open_dataset(grb_file, engine='cfgrib')
    nvar = list(grbs.data_vars.keys())[0]
    xe   = np.array(xlon) % 360
    ye   = xlat
    tiempos = grbs.valid_time.values <= np.datetime64(fecha + dt.timedelta(days=5))
    data = grbs[nvar].sel(longitude=xe, latitude=ye, step=tiempos, method='nearest')
    aux_d = data.to_pandas()
    grbs.close()

    return aux_d


def calc_radsup(r_sup):
    '''
    This function calculates for an array_like with 4 values
    the integrated value of Surface Radiation
    '''
    if len(r_sup) < 4:
        tot_rad = np.nan
    else:
        x = np.array([0., 3., 9., 15., 21., 23.]) * 60. * 60. # segundos
        y = np.array(r_sup)
        y = np.insert(y, 0, 0.)
        y = np.append(y, 0.)
        tot_rad = np.trapz(y, x) * 1.e-6  #Mj/m2

    return tot_rad


def calc_precip(pp_h):
    '''
    This function calculates for an array_like with 4 values
    the daily accumulated precipitation in meteorological time
    from 12UTC day -> 12 UTC day + 1
    or 9HL day -> 9HL day + 1
    '''
    factor_6h = 6.*60.*60.
    acc_precip = factor_6h*np.nansum(pp_h)

    return acc_precip


def get_initial_date(fgrib):
    '''
    Obtain a datetime object from attribute of gribfile input

    '''
    grbs = xr.open_dataset(fgrib, engine='cfgrib')
    nvar = list(grbs.data_vars.keys())[0]
    # str_f = grbs[nvar].time.values
    init_date = grbs[nvar].time.values # dt.datetime.strptime(str_f, '%m/%d/%Y (%H:%M)')
    grbs.close()

    return init_date


def calc_hr(init_date, psf, q2f, t2f):
    '''
    Calculate Relative Humidity (HR), using the three
    pandas Series obtained from get_data_from_grib function
    Also change the values of Index from hours of initial date
    to easy-use of resample pandas function.
    '''
    n_idx = (init_date + psf.index).tz_localize('UTC')
    n_idx = n_idx.tz_convert('America/Argentina/Buenos_Aires')
    # Formula to calculate HR
    T0 = 273.16
    av0 = np.divide(t2f - T0, t2f - 29.65)
    av1 = np.exp(17.63 * av0)
    av2 = np.power(av1, -1)
    hrs = 0.263 * psf * q2f * av2
    # Final output
    HR = pd.Series(index=n_idx, data=hrs.array, dtype='float32')

    return HR
# --------------------------------------------
start_time = time.time()
# ############################################
var    = sys.argv[1]  # Segundo argumento variable
f_str  = sys.argv[2]
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

lat_e = [-34.55, -27.45, -31.3, -33.11667, -35.966667, -33.666667, -31.783333, -29.9, -29.8833]
lon_e = [-60.92,  -59.05, -58.016667, -64.233333, -62.73333, -61.966667,
         -60.483333, -63.683333, -61.95]
n_est = ['junin', 'resistencia', 'concordia', 'rio_cuarto', 'trenque_lauquen',
         'venado_tuerto','parana', 'vmrs', 'ceres']
# -------------------------------------------------------
# MAIN CODE
# -------------------------------------------------------
tz_str = 'America/Argentina/Buenos_Aires'
arg_tz = timezone('America/Argentina/Buenos_Aires')
fecha = dt.datetime.strptime(f_str, '%Y-%m-%d')
print(fecha)
if fecha >= dt.datetime(2021, 2, 24):
    fecha = fecha - dt.timedelta(days=1)
    print(fecha)

print(' --- Generando pronosticos para el: ' + fecha.strftime('%d-%m-%Y') + ' --- ')

for ii in range(len(n_est)):
    # lat_e = [-34.55]
    # lon_e = [-60.92]
    # n_est = ['junin']
    # Diccionario con datos generales
    dic = {'dfolder':folder, 'var':var, 'lat_e':lat_e[ii], 'lon_e':lon_e[ii],
       'n_est':n_est[ii]}

    i_fecha = fecha
    f_fecha = (fecha + dt.timedelta(days=29))
    dic['idate'] = i_fecha
    dic['fdate'] = f_fecha

    # Obtenemos los archivos para calcular el ensamble
    archi = get_ens_file(var, i_fecha)

    # Abrimos una carpeta y guardamos los archivos ahi
    cpta_salida = '/home/osman/proyectos/pde_proyect/datos/datos_op/' + dic['n_est'] + '/' + fecha.strftime('%Y%m%d') + '/'
    os.makedirs(cpta_salida, exist_ok=True)
    dic['ofolder'] = cpta_salida
    # print(dic)
    def process_hr(ens, archi=archi, dic=dic, i_fecha=i_fecha, f_fecha=f_fecha):
            print('Calulando HR con archivos')
            f_ps = archi['pressfc'][ens]
            f_q2 = archi['q2m'][ens]
            f_t2 = archi['tmp2m'][ens]
            if 'vacio' in [f_ps, f_q2, f_t2]:
                print( 'No se genera pronostico para HR con: ')
                print('Presion sup: ', f_ps)
                print('Hum Esp 2m: ', f_q2)
                print('Tmp 2m: ', f_t2)
            else:
                # print(f_ps, f_q2, f_t2)
                in_t = get_initial_date(f_ps)
                d_ps = get_data_from_grib(f_ps, dic['lat_e'], dic['lon_e'], dic['fdate'])
                d_q2 = get_data_from_grib(f_q2, dic['lat_e'], dic['lon_e'], dic['fdate'])
                d_t2 = get_data_from_grib(f_t2, dic['lat_e'], dic['lon_e'], dic['fdate'])
                d_hr = calc_hr(in_t, d_ps, d_q2, d_t2)
                if operacion == 'mean':
                    fvar = 'hrmean'
                    resu = d_hr.resample(rule='1D').mean()
                elif operacion == 'max':
                    fvar = 'hrmax'
                    resu = d_hr.resample(rule='1D').max()
                elif operacion == 'min':
                    fvar = 'hrmin'
                    resu = d_hr.resample(rule='1D').min()
                else:
                    fvar = 'hrmean'
                    resu = d_hr.resample(rule='1D').mean()
                sel_d = np.logical_and(resu.index >= arg_tz.localize(i_fecha),\
                                       resu.index <= arg_tz.localize(f_fecha))
                resultado = resu.loc[sel_d]
            # Guardamos el archivo en la carpeta de salida
                in_t = dt.datetime.utcfromtimestamp(in_t.item()/10**9).strftime('%Y%m%d%H')
                archivo_salida = cpta_salida + fvar + '_' + str(ens).zfill(2) +\
                                 '_' + in_t + '.txt'
                resultado.to_csv(archivo_salida, sep=';', float_format='%.2f', decimal=',',\
                                 date_format='%Y-%m-%d',index_label='fecha', header=[fvar])
    def process_var(ens, archi=archi, var=var, dic=dic, i_fecha=i_fecha, f_fecha=f_fecha):
        arch = archi[ens]
        if arch == 'vacio':
            pass
        else:
            grbs = xr.open_dataset(arch, engine='cfgrib')#, chunks={'lon_0':20, 'lat_0':20})
            nvar = list(grbs.data_vars.keys())[0]
            xe   = np.array(dic['lon_e']) % 360
            ye   = dic['lat_e']
            tiempos = grbs.valid_time.values <= np.datetime64(dic['fdate'] + dt.timedelta(days=5))
            data = grbs[nvar].sel(longitude=xe, latitude=ye, step=tiempos, method='nearest')
            in_t = data.time.values
            aux_d = data.to_pandas()
            new_index = (in_t + aux_d.index).tz_localize('UTC')  # Horas UTC
            new_index = new_index.tz_convert(tz_str)
            datos = pd.Series(index=new_index, data=aux_d.array, dtype='float32')
            if var == 'wnd10m':
                fvar = 'velviento'
                nvar1 = list(grbs.data_vars.keys())[1]
                data1 = grbs[nvar1].sel(longitude=xe, latitude=ye, step=tiempos, method='nearest')
                aux_d1 = data1.to_pandas()
                datos1 = pd.Series(index=new_index, data=aux_d1.array, dtype='float32')
                spd = (datos1**2 + datos**2).apply(np.sqrt)
                resu = spd.resample('1D').mean()
            elif var == 'prate':
                fvar = 'precip'
                resu = datos.resample(rule='24H', closed='left', base=9).apply(calc_precip)
                resu.index = resu.index.map(lambda t: t.replace(hour=0))
            elif var == 'dswsfc':
                fvar = 'radsup'
                resu = datos.resample(rule='1D').apply(calc_radsup)
            elif var == 'tmax':
                fvar = var
                resu = datos.resample(rule='1D').max()
            elif var == 'tmin':
                fvar = var
                resu = datos.resample(rule='1D').min()
            grbs.close()
        # Seleccionamos datos de pronostico para prox 30 dias
            sel_d = np.logical_and(resu.index >= arg_tz.localize(i_fecha),\
                                   resu.index <= arg_tz.localize(f_fecha))
            resultado = resu.loc[sel_d]
            in_t = dt.datetime.utcfromtimestamp(in_t.item()/10**9).strftime('%Y%m%d%H')
            archivo_salida = cpta_salida + fvar + '_' + str(ens).zfill(2) + '_' + in_t + '.txt'
            resultado.to_csv(archivo_salida, sep=';', float_format='%.2f', decimal=',',\
                             date_format='%Y-%m-%d',index_label='fecha', header=[fvar])


        # Comenzamos el calculo en cada variable
    if var == 'hr':
        ipar = range(0, 16)
        p = Pool(CORES)
        p.clear()
        p.map(process_hr, ipar)
        p.close()
    else:
        ipar = range(0, 16)
        p = Pool(CORES)
        p.clear()
        p.map(process_var, ipar)
        p.close()

print("--- %s seconds ---" % (time.time() - start_time))
