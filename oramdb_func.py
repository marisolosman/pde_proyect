import os
import glob
import pyodbc
import numpy as np
import pandas as pd
import datetime as dt

'''
Set de funciones para interactuar con la base de datos ORA: ora.mdb
Dado que para este proyecto se trabaja a nivel de Estacion
se considera que la base de todo es un DataFrame (DF) de Pandas.
Actualmente:
get_hist_sql_string --> permite obtener string para extraer datos historicos
read_data_hist_mdb --> permite obtener un DF con datos historicos 1999-2010
'''


def get_hist_sql_string(tv, ti, ide):
    """
    This function generate the strings to get data from the
    database of ORA (ora.mdb)
    """
    SQL_q2 = ''
    if tv == 'prate':
        SQL_q1 = '''
            SELECT Fecha, Precipitacion FROM DatoDiario
            WHERE Estacion = {}
            AND (((DatoDiario.Fecha)>#1/1/1999#))
            AND (((DatoDiario.Fecha)<#12/31/2010#))
            '''.format(ide)
    elif tv == 'tmin':
        if ti == 'SMN':
            SQL_q1 = '''
                SELECT Fecha, Tmin FROM DatoDiarioSMN
                WHERE Estacion = {}
                AND (((DatoDiarioSMN.Fecha)>#1/1/1999#))
                AND (((DatoDiarioSMN.Fecha)<#12/31/2010#))
                '''.format(ide)
    elif tv == 'tmax':
        if ti == 'SMN':
            SQL_q1 = '''
                SELECT Fecha, Tmax FROM DatoDiarioSMN
                WHERE Estacion = {}
                AND (((DatoDiarioSMN.Fecha)>=#1/1/1999#))
                AND (((DatoDiarioSMN.Fecha)<=#12/31/2010#))
                '''.format(ide)
    elif tv == 'wnd10m':
        if ti == 'SMN':
            SQL_q1 = '''
                SELECT Fecha, Viento FROM DatoDiarioSMN
                WHERE Estacion = {}
                AND (((DatoDiarioSMN.Fecha)>=#1/1/1999#))
                AND (((DatoDiarioSMN.Fecha)<=#12/31/2007#))
                '''.format(ide)
            SQL_q2 = '''
                SELECT Fecha, Hora, Viento FROM MedicionHorariaSMN
                WHERE Estacion = {}
                AND (((MedicionHorariaSMN.Fecha)>=#1/1/2008#))
                AND (((MedicionHorariaSMN.Fecha)<=#12/31/2010#))
                '''.format(ide)
    elif tv == 'dswsfc':
        if ti == 'SMN':
            SQL_q1 = '''
                SELECT Fecha, Heliofania FROM DatoDiarioSMN
                WHERE Estacion = {}
                AND (((DatoDiarioSMN.Fecha)>=#1/1/1999#))
                AND (((DatoDiarioSMN.Fecha)<=#12/31/2010#))
                '''.format(ide)


    # ## End of SQL string to select data
    return SQL_q1, SQL_q2


def read_data_hist_mdb(var, tipo, idestacion):
    '''
    var: String con nombre de variable
    tipo: String con tipo de estacion
    idestacion: String con ID de estacion en ora.mdb
    '''
    drv = '{Microsoft Access Driver (*.mdb, *.accdb)}'
    pwd = 'pw'
    db = 'c:/Felix/ORA/base_datos/BaseNueva/ora.mdb'
    try:
        print('Conectando a base: ' + db)
        cnxn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(drv, db, pwd))
    except pyodbc.Error as err:
        logging.warn(err)
        print('La base NO esta en: ' + db)
        print('Si no, corregir codigo read_data_hist_mdb en oramdb_func.py')
    listVar = ['prate', 'dswsfc', 'tmax', 'tmin', 'wnd10m', 'hr']
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
    if var == 'wnd10m':
        SQL_s1, SQL_s2 = get_hist_sql_string(var, tipo, idestacion)
        df1 = pd.read_sql_query(SQL_s1, cnxn)
        df2 = pd.read_sql_query(SQL_s2, cnxn)
        cnxn.close()
        df2['H'] = df2['Hora'].apply(lambda x: '{0:0>2}'.format(x))
        df2['D'] = pd.to_datetime(df2['Fecha'].dt.date.astype(str) +\
                                  ' ' + df2['H'].astype(str),
                                  format='%Y-%m-%d %H')
        df2['D_UTC'] = df2['D'].dt.tz_localize('UTC')
        df2['D_LOCAL'] = df2['D_UTC'].dt.tz_convert('America/Argentina/Buenos_Aires')
        df3 = df2.groupby([df2['D_LOCAL'].dt.date])['Viento'].mean()
        df3 = df3.iloc[1::]
        aux = {'Fecha': df3.index, 'Viento':df3.values}
        df4 = pd.DataFrame(index=np.arange(0, len(df3)), columns=['Fecha','Viento'],
                           data=aux)
        df1['Fecha'] = df1['Fecha'].dt.strftime('%Y-%m-%d')
        df = pd.concat([df1, df4], axis=0, ignore_index=True)
        df1 = None
        df2 = None
        df3 = None
        df4 = None
    elif var == 'dswsfc':
        SQL_q, SQL_extra = get_hist_sql_string(var, tipo, idestacion)
        df0 = pd.read_sql_query(SQL_q, cnxn)
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
        import etp_func
        # ..................................
        a_juliano = np.array(df0.Juliano.values, dtype=np.float64)
        df0['dr'] = etp_func.calcularDr(a_juliano)
        df0['delta'] = etp_func.calcularDelta(a_juliano)
        df0['omega'] = etp_func.calcularOmegaS(df_d.Latitud.values,\
                                               df0.delta)
        df0['Ra'] = etp_func.calcularRa(a_juliano, df_d.Latitud.values,\
                                        df0.delta, df0.omega)
        df0['Rs'] = etp_func.calculaRSdeHeliofania(df0.Heliofania.values,\
                                                   df0.omega, df0.Ra);
        df = df0[['Fecha', 'Rs']]
    else:
        SQL_q, SQL_extra = get_hist_sql_string(var, tipo, idestacion)
        df = pd.read_sql_query(SQL_q, cnxn)
        cnxn.close()
    return df
