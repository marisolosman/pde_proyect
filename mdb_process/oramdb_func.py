import os
import glob
import pyodbc
import numpy as np
import pandas as pd
import datetime as dt

from etp_func import (calcularDr, calcularOmegaS, calcularRa,
                      calcularDelta, calculaRSdeHeliofania)
'''
Set de funciones para interactuar con la base de datos ORA: ora.mdb
Dado que para este proyecto se trabaja a nivel de Estacion
se considera que la base de todo es un DataFrame (DF) de Pandas.
Actualmente:
get_hist_sql_string --> permite obtener string para extraer datos historicos
read_data_hist_mdb --> permite obtener un DF con datos historicos 1999-2010
'''
# General parameters to read database
drv = '{Microsoft Access Driver (*.mdb, *.accdb)}'
pwd = 'pw'
db = 'c:/Felix/ORA/base_datos/BaseNueva/ora.mdb'
db_csv = '/home/osman/proyectos/pde_proyect/ora.csv'

def get_hist_sql_string(tv, ti, ide):
    """
    This function generate the strings to get data from the
    database of ORA (ora.mdb)
    """
    SQL_q2 = ''
    if tv == 'precip':
        SQL_q1 = '''
            SELECT Fecha, Precipitacion FROM DatoDiario
            WHERE Estacion = {}
            AND (((DatoDiario.Fecha)>=#1/1/1999#))
            AND (((DatoDiario.Fecha)<=#12/31/2010#))
            ORDER BY Fecha
            '''.format(ide)
    elif tv == 'etp':
        SQL_q1 = '''
            SELECT Fecha, ETP FROM DatoDiario
            WHERE Estacion = {}
            AND (((DatoDiario.Fecha)>=#1/1/1999#))
            AND (((DatoDiario.Fecha)<=#12/31/2010#))
            ORDER BY Fecha
            '''.format(ide)
    elif tv == 'tmin':
        if ti == 'SMN':
            SQL_q1 = '''
                SELECT Fecha, Tmin FROM DatoDiarioSMN
                WHERE Estacion = {}
                AND (((DatoDiarioSMN.Fecha)>=#1/1/1999#))
                AND (((DatoDiarioSMN.Fecha)<=#12/31/2010#))
                ORDER BY Fecha
                '''.format(ide)
    elif tv == 'tmax':
        if ti == 'SMN':
            SQL_q1 = '''
                SELECT Fecha, Tmax FROM DatoDiarioSMN
                WHERE Estacion = {}
                AND (((DatoDiarioSMN.Fecha)>=#1/1/1999#))
                AND (((DatoDiarioSMN.Fecha)<=#12/31/2010#))
                ORDER BY Fecha
                '''.format(ide)
    elif tv == 'velviento':
        if ti == 'SMN':
            SQL_q1 = '''
                SELECT Fecha, Viento FROM DatoDiarioSMN
                WHERE Estacion = {}
                AND (((DatoDiarioSMN.Fecha)>=#1/1/1999#))
                AND (((DatoDiarioSMN.Fecha)<=#12/31/2007#))
                ORDER BY Fecha
                '''.format(ide)
            SQL_q2 = '''
                SELECT Fecha, Hora, Viento FROM MedicionHorariaSMN
                WHERE Estacion = {}
                AND (((MedicionHorariaSMN.Fecha)>=#1/1/2008#))
                AND (((MedicionHorariaSMN.Fecha)<=#12/31/2010#))
                ORDER BY Fecha
                '''.format(ide)
    elif tv == 'radsup':
        if ti == 'SMN':
            SQL_q1 = '''
                SELECT Fecha, Heliofania FROM DatoDiarioSMN
                WHERE Estacion = {}
                AND (((DatoDiarioSMN.Fecha)>=#1/1/1999#))
                AND (((DatoDiarioSMN.Fecha)<=#12/31/2010#))
                ORDER BY Fecha
                '''.format(ide)

    elif tv == 'hrmean':
        if ti == 'SMN':
            if ti == 'SMN':
                SQL_q1 = '''
                    SELECT Fecha, Humedad FROM DatoDiarioSMN
                    WHERE Estacion = {}
                    AND (((DatoDiarioSMN.Fecha)>=#1/1/1999#))
                    AND (((DatoDiarioSMN.Fecha)<=#12/31/2007#))
                    ORDER BY Fecha
                    '''.format(ide)
                SQL_q2 = '''
                    SELECT Fecha, Hora, Humedad FROM MedicionHorariaSMN
                    WHERE Estacion = {}
                    AND (((MedicionHorariaSMN.Fecha)>=#1/1/2008#))
                    AND (((MedicionHorariaSMN.Fecha)<=#12/31/2010#))
                    ORDER BY Fecha
                    '''.format(ide)

    # ## End of SQL string to select data
    return SQL_q1, SQL_q2


def read_SMN_data(var, tipo, idestacion):
    '''
    This function only applies to SMN data that are contained in
    MedicionHorariaSMN and DatoDiarioSMN tables from the database ora.mdb
    And only applies for the historical data, because this variables comes from
    different sources since 01/01/2008.
    '''
    try:
        cnxn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(drv, db, pwd))
    except pyodbc.Error as err:
        logging.warn(err)
        print('La base NO esta en: ' + db)
        print('Si no, corregir codigo read_data_hist_mdb en oramdb_func.py')

    SQL_s1, SQL_s2 = get_hist_sql_string(var, tipo, idestacion)
    df1 = pd.read_sql_query(SQL_s1, cnxn)
    df2 = pd.read_sql_query(SQL_s2, cnxn)  # De tabla horaria
    cnxn.close()
    if df2.empty:
        fechas = pd.date_range('2008-01-01','2010-12-31')
        if var == 'wnd10m' or var == 'velviento':
            aux = {'Fecha': fechas,'Viento':np.nan*np.ones(len(fechas))}
            df4 = pd.DataFrame(index=np.arange(0, len(fechas)),
                               columns=['Fecha','Viento'], data=aux)
        elif var == 'hrmean':
            aux = {'Fecha': fechas,'Humedad':np.nan*np.ones(len(fechas))}
            df4 = pd.DataFrame(index=np.arange(0, len(fechas)),
                               columns=['Fecha','Humedad'], data=aux)
    else:
        df2['H'] = df2['Hora'].apply(lambda x: '{0:0>2}'.format(x))
        df2['D'] = pd.to_datetime(df2['Fecha'].dt.date.astype(str) +\
                                  ' ' + df2['H'].astype(str),
                                  format='%Y-%m-%d %H')
        df2['D_UTC'] = df2['D'].dt.tz_localize('UTC')
        df2['D_LOCAL'] = df2['D_UTC'].dt.tz_convert('America/Argentina/Buenos_Aires')
        if var == 'wnd10m' or var == 'velviento':
            df3 = df2.groupby([df2['D_LOCAL'].dt.date])['Viento'].mean()
            df3 = df3.iloc[1::]
            aux = {'Fecha': df3.index, 'Viento':df3.values}
            df4 = pd.DataFrame(index=np.arange(0, len(df3)),
                               columns=['Fecha','Viento'], data=aux)
            # Transformamos ambas series de km/hora --> m/s
            df1['Viento'] = (1./3.6) * df1['Viento']
            df4['Viento'] = (1./3.6) * df4['Viento']
        elif var == 'hrmean':
            df3 = df2.groupby([df2['D_LOCAL'].dt.date])['Humedad'].mean()
            df3 = df3.iloc[1::]
            aux = {'Fecha': df3.index, 'Humedad':df3.values}
            df4 = pd.DataFrame(index=np.arange(0, len(df3)),
                               columns=['Fecha','Humedad'], data=aux)
        #
    df1['Fecha'] = df1['Fecha'].dt.strftime('%Y-%m-%d')
    df = pd.concat([df1, df4], axis=0, ignore_index=True)
    df['Fecha'] = pd.to_datetime(df.Fecha)
    df1 = None
    df2 = None
    df3 = None
    df4 = None
    #
    if var == 'wnd10m' or var == 'velviento':
        print('NaN ', df['Viento'].isna().sum())
        df.rename(columns={'Viento': 'velviento'}, inplace=True)
    elif var == 'hrmean':
        print('NaN ', df['Humedad'].isna().sum())
        df.rename(columns={'Humedad': 'hrmean'}, inplace=True)
    return df


def get_latlon_mdb(idestacion):
    '''
    Get the Latitude and Longitude of station of database
    '''
    try:
        cnxn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(drv, db, pwd))
    except pyodbc.Error as err:
        logging.warn(err)
        print('La base NO esta en: ' + db)
        print('Si no, corregir codigo read_data_hist_mdb en oramdb_func.py')
    SQL_E = '''
            SELECT Latitud, Longitud From Estacion
            WHERE IdEstacion = {}
            '''.format(idestacion)
    df_d = pd.read_sql_query(SQL_E, cnxn)
    cnxn.close()
    lat = df_d.Latitud.values
    lon = df_d.Longitud.values

    return lat, lon

def get_latlon_csv(idestacion):
    '''
    Get the Latitude and Longitude of station of database
    '''
    cols = ['ID', 'lat', 'lon']
    df_d = pd.read_csv(db,)
    lat = df.lat[df.ID==int(idestacion)]
    lon = df.lon[df.ID==int(idestacion)]
#    lat = df_d.Latitud.values
#    lon = df_d.Longitud.values

    return lat, lon


def read_data_hist_mdb(var, tipo, idestacion):
    '''
    var: String con nombre de variable
    tipo: String con tipo de estacion
    idestacion: String con ID de estacion en ora.mdb
    '''
    try:
        cnxn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(drv, db, pwd))
    except pyodbc.Error as err:
        logging.warn(err)
        print('La base NO esta en: ' + db)
        print('Si no, corregir codigo read_data_hist_mdb en oramdb_func.py')
    listVar = ['tmax', 'tmin', 'hrmean', 'velviento', 'precip', 'radsup', 'etp']
    if var not in listVar:
        err_msg =''' El tipo de variable: {} NO se encuentra
        en el listado.\n
        Queda por programar esa extraccion de variables de la base.\n
         ----- Saliendo del programa -----
        '''.format(var)
        print('Listado de variables actualmente disponibles:')
        print(listVar)
        print(err_msg)
        exit()
    listTipo = ['SMN']
    if tipo not in listTipo:
        err_msg =''' El tipo de estacion: {} NO se encuentra
        en el listado.\n
        Queda por programar esa extraccion de variables de la base.\n
         ----- Saliendo del programa -----
        '''.format(tipo)
        print('Listado de variables actualmente disponibles:')
        print(listVar)
        print(err_msg)
        exit()
    if var == 'hrmean' or var == 'velviento':
        df = read_SMN_data(var, tipo, idestacion)
        df.dropna(inplace=True)
    elif var == 'radsup':
        SQL_q, SQL_extra = get_hist_sql_string(var, tipo, idestacion)
        df0 = pd.read_sql_query(SQL_q, cnxn)
        if df0.dropna().empty:
            SQL_q1 = '''
                SELECT Fecha, valor  FROM DatoInterpolado
                WHERE Estacion = {}
                AND nombreCampo = 7
                AND (((DatoInterpolado.Fecha)>=#1/1/1999#))
                AND (((DatoInterpolado.Fecha)<=#12/31/2010#))
                ORDER BY Fecha
                '''.format(idestacion)
            df0 = pd.read_sql_query(SQL_q1, cnxn)
            df0.rename(columns={'Fecha': 'Fecha', 'valor': 'Heliofania'}, inplace=True)

        SQL_E = '''
                SELECT Latitud, Longitud From Estacion
                WHERE IdEstacion = {}
                '''.format(idestacion)
        df_d = pd.read_sql_query(SQL_E, cnxn)
        cnxn.close()
        # --------------------------- OJO ACA ----------------------------------
        # Consideramos que tenemos Heliofania y transformamos RS para comparar
        #                             Con CFS
        # ----------------------------------------------------------------------
        # Calcular dia Juliano de Columna Fecha
        df0['Juliano'] = df0['Fecha'].dt.strftime('%j')
        # -- Comenzamos transformacion ---

        # ..................................
        a_juliano = np.array(df0.Juliano.values, dtype=np.float64)
        df0['dr'] = calcularDr(a_juliano)
        df0['delta'] = calcularDelta(a_juliano)
        df0['omega'] = calcularOmegaS(df_d.Latitud.values,\
                                               df0.delta)
        df0['Ra'] = calcularRa(a_juliano, df_d.Latitud.values,\
                                        df0.delta, df0.omega)
        df0['Rs'] = calculaRSdeHeliofania(df0.Heliofania.values,\
                                                   df0.omega, df0.Ra);
        df = df0.loc[:, ['Fecha', 'Rs']]
        print('NaN ', df['Rs'].isna().sum())
        df.dropna(inplace=True)
        df.rename(columns={'Rs':var}, inplace=True)
    else:
        SQL_q, SQL_extra = get_hist_sql_string(var, tipo, idestacion)
        df = pd.read_sql_query(SQL_q, cnxn)
        cnxn.close()
        if var == 'precip':
            df.rename(columns={'Precipitacion':var}, inplace=True)
            print('NaN ', df[var].isna().sum())
        elif var == 'tmax':
            df.rename(columns={'Tmax':var}, inplace=True)
            print('NaN ', df[var].isna().sum())
            df.dropna(inplace=True)
        elif var == 'tmin':
            df.rename(columns={'Tmin':var}, inplace=True)
            print('NaN ', df[var].isna().sum())
            df.dropna(inplace=True)
        elif var =='etp':
            df.rename(columns={'ETP':var}, inplace=True)
            print('NaN ', df[var].isna().sum())
            df.dropna(inplace=True)
    return df


def get_medias_ETP(idestacion):
    '''
    '''
    try:
        cnxn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(drv, db, pwd))
    except pyodbc.Error as err:
        logging.warn(err)
        print('La base NO esta en: ' + db)
        print('Si no, corregir codigo read_data_hist_mdb en oramdb_func.py')
    SQL = '''
        SELECT * FROM MediasETPporEstacion
        WHERE Estacion = {}
        '''.format(idestacion)
    tabla = pd.read_sql_query(SQL, cnxn)

    return tabla


def get_data_estacion_mdb(idestacion):
    '''
    La base de datos cuenta con las latitudes y longitudes de cada estacion
    Esta funcion devuelve los valores de latitud y longitud a partir de la
    ID de la estacion
    '''
    try:
        cnxn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(drv, db, pwd))
    except pyodbc.Error as err:
        logging.warn(err)
        print('La base NO esta en: ' + db)
        print('Si no, corregir codigo read_data_hist_mdb en oramdb_func.py')
    idtipo = pd.read_sql_query('SELECT * From TipoEstacion', cnxn)
    provincia = pd.read_sql_query('SELECT * From Provincia', cnxn)
    SQL_E = '''
            SELECT Nombre, ProvinciaID, IdTipo, Latitud, Longitud From Estacion
            WHERE IdEstacion = {}
            '''.format(idestacion)
    df_d = pd.read_sql_query(SQL_E, cnxn)
    cnxn.close()
    if df_d.empty:
        print('Los datos ingresado no corresponden a una estacion en la base')
        lat_e = np.nan
        lon_e = np.nan
    else:
        out = {}
        out['Nombre'] = df_d.Nombre.values[0]
        out['Provincia'] = provincia.loc[provincia['IDProv']== df_d.ProvinciaID.values[0],
                                         'Provincia'].values[0]
        out['Tipo'] = idtipo.loc[idtipo['IdTipo']== df_d.IdTipo.values[0], 'Nombre'].values[0]
        out['Lat'] = df_d.Latitud.values[0]
        out['Lon'] = df_d.Longitud.values[0]
        out['id'] = idestacion

    return out


if __name__ == "__main__":
    variables = ['tmax', 'tmin', 'radsup', 'hrmean', 'velviento', 'precip']
    for nomvar in variables:
        df = pd.read_csv('/home/osman/proyectos/pde_proyect/datos/estaciones.txt', sep=';')
        for row in df.itertuples():
            print(nomvar)
            dfm = read_data_hist_mdb(nomvar, row.tipo_est, row.id_est)
    #print(dfm)
