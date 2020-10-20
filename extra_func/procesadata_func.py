import os
import pandas as pd
import numpy as np
import datetime as dt


def extract_variable_file(archivo):
    '''
    '''
    principal = archivo.split('.')[0]  #sacamos el txt
    variable = principal.split('_')[-1]  # El ultimo es el nombre

    return variable


def gen_dataframe(archivo):
    '''
    Given a file, generates appropiate DataFrame
    '''
    columnas = ['Fecha', 'tmax', 'tmin', 'radsup', 'velviento', 'hr',
                'precip']
    # Se trabaja con el primer archivo
    df = pd.read_csv(archivo, sep=';', decimal=',', index_col=0, header=0)
    #
    DF1 = pd.DataFrame(columns=columnas, index=np.arange(0, len(df)))
    DF1['Fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')

    return DF1


def read_cfsr_hist_file(variable, estacion):
    '''
    Given a variable and station, retrieves the data from that file that comes
    from CFSR. The location is under:
    ./data/{estacion}/
    and the text is with the name:
    data_final_{variable}.txt
    '''
    lista_variables = ['Fecha', 'tmax', 'tmin', 'radsup', 'velviento', 'hr',
                       'precip']
    if variable in lista_variables:
        archivo = './datos/' + estacion + '/data_final_' + variable + '.txt'
        df = pd.read_csv(archivo, sep=';', decimal=',', index_col=0, header=0)
        df.rename(columns={'fecha': 'Fecha'}, inplace=True)
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d')
        #
        return df
    else:
        err_msg = '''
        ######### ERROR ############# \n
        la variable dada, no se encuentra en la lista\n
        La lista de variables posibles para CFSR es: \n
        '''
        print(err_msg)
        print(lista_variables)
        exit()


def read_hist_cfsr(l_archivos, miembro_ensamble):
    '''
    For specific station data, receives the list of files for historic data
    variables and generate/return a DataFrame with this data.
    txt files have this common format name:

    data_final_{variable}.txt

    where variable should be: radsup, precip, tmax, tmin, velviento y hr
    miembro_ensamble: value between 1 and 4  for historic data
    '''
    # Variables DataFrame salida
    if miembro_ensamble > 4:
        print('ERROR solo hay 4 ensambles en datos historicos.')
        print('Colocaste ', miembro_ensamble, ' exit()')
        exit()
    df = gen_dataframe(l_archivos[0])
    # Read one file to extract Date and length

    for filein in l_archivos:
        df0 = pd.read_csv(filein, sep=';', decimal=',', index_col=0, header=0)
        ens = df0.columns[miembro_ensamble]
        vari = extract_variable_file(os.path.basename(filein))
        if vari == 'radsup':
            df['radsup'] = df0[ens]
        elif vari == 'tmax':
            df['tmax'] = df0[ens] - 273.
        elif vari == 'tmin':
            df['tmin'] = df0[ens] - 273.
        elif vari == 'velviento':
            df['velviento'] = df0[ens]
        elif vari == 'hr':
            df['hr'] = df0[ens]
        elif vari == 'precip':
            df['precip'] = df0[ens]
        else:
            print('No se guardo la variable: ', vari)
    # End LOOP
    cols = ['Fecha', 'tmax', 'tmin', 'radsup', 'velviento', 'hr', 'precip']
    df = df[cols]

    return df


def read_hist_obs(tipo, idestacion):
    '''
    This function add all historic data from observations.
    $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    The observations are considered in the database in this PATH:
    c:/Felix/ORA/base_datos/BaseNueva/ora.mdb

    Caso contrario, genera ERROR!
    $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    '''
    from oramdb_func import read_data_hist_mdb

    tmax = read_data_hist_mdb('tmax', tipo, idestacion)
    tmin = read_data_hist_mdb('tmin', tipo, idestacion)
    velviento = read_data_hist_mdb('velviento', tipo, idestacion)
    precip = read_data_hist_mdb('precip', tipo, idestacion)
    radsup = read_data_hist_mdb('radsup', tipo, idestacion)
    humedad = read_data_hist_mdb('hr', tipo, idestacion)
    # Numero total de datos
    frames = [tmax, tmin, radsup, velviento, humedad, precip]
    fechas_hist = pd.date_range(start='1999-01-01', end='2010-12-31')
    n_data = len(fechas_hist)
    df = pd.DataFrame(index=np.arange(0, n_data), data={'Fecha': fechas_hist})
    for dfvar in frames:
        df = df.merge(dfvar, how='outer', on='Fecha')
    df.columns = ['Fecha', 'tmax', 'tmin', 'radsup', 'velviento',
                  'hr', 'precip']
    return df


if __name__ == "__main__":
    import glob
    from etp_func import CalcularETPconDatos
    from oramdb_func import get_latlon_mdb
    from pdf_func import (qq_correction, qq_correction_precip)

    list_files = glob.glob('./datos/resistencia/data_final_*.txt')
    test_df = read_hist_cfsr(list_files, 1)
    print(test_df.columns)
    print(test_df.head())
    #tmin_corr = qq_correction(test_df.loc[0:100, ['Fecha', 'tmin']], 'resistencia')
    #tmax_corr = qq_correction(test_df.loc[0:100, ['Fecha', 'tmax']], 'resistencia')
    #print(test_df.loc[0:100, ['Fecha', 'precip']])
    #pp_corr = qq_correction_precip(test_df.loc[32:40, ['Fecha', 'precip']], 'resistencia', 'EG')
    #print(hr_corr.head())
    #test_dfo = read_hist_obs('SMN', '107')
    #print(test_dfo.columns)
    #lati, loni = get_latlon_mdb('107')
    #test_df['hr'] = test_dfo['hr']
    #dfo = CalcularETPconDatos(test_df, lati)
    #print(dfo[dfo.Fecha == '2007-09-14'])
