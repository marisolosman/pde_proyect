import os
import glob
import numpy as np
import pandas as pd
import datetime as dt

import matplotlib.pyplot as plt

def calc_percentil(muestra):
    """
    Calculate from 1 to 99 percentiles using the data
    in muestra. muestra must be an numpy array
    """
    percentiles = []
    for p in range(1, 100):
        percentiles.append(np.nanpercentile(muestra, p))

    return percentiles


def save_tabla_percentil(in_di, matdata):
    """
    Use matdata as the data with percetiles for each month,
    colected from three months around the one studied.
    This function generates a Pandas DataFrame and save it
    as a CSV.

    """
    columnas = ['Prct', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    tabla_percentil = pd.DataFrame(data=matdata, columns=columnas)
    f_name = in_di['outfo'] + in_di['estacion'] + '/percentiles_' +\
             in_di['type'] + '_' + in_di['var'] + '.txt'
    tabla_percentil.apply(pd.to_numeric, errors='ignore')
    tabla_percentil.to_csv(f_name, sep=';', decimal=',', float_format='%.2f')


def calc_pdf_CFS(in_di):
    """
    This function reads CSV generated by grib_func.py functions, that extracts
    the value of the variable for an ensemble of 4 members. The dictionary must
    contain at least the folder where the general output is, the name of the
    station and the variable to work.
    """
    #from statsmodels.distributions.empirical_distribution import ECDF

    # Check if keys are in input dictionary
    if all(llaves in in_di for llaves in ['outfo', 'estacion', 'var']):
        nfile = in_di['outfo'] + in_di['estacion'] +\
                '/data_final_' + in_di['var'] + '.txt'
        df = pd.read_csv(nfile, sep=';', decimal=',', index_col=0, header=0)
        ncol = in_di['var'] + '_00'
        col = df.loc[:, ncol::]
        df['ens_mean'] = col.mean(axis=1) - 273.
        df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')
        df['month'] = pd.DatetimeIndex(df['fecha']).month
        fmat = np.empty((99, 13))
        #print(fmat.shape)
        fmat.fill(np.nan)
        fmat[:, 0] = np.arange(1, 100)
        for mes in range(1, 13):
            if mes - 1 <= 0:
                cnd = [12, mes, mes + 1]
            elif mes + 1 >= 13:
                cnd = [11, 12, 1]
            else:
                cnd = [mes - 1, mes, mes + 1]
            datos = df[df['month'].isin(cnd)]
            # ecdf = ECDF(datos.ens_mean.values)
            prc = calc_percentil(datos.ens_mean.values)
            fmat[:, mes] = prc
        save_tabla_percentil(in_di, fmat)

    else:
        print('No estan todos los input en el diccionario de entrada')
        exit()


def calc_pdf_OBS(in_di):
    """
    This function reads database of ORA (ora.mdb), that extracts
    the value of the variable for specified station and variable.
    The dictionary must contain at least the folder where the db is,
    the idestacion (that is in ora.mdb) and the variable to work.
    """
    import pyodbc
    # from statsmodels.distributions.empirical_distribution import ECDF
    drv = '{Microsoft Access Driver (*.mdb, *.accdb)}'
    pwd = 'pw'
    cnxn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(drv,
                                                           in_di['dbf'], pwd))
    #cursor = cnxn.cursor()
    if in_di['var'] == 'precip':
        SQL_q = '''
            SELECT Fecha, Precipitacion FROM DatoDiario
            WHERE Estacion = {}
            AND (((DatoDiario.Fecha)>#1/1/1999#))
            AND (((DatoDiario.Fecha)<#12/31/2010#))
            '''.format(str(in_di['iest']))
        print('Hay que programar')
    elif in_di['var'] == 'tmin':
        SQL_q = '''
            SELECT Fecha, Tmin FROM DatoDiarioSMN
            WHERE Estacion = {}
            AND (((DatoDiarioSMN.Fecha)>#1/1/1999#))
            AND (((DatoDiarioSMN.Fecha)<#12/31/2010#))
            '''.format(str(in_di['iest']))
    elif in_di['var'] == 'tmax':
        SQL_q = '''
            SELECT Fecha, Tmax FROM DatoDiarioSMN
            WHERE Estacion = {}
            AND (((DatoDiarioSMN.Fecha)>=#1/1/1999#))
            AND (((DatoDiarioSMN.Fecha)<=#12/31/2010#))
            '''.format(str(in_di['iest']))

    df = pd.read_sql_query(SQL_q, cnxn)
    df.columns = ['fecha', 'variable']
    df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')
    df['month'] = pd.DatetimeIndex(df['fecha']).month
    print(df.head())
    fmat = np.empty((99, 13))
    fmat.fill(np.nan)
    fmat[:, 0] = np.arange(1, 100)
    for mes in range(1, 13):
        if mes - 1 <= 0:
            cnd = [12, mes, mes + 1]
        elif mes + 1 >= 13:
            cnd = [11, 12, 1]
        else:
            cnd = [mes - 1, mes, mes + 1]
        datos = df[df['month'].isin(cnd)]
        prc = calc_percentil(datos.variable.values)
        fmat[:, mes] = prc
    save_tabla_percentil(in_di, fmat)


if __name__ == '__main__':
    of = '../pde_salidas/'
    estac = 'resistencia'
    vari = 'tmin'
    tipo = 'CFS'
    dic0 = {'outfo': of, 'estacion': estac, 'var':vari, 'type': tipo}
    calc_pdf_CFS(dic0)

    db = 'c:/Felix/ORA/base_datos/BaseNueva/ora.mdb'
    idest = 107  # Resistencia
    vari = 'tmin'
    tipo = 'OBS'
    dic1 = {'outfo': of, 'estacion': estac, 'dbf': db,
            'iest': idest, 'var': vari, 'type':tipo}
    calc_pdf_OBS(dic1)
