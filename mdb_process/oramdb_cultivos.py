import os
import glob
import pyodbc
import numpy as np
import pandas as pd
import datetime as dt

# General parameters to read database
drv = '{Microsoft Access Driver (*.mdb, *.accdb)}'
pwd = 'pw'
db = 'c:/Felix/ORA/base_datos/BaseNueva/ora.mdb'

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
            #print('##### Parametros BH - Superficial ' + cultivo + ' #####')
            SQL2 = '''
                   SELECT Nombre, CC_sup, PMP_sup, CE_sup, CP_sup FROM PatronSuelo
                   WHERE IdPatron = {}
                   '''.format(str(PatSoil.PatronSuelo.values[0]))
            df1 = pd.read_sql_query(SQL2, cnxn)
            df1.rename(columns={'CC_sup':'CC', 'PMP_sup':'PMP', 'CE_sup':'CE',
                                'CP_sup':'CP'},
                       inplace=True)
        elif tipo_bh == 'profundo':
            #print('##### Parametros BH - Profundo ' + cultivo + ' #####')
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
        out_dict['LD'] = lim_desec  # Limite desecamiento
        out_dict['ALM_MIN'] = alm_min  # ALM Minimo
        out_dict['CCD'] = ccd  # Cap. Campo Disponible
        out_dict['UI'] = umbral_perc  # Umbral de Percolacion

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

if __name__ == "__main__":
    import sys
    sys.path.append('../bh_process/')
    from bhora_func import get_KC
    # ------
    idestacion = '107'
    cultivo = 'S1-VII'
    tipo_bh = 'profundo'
    kwargs = {'plot': True}
    ds = read_soil_parameter(idestacion, cultivo, tipo_bh)
    print(ds)
    fen = read_fenologia(idestacion, cultivo)
    print(fen)
    get_KC(idestacion, cultivo, **kwargs)
