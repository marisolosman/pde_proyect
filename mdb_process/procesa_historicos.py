import os
import pandas as pd
import numpy as np
import netCDF4 as nc

import matplotlib.pyplot as plt
#import sys
#sys.path.append('../mdb_process/')
from oramdb_func import *

def crea_variable_estacion(nc_arch, d_est):
    '''
    A partir de la referencia de un fichero netcdf,
    crea una variable de la estacion.
    El diccionario d_est debe contener las siguientes llaves:
    nombre_variable: String con el nombre de estacion a usar de variable
    nombre: String con el nombre de la estacion en la base
    precip: numpy array con los datos de precipitacion
    tipo: String con el tipo de estacion dado en el CSV
    id: ID en la base de datos ORA
    lat: Latitud de la estacion
    lon: Longitud de la estacion
    '''
    pp_o = nc_arch.createVariable(d_est['nombre_variable'], 'f8', ('time',),
                                  fill_value=-999.9)
    pp_o.units = d_est['units']
    pp_o.lat = d_est['Lat']
    pp_o.lon = d_est['Lon']
    pp_o.long_name = d_est['Nombre']
    pp_o.provincia = d_est['Provincia']
    pp_o.tipo = d_est['Tipo']
    pp_o.id_ora = d_est['id']
    nc_arch.variables[d_est['nombre_variable']][:] = d_est['datos']

def completar_faltante(DF, nomvar):
    '''
    En la base:
    NaN -> No llueve
    por lo que para representar datos faltantes se usara el numero 999.9
    en caso fuese necesario.
    '''
    fechas = pd.date_range(start='1999-01-01', end='2010-12-31')
    faltante = {'Fecha':fechas, nomvar:-999.9*np.ones(len(fechas))}
    da = pd.DataFrame(index=np.arange(0, len(fechas)), data=faltante)
    D1 = pd.merge(DF, da, on='Fecha', how='outer', indicator=True)
    if 'right_only' in D1._merge.values:
        D1.loc[D1._merge == 'right_only', nomvar + '_x'] = -999.9
    D1.sort_values(by=['Fecha'], inplace=True)
    D2 = pd.DataFrame(index=fechas, data={nomvar:D1[nomvar + '_x'].values})
    print(len(DF), len(fechas), len(D2))
    print('Faltantes: ', np.sum(D2[nomvar].to_numpy() == -999.9))
    return D2


#
carpeta = '../datos/datos_hist/obs/'
os.makedirs(carpeta, exist_ok=True)
variables = ['tmax', 'tmin', 'radsup', 'hrmean', 'velviento', 'precip', 'etp']
unidades = ['degree_celsius', 'degree_celsius', 'W/m2', '', 'm/s', 'mm', 'mm']
for nomvar, unid in zip(variables, unidades) :
    print(nomvar)
    d1 = dt.datetime.strptime('1999-01-01', '%Y-%m-%d')
    d2 = dt.datetime.strptime('2010-12-31', '%Y-%m-%d')
    time_unit = 'days since 1999-01-01 00:00:00'
    calendar_u = 'proleptic_gregorian'
    namefile = carpeta + nomvar + '_' + d1.strftime('%Y%m') +\
               '_' + d2.strftime('%Y%m') + '.nc'
    print('Generando Archivo: ' + namefile)
    f = nc.Dataset(namefile, 'w', format='NETCDF4')
    f.createDimension('time', None)
    df = pd.read_csv('../datos/estaciones.txt', sep=';')
    for row in df.itertuples():
        print(row)

        dfm = read_data_hist_mdb(nomvar, row.tipo_est, row.id_est)
        # Datos para todas las fechas entre 01/01/1999 - 31/12/2010
        df0 = completar_faltante(dfm, nomvar)
        datos_e = get_data_estacion_mdb(row.id_est)
        datos_e['nombre_variable'] = row.nom_est
        datos_e['datos'] = df0[nomvar].values
        datos_e['units'] = unid
        #
        #df0.plot(y=nomvar)
        #plt.show()

        if row.Index == 0:
            tiempos = f.createVariable('time', 'u8', ('time',))
            tiempos.units = time_unit
            tiempos.calendar = calendar_u
            tiempos.axis = 'T'
            f.variables['time'][:] = nc.date2num(df0.index.to_pydatetime(),
                                                 units=time_unit,
                                                 calendar=calendar_u)

            #print(nc.date2num(df0.index.to_pydatetime(), units=time_unit,
            #                  calendar=calendar_u))
        crea_variable_estacion(f, datos_e)

    f.close()
