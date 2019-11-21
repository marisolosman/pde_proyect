import os
import glob
import pyodbc
import numpy as np
import pandas as pd
import datetime as dt

'''
Modulo de funciones para
'''

def calc_percentil(muestra):
    """
    Calculate from 1 to 99 percentiles using the data
    in muestra. muestra must be an numpy array
    """
    percentiles = []
    for p in range(1, 100):
        percentiles.append(np.nanpercentile(muestra, p))

    return percentiles


def get_id_estacion(estacion):
    '''
    Read a csv file called:
    estaciones.txt
    That relates simple name with ID and type in ora.mdb
    '''
    df = pd.read_csv('./datos/estaciones.txt', sep=';')
    id = df['id_est'].loc[df['nom_est'] == estacion].values[0]
    tipo = df['tipo_est'].loc[df['nom_est'] == estacion].values[0]

    return id, tipo


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
    # Check if keys are in input dictionary
    if all(llaves in in_di for llaves in ['outfo', 'estacion', 'var']):
        nfile = in_di['outfo'] + in_di['estacion'] +\
                '/data_final_' + in_di['var'] + '.txt'
        df = pd.read_csv(nfile, sep=';', decimal=',', index_col=0, header=0)
        df.rename(columns={'fecha': 'Fecha'}, inplace=True)
        ncol = df.columns[1]
        col = df.loc[:, ncol::]
        if in_di['var'] == 'tmax' or in_di['var'] == 'tmin':
            df['ens_mean'] = col.mean(axis=1) - 273.
        else:
            df['ens_mean'] = col.mean(axis=1)
        # ---------------------------
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d')
        df['month'] = pd.DatetimeIndex(df['Fecha']).month
        fmat = np.empty((99, 13))
        fmat.fill(np.nan)
        fmat[:, 0] = np.arange(1, 100)
        for mes in range(1, 13):
            if mes - 1 <= 0:
                cnd = [12, 1, 2]
            elif mes + 1 >= 13:
                cnd = [11, 12, 1]
            else:
                cnd = [mes - 1, mes, mes + 1]
            datos = df[df['month'].isin(cnd)]
            #
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
    from oramdb_func import read_data_hist_mdb
    # -------------------
    df = read_data_hist_mdb(in_di['var'], in_di['t_estac'], in_di['iest'])
    df.columns = ['Fecha', 'variable']
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d')
    df['month'] = pd.DatetimeIndex(df['Fecha']).month
    fmat = np.empty((99, 13))
    fmat.fill(np.nan)
    fmat[:, 0] = np.arange(1, 100)
    for mes in range(1, 13):
        if mes - 1 <= 0:
            cnd = [12, 1, 2]
        elif mes + 1 >= 13:
            cnd = [11, 12, 1]
        else:
            cnd = [mes - 1, mes, mes + 1]
        datos = df[df['month'].isin(cnd)]
        prc = calc_percentil(datos.variable.values)
        fmat[:, mes] = prc
    save_tabla_percentil(in_di, fmat)
    # Devolvemos el total de datos historicos
    return df[['Fecha', 'variable']]


def get_ecdf(variable, estacion, mes):
    '''
    This function, retrieves the historical data of model and observations
    and returns the Empirical Cumulative Distribution Function (ECDF).
    This is made for the variable. It considerer that static data is in
    ./datos/estacion/ Folder and the database in
    c:/Felix/ORA/base_datos/BaseNueva/ora.mdb

    '''
    from statsmodels.distributions.empirical_distribution import ECDF
    from oramdb_func import read_data_hist_mdb
    from procesadata_func import read_cfsr_hist_file
    ##### Trabajo con datos de modelo #####
    df_m = read_cfsr_hist_file(variable, estacion)
    ret_var = variable
    ncol = df_m.columns[1]
    col = df_m.loc[:, ncol::]
    if variable == 'tmax' or variable == 'tmin':
        df_m['ens_mean'] = col.mean(axis=1) - 273.
    else:
        df_m['ens_mean'] = col.mean(axis=1)
    df_m = df_m.assign(month=pd.DatetimeIndex(df_m['Fecha']).month)
    # Seleccionamos segun mes y generamos el ECDF
    datos_m = df_m.loc[df_m.month == mes, 'ens_mean'].values
    ecdf_m = ECDF(datos_m)
    ##### Trabajo con datos de observacion #####
    id_est, tipo_est = get_id_estacion(estacion)
    df_o = read_data_hist_mdb(variable, tipo_est, id_est)
    df_o.columns = ['Fecha', 'variable']
    df_o = df_o.assign(month=pd.DatetimeIndex(df_o['Fecha']).month)
    # Seleccionamos segun mes y generamos el ECDF
    datos_o = df_o.loc[df_o.month == mes, 'variable'].values
    ecdf_o = ECDF(datos_o)

    return ecdf_m, datos_m, ecdf_o, datos_o


def qq_correction(df_m, estacion):
    '''
    This function receives dataframes of model correct the values
    using the quantile-quantile technique.
    The df_m DataFrame MUST contain two columns:
    Fecha: The date in a datetime format Pandas
    Variable: The values of the variable

    This function retrieves the historical values of model and observation
    and generate the ECDF for both of them.
    After this, for each value in df_m, it adds a new column, with the
    corrected value.

    Reference: Boe et al., 2007. 'Statistical and dynamical downscaling of the
    Seine basin climate for hydro-meteorological studies'
    '''
    # Check columns
    columnas = df_m.columns
    list2 = ['Fecha', 'tmax', 'tmin', 'radsup', 'velviento', 'hr']
    result =  any(elem in columnas  for elem in list2)
    if result and len(columnas) == 2:
        print(' ################# Correccion Q-Q ', columnas[-1],' #################')
        df_m = df_m.assign(month=pd.DatetimeIndex(df_m.loc[:, 'Fecha']).month)
        corrected_values = np.empty(len(df_m))
        corrected_values[:] = np.nan
        # Go for each row with data and make the correction according to month
        for index, row in df_m.iterrows():
            ecdf_m, datos_m, ecdf_o, datos_o = get_ecdf(columnas[-1],
                                                        estacion, row.month)
            sce_data = row[columnas[-1]]  #Last column is data, first is Fecha
            p = ecdf_m(sce_data)
            corr_o = np.nanquantile(datos_o, p, interpolation='linear')
            corr_m = np.nanquantile(datos_m, p, interpolation='linear')
            corrected_values[index] = corr_o
        # End of Loop
        #print(corrected_values)
        df_out = df_m.loc[:, [columnas[0], columnas[1]]].copy()
        df_out = df_out.assign(corregido=corrected_values)
        df_out.columns = ['Fecha', columnas[-1], columnas[-1] + '_corr']

        return df_out
    else:
        err_txt = '''
                     ########### ERROR ##############\n
        No estan todas las columnas para hacer correccion Q-Q con datos.\n
                                exit()\n
                     ################################

                  '''
        print(err_txt)
        exit()


def qq_correction_precip(df_m, estacion, tipo):
    '''
    This function receives dataframes of model correct the values
    using the quantile-quantile technique.
    The df_m DataFrame MUST contain two columns:
    Fecha: The date in a datetime format Pandas
    precip: The values of the variable precipitation

    This function retrieves the historical values of model and observation
    and generate the ECDF for both of them.
    After this, for each value in df_m, it adds a new column, with the
    corrected value.

    References:
    Boe et al., 2007. 'Statistical and dynamical downscaling of the
    Seine basin climate for hydro-meteorological studies'

    Ines et al., 2006. 'Bias correction of daily GCM rainfall
    for crop simulation studies'

    '''
    import math
    # Gamma Module from scipy
    from scipy.stats import gamma
    # ECDF function
    from statsmodels.distributions.empirical_distribution import ECDF
    # Check columns
    columnas = df_m.columns
    list2 = ['Fecha', 'precip']
    result =  all(elem in columnas  for elem in list2)
    if result and len(columnas) == 2:
        print(' ################# Correccion Q-Q Precip #################')
        df_m = df_m.assign(month=pd.DatetimeIndex(df_m.loc[:, 'Fecha']).month)
        corrected_values = np.empty(len(df_m))
        corrected_values[:] = np.nan
        # Parameter to CDF ()
        cdf_limite = .99999999
        limite_menor = 0.1
        # Go for each row with data and make the correction according to month
        for index, row in df_m.iterrows():
            pp_prono = row['precip']  # PP a corregir
            print('PP a corregir: ', pp_prono)
            # Two step correction for each data precipitation
            # #### Preliminary data to work ####
            ecdf_m, datos_m, ecdf_o, datos_o = get_ecdf('precip',
                                                        estacion, row.month)
            # Minimum value observed (NON-ZERO)
            xo_min = np.nanmin(datos_o[datos_o > 0])
            print('xo_min: ', xo_min)
            if xo_min <= 0 or math.isnan(xo_min):
                # if no minimum is found, use 0.1 as default
                xo_min = limite_menor
            # Days with precipitacion
            obs_precdias = datos_o[datos_o > xo_min]
            # Frequency
            obs_frecuencia = 1. * obs_precdias.shape[0] / datos_o.shape[0]
            print('obs_frecuencia: ', obs_frecuencia)
            # Fit a Gamma distribution over days with precipitation
            obs_gamma = gamma.fit(obs_precdias, loc=0)
            print('obs_gamma: ', obs_gamma)
            obs_cdf = gamma.cdf(np.sort(obs_precdias), *obs_gamma)
            obs_cdf[obs_cdf > cdf_limite] = cdf_limite
            # #### Correction of Frequency ####
            pobs = ecdf_o(xo_min)
            print('pobs: ', pobs)
            xm_min = np.nanquantile(datos_m, pobs)
            if xm_min <= 0 or math.isnan(xm_min):
                # if no minimum is found, use 0.1 as default
                xm_min = limite_menor
            print('xm_min: ', xm_min)
            if tipo == 'GG':
                # OBS --> Gamma / Model --> Gamma
                if pp_prono < xm_min:
                    pp_corr = 0.
                    print('PP corregida = ', pp_corr)
                    print(' ---------- Es menor al minimo --------------')
                elif math.isnan(pp_prono):
                    pp_corr = np.nan
                    print('PP corregida = ', pp_corr)
                    print(' ---------- Es NaN --------------------------')
                else:
                    # Fit gamma distribution with Model Data
                    mod_precdias = datos_m[datos_m > xm_min]
                    mod_gamma = gamma.fit(mod_precdias, loc=0)
                    print('mod_gamma: ', mod_gamma)
                    mod_cdf = gamma.cdf(np.sort(mod_precdias), *mod_gamma)
                    mod_cdf[mod_cdf > cdf_limite] = cdf_limite
                    # Corrected Value is F^-1(F(xi))
                    F_xi = gamma.cdf(pp_prono, *mod_gamma)
                    #print('F(x_i) = ', F_xi)
                    Fobs = gamma.ppf(F_xi, *obs_gamma)
                    #print(u'F^{-1}(F(x_i)) = ', Fobs)
                    pp_corr = Fobs
                    print('PP corregida = ', pp_corr)
                    print(' ---------- ', tipo, ' --------------------------')

            elif tipo == 'EG':
                # OBS --> Gamma / Model --> ECDF
                if pp_prono < xm_min:
                    pp_corr = 0.
                    print('PP corregida = ', pp_corr)
                    print(' ---------- Es menor al minimo --------------')
                elif math.isnan(pp_prono):
                    pp_corr = np.nan
                    print('PP corregida = ', pp_corr)
                    print(' ---------- Es NaN --------------------------')
                else:
                    # Fit gamma distribution with Model Data
                    mod_precdias = datos_m[datos_m > xm_min]
                    ecdf_m_pp = ECDF(mod_precdias)
                    # Corrected Value is F^-1(F(xi))
                    F_xi = ecdf_m_pp(pp_prono)
                    #print('F(x_i) = ', F_xi)
                    Fobs = gamma.ppf(F_xi, *obs_gamma)
                    #print(u'F^{-1}(F(x_i)) = ', Fobs)
                    pp_corr = Fobs
                    print('PP corregida = ', pp_corr)
                    print(' ---------- ', tipo, ' --------------------------')


        # End Of LooP
        #print(corrected_values)
        df_out = df_m.loc[:, [columnas[0], columnas[1]]].copy()
        df_out = df_out.assign(corregido=corrected_values)
        df_out.columns = ['Fecha', columnas[-1], columnas[-1] + '_corr']

        return df_out
    else:
        err_txt = '''
                     ########### ERROR ##############\n
No estan todas las columnas para hacer correccion Q-Q precipitacion con datos.\n
                                exit()\n
                     ################################

                  '''
        print(err_txt)
        exit()


if __name__ == '__main__':
    # Pequeñas instrucciones para calcular percentiles.
    of = './datos/'
    estac = 'resistencia'
    vari = 'hr'
    typo = 'CFS'
    dic0 = {'outfo': of, 'estacion': estac, 'var':vari, 'type': typo}
    calc_pdf_CFS(dic0)
    idest = '107'  # Resistencia
    vari = 'hr'
    typo = 'OBS'
    dic1 = {'outfo': of, 'estacion': estac, 'iest': idest, 't_estac': 'SMN',
            'var': vari, 'type':typo}
    calc_pdf_OBS(dic1)
