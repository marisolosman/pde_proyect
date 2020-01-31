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
# General parameters to read database
drv = '{Microsoft Access Driver (*.mdb, *.accdb)}'
pwd = 'pw'
db = 'c:/Felix/ORA/base_datos/BaseNueva/ora.mdb'

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
    elif tv == 'hr':
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
    elif var == 'hr':
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
    listVar = ['tmax', 'tmin', 'hr', 'velviento', 'precip', 'radsup']
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
    if var == 'hr' or var == 'velviento':
        df = read_SMN_data(var, tipo, idestacion)
    elif var == 'radsup':
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


def get_id_cultivo(cultivo):
    '''
    Obtains the ID_CULTIVO to work with other tables.
    The entry is the string that is used in the database:
    '''
    try:
        cnxn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(drv, db, pwd))
    except pyodbc.Error as err:
        logging.warn(err)
        print('La base NO esta en: ' + db)
        print('Si no, corregir codigo read_data_hist_mdb en oramdb_func.py')
    # End TRY
    t_cult = pd.read_sql_query('SELECT * FROM Cultivo', cnxn)
    try:
        condicion = t_cult.Codigo == cultivo
        n_cultivo = t_cult['IdCultivo'].loc[condicion].values[0]
    except:
        print( '############ ERROR ###############')
        print('Para el cultivo ingresado: ' + cultivo + ' NO hay codigo')
        print( '##################################')
        exit()

    return n_cultivo


def read_soil_parameter(idestacion, cultivo, tipo_bh):
    '''
    This function read the soil parameters given the ID in ora.mdb station
    database
    '''
    id_cultivo = get_id_cultivo(cultivo)
    try:
        cnxn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(drv, db, pwd))
    except pyodbc.Error as err:
        logging.warn(err)
        print('La base NO esta en: ' + db)
        print('Si no, corregir codigo read_data_hist_mdb en oramdb_func.py')
    # End TRY
    SQL1 = '''
        SELECT ID, NombreUnidad, PatronSuelo, Cultivo FROM Balance
        WHERE Estacion = {}
        AND Cultivo = {}
        '''.format(idestacion, id_cultivo)
    PatSoil = pd.read_sql_query(SQL1, cnxn)
    if not PatSoil.empty:
        if tipo_bh == 'superficial':
            print('##### Parametros BH - Superficial #####')
            SQL2 = '''
                   SELECT Nombre, CC_sup, PMP_sup, CE_sup, CP_sup FROM PatronSuelo
                   WHERE IdPatron = {}
                   '''.format(str(PatSoil.PatronSuelo.values[0]))
            df1 = pd.read_sql_query(SQL2, cnxn)
            df1.rename(columns={'CC_sup':'CC', 'PMP_sup':'PMP', 'CE_sup':'CE',
                                'CP_sup':'CP'},
                       inplace=True)
        elif tipo_bh == 'profundo':
            print('##### Parametros BH - Profundo #####')
            SQL2 = '''
                   SELECT Nombre, CC, PMP, CE, CP FROM PatronSuelo
                   WHERE IdPatron = {}
                   '''.format(str(PatSoil.PatronSuelo.values[0]))
            df1 = pd.read_sql_query(SQL2, cnxn)
        else:
            print( '############ ERROR ###############')
            print('El tipo de BH: ' + tipo_bh)
            print('NO esta implementado o NO existe para calcular.')
            print( '##################################')
            exit()
        cnxn.close()
        out_dict = {'Nombre': df1.Nombre.values[0], 'CC': df1.CC.values[0],
                    'PMP': df1.PMP.values[0], 'CE': df1.CE.values[0],
                    'CP': df1.CP.values[0]}
        # Soil parameters to calculate
        agua_util = out_dict['CC'] - out_dict['PMP']
        lim_desec = 2.5*(out_dict['PMP']/out_dict['CC'] - 0.4)
        if lim_desec < 0.:
            lim_desec = 0.
        elif lim_desec > 1.:
            lim_desec = 1.
        alm_min = lim_desec * out_dict['PMP']
        ccd = out_dict['CC'] - alm_min
        umbral_perc = out_dict['PMP'] + 0.5*agua_util
        # Save new parameters in output
        out_dict['AU'] = agua_util
        out_dict['LD'] = lim_desec
        out_dict['ALM_MIN'] = alm_min
        out_dict['CCD'] = ccd
        out_dict['UI'] = umbral_perc

        return out_dict
    else:
        cnxn.close()
        print('############ ERROR ###############')
        print('---- -- Sin datos de Suelo -------')
        print('El cultivo ' + cultivo)
        print('No se realiza en la estacion: ' + idestacion)
        print( '##################################')
        exit()


def read_fenologia(idestacion, cultivo):
    '''
    This function reads the id of station and the crop and returns
    a DataFrame which index goes from 1-366 (Julian day) and contains a column
    name Kc, which gives the value of the crop Kc according to fenology from
    ora.mdb database.
    '''
    try:
        cnxn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(drv, db, pwd))
    except pyodbc.Error as err:
        logging.warn(err)
        print('La base NO esta en: ' + db)
        print('Si no, corregir codigo read_data_hist_mdb en oramdb_func.py')
    # End TRY
    id_cultivo = get_id_cultivo(cultivo)
    # End TRY
    # Select Fenology for specified crop
    SQL1 = '''
        SELECT * FROM EtapaFenologica
        WHERE Cultivo = {}
        '''.format(id_cultivo)
    df = pd.read_sql_query(SQL1, cnxn)
    # Select Patron KC for specified crop and station
    SQL1 = '''
        SELECT PatronKC FROM Balance
        WHERE Cultivo = {}
        AND Estacion = {}
        '''.format(id_cultivo, idestacion)
    aux_PatKC = pd.read_sql_query(SQL1, cnxn)
    if not aux_PatKC.empty:
        PatKC = aux_PatKC.loc[0,:].values[0]
        # Select Julian Days for specified crop
        SQL1 = '''
               SELECT * FROM FenologiaPorZona
               WHERE patronKc = {}
               '''.format(str(PatKC))
        FenZona = pd.read_sql_query(SQL1, cnxn)
        cnxn.close()
        df.rename(columns={'id':'idEtapa'}, inplace=True)
        resultado = pd.merge(df, FenZona, on='idEtapa')

        return resultado
    else:
        cnxn.close()
        print('############ ERROR ###############')
        print('------- Sin Fenologia -------')
        print('El cultivo ' + cultivo)
        print('No se realiza en la estacion: ' + idestacion)
        print( '##################################')
        exit()


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


if __name__ == "__main__":
    idestacion = '107'
    cultivo = 'S1-VII'
    tipo_bh = 'profundo'
    ds = read_soil_parameter(idestacion, cultivo, tipo_bh)
    print(ds)
    fen = read_fenologia(idestacion, cultivo)
    print(fen)
