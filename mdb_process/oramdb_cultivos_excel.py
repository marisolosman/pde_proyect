import os
import glob
import pyodbc
import numpy as np
import pandas as pd
import datetime as dt

# General parameters to read excel tables
xlsf = '../datos/oramdb/'

def get_id_cultivo(cultivo):
    '''
    Obtains the ID_CULTIVO to work with other tables.
    The entry is the string that is used in the database:
    '''
    t_cult = pd.read_excel(xlsf + 'Cultivo.xlsx')
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
    usecols = ['ID', 'Estacion', 'Cultivo', 'NombreUnidad', 'PatronSuelo', 'Cultivo']
    df = pd.read_excel(xlsf + 'Balance.xlsx', usecols=usecols)
    df1 = df.loc[df.Estacion == int(idestacion)]
    PatSoil = df1.loc[df1.Cultivo == id_cultivo]
    if not PatSoil.empty:
        PatSuelo = int(PatSoil.PatronSuelo.values[0])
        if tipo_bh == 'superficial':
            ucols = ['Nombre', 'IdPatron', 'CC_sup', 'PMP_sup', 'CE_sup', 'CP_sup']
            da = pd.read_excel(xlsf + 'PatronSuelo.xlsx', usecols=ucols)
            da1 = da.loc[da.IdPatron == PatSuelo, ucols]
            da1.drop('IdPatron', axis=1, inplace=True)
            da1.rename(columns={'CC_sup':'CC', 'PMP_sup':'PMP', 'CE_sup':'CE',
                                'CP_sup':'CP'},
                       inplace=True)
        elif tipo_bh == 'profundo':
            ucols = ['Nombre', 'IdPatron', 'CC', 'PMP', 'CE', 'CP']
            da = pd.read_excel(xlsf + 'PatronSuelo.xlsx', usecols=ucols)
            da1 = da.loc[da.IdPatron == PatSuelo, ucols]
            da1.drop('IdPatron', axis=1, inplace=True)
        else:
            print( '############ ERROR ###############')
            print('El tipo de BH: ' + tipo_bh)
            print('NO esta implementado o NO existe para calcular.')
            print( '##################################')
            exit()
        out_dict = {'Nombre': da1.Nombre.values[0], 'CC': da1.CC.values[0],
                    'PMP': da1.PMP.values[0], 'CE': da1.CE.values[0],
                    'CP': da1.CP.values[0]}
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
    id_cultivo = get_id_cultivo(cultivo)
    # Select Fenology for specified crop
    df = pd.read_excel(xlsf + 'EtapaFenologica.xlsx')
    # Select Patron KC for specified crop and station
    ucols = ['PatronKC', 'Cultivo', 'Estacion']
    dg0 = pd.read_excel(xlsf + 'Balance.xlsx', usecols=ucols)
    dg1 = dg0.loc[dg0.Cultivo == id_cultivo]
    dg2 = dg1.loc[dg1.Estacion == int(idestacion)]
    aux_PatKC = dg2.loc[:, 'PatronKC']
    if not aux_PatKC.empty:
        PatKC = aux_PatKC.values[0]
        # Select Julian Days for specified crop
        dh0 = pd.read_excel(xlsf + 'FenologiaPorZona.xlsx')
        FenZona = dh0.loc[dh0.patronKc == PatKC]
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
    # Test de las funciones excel:
    idestacion = '107'  # Resistencia SMN
    tipo_bh = 'profundo'
    cultivo = 'S1-VII'
    print(get_id_cultivo(cultivo))
    print('---------------')
    a = read_soil_parameter(idestacion, cultivo, tipo_bh)
    print(a)
    print('---------------')
    b = read_fenologia(idestacion, cultivo)
    print(b)
