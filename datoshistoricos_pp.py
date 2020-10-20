'''
This script works with the historic dataset between
1999-2010 for both CFSR extracted data and Observed data.

- The first part uses different programed functions to collect data
- The second part select one year to be used as a test function and the rest
of the data is used to calibrate.
- Finally it calculate and plot data of:
* ETP calculated with observed data for that year
* ETP calculated with model data for that selected year
* ETP calculated with corrected data for that selected year.

Plot comparisons/calculate statistics to evaluate.
'''
import sys
import glob
import os
import time
import pyodbc
import numpy as np
import pandas as pd
import datetime as dt

# Gamma Module from scipy
from scipy.stats import gamma
# ECDF function
from statsmodels.distributions.empirical_distribution import ECDF
#
import matplotlib.pyplot as plt
import matplotlib as mpl

from pandas.plotting import register_matplotlib_converters

def read_pp_mdb(t_est, idest, fi, ff):
    '''
    Lee precipitaciones en fechas indicadas
    '''
    # General parameters to read database
    drv = '{Microsoft Access Driver (*.mdb, *.accdb)}'
    pwd = 'pw'
    db = 'c:/Felix/ORA/base_datos/BaseNueva/ora.mdb'
    if t_est == 'SMN':
        SQL_q1 = '''
            SELECT Fecha, Precipitacion FROM DatoDiario
            WHERE Estacion = {}
            AND (((DatoDiario.Fecha)>=#{}#))
            AND (((DatoDiario.Fecha)<=#{}#))
            ORDER BY Fecha
            '''.format(idest, fi, ff)
    try:
        cnxn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(drv, db, pwd))
    except pyodbc.Error as err:
        logging.warn(err)
        print('La base NO esta en: ' + db)
        print('Si no, corregir codigo read_data_hist_mdb en oramdb_func.py')

    df1 = pd.read_sql_query(SQL_q1, cnxn)
    cnxn.close()
    df1 = df1.assign(month=pd.DatetimeIndex(df1.loc[:, 'Fecha']).month)
    df1.rename(columns={'Precipitacion': 'precip'}, inplace=True)
    return df1


def variables_a_trabajar(nombre, archivo, nens):
    '''
    '''
    df = pd.read_csv(archivo, sep=';', decimal=',',
                     header=0).drop(['Unnamed: 0'],axis=1)
    df.rename(columns={'fecha': 'Fecha'}, inplace=True)
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d')
    col = df.loc[:, df.columns[1]::]
    df[nombre] = col.mean(axis=1)
    df1 = df.loc[:, ['Fecha', nombre]]
    df2 = df.loc[:, ['Fecha', df.columns[nens]]]
    df1 = df1.assign(month=pd.DatetimeIndex(df1.loc[:, 'Fecha']).month)
    df2 = df2.assign(month=pd.DatetimeIndex(df2.loc[:, 'Fecha']).month)
    df2.rename(columns={df.columns[nens]: nombre}, inplace=True)

    return df1, df2


def calc_freq_pp(datos, ppmin):
    '''
    '''
    ind = np.array([e > ppmin if ~np.isnan(e) else False for e in datos],
                    dtype=bool)
    precdias = datos[ind]
    frec = 1. - 1.*precdias.shape[0]/datos.shape[0]

    return frec

def fit_gamma_param(df, xmin, mes, year_test='None', option=0):
    """
    """
    cdf_limite = .99999999
    if mes - 1 <= 0:
        cnd = [12, 1, 2]
    elif mes + 1 >= 13:
        cnd = [11, 12, 1]
    else:
        cnd = [mes - 1, mes, mes + 1]
    if year_test == 'None':
        datos = df.loc[df['month'].isin(cnd), 'precip'].values
    else:
        id_fm = np.logical_and(df.Fecha >= '01/01/'+str(year_test),
                               df.Fecha <= '12/31/'+str(year_test))
        # generate index to work in cnd and out of year considered.
        im_tot = np.logical_and(df['month'].isin(cnd), np.logical_not(id_fm))
        # extract data to generate the distribution of historical data.
        print(np.unique(pd.DatetimeIndex(df.loc[im_tot, 'Fecha']).year.to_numpy()))
        print(np.unique(pd.DatetimeIndex(df.loc[im_tot, 'Fecha']).month.to_numpy()))
        datos = df.loc[im_tot, 'precip'].values
    # Days with precipitacion
    in_dato = np.array([e > xmin if ~np.isnan(e) else False
                        for e in datos], dtype=bool)
    precdias = datos[in_dato]
    # Fit a Gamma distribution over days with precipitation
    param_gamma = gamma.fit(precdias, floc=0)
    gamma_cdf = gamma.cdf(np.sort(precdias), *param_gamma)
    gamma_cdf[gamma_cdf > cdf_limite] = cdf_limite
    if option == 0:
        return param_gamma
    else:
        return param_gamma, precdias, gamma_cdf

def fit_ecdf(df, xmin, mes, year_test='None', option=0):
    cdf_limite = .99999999
    if mes - 1 <= 0:
        cnd = [12, 1, 2]
    elif mes + 1 >= 13:
        cnd = [11, 12, 1]
    else:
        cnd = [mes - 1, mes, mes + 1]
    if year_test == 'None':
        datos = df.loc[df['month'].isin(cnd), 'precip'].values
    else:
        id_fm = np.logical_and(df.Fecha >= '01/01/'+str(year_test),
                               df.Fecha <= '12/31/'+str(year_test))
        # generate index to work in cnd and out of year considered.
        im_tot = np.logical_and(df['month'].isin(cnd), np.logical_not(id_fm))
        # extract data to generate the distribution of historical data.
        datos = df.loc[im_tot, 'precip'].values
    # Days with precipitacion
    in_dato = np.array([e > xmin if ~np.isnan(e) else False
                        for e in datos], dtype=bool)
    precdias = datos[in_dato]
    ecdf_var = ECDF(precdias)
    if option == 0:
        return ecdf_var, precdias
    else:
        return ecdf_var

#
# ------  Start the script ---------------
# $$$ Initial data to work
start = time.time()
# Archivo con datos historicos de la variable:
# precip, tmax, tmin, velviento, radsup, hr
nomvar = 'precip'
ens_mem = 1  # Miembro a utilizar como prueba
mes = 1  # Mes en el cual se realiza el analisis
tipo_est = 'SMN'
id_est = '107'
estacion = 'resistencia'
xm_min = 0.1
cdf_limite = .99999999
tipo_ajuste = 'Mult-Shift'
# Datos a utilizar
var_file = './datos/resistencia/data_final_' + nomvar + '.txt'
# d_var = Media ensamble de precipitacion --> Ajustar Gamma
# d_ens = Un miembro del ensamble con el que se construye el historico
# de precipitacion.
d_var, d_ens = variables_a_trabajar(nomvar, var_file, ens_mem)
d_obs = read_pp_mdb(tipo_est, id_est, '1/1/1999', '12/31/2010')

ppsincorr = []
ppcorr = []
ppcorr_o = []
ppcorr_m = []
for year_test in np.arange(1999, 2011):
    print('--------', year_test, '----------')
    id_fm = np.logical_and(d_ens.Fecha >= '01/01/'+str(year_test),
                           d_ens.Fecha <= '12/31/'+str(year_test))
    # data of year to work.
    prono_m = d_ens.loc[id_fm, 'precip'].values
    meses_m = d_ens.loc[id_fm, 'month'].values
    # Corregimos los valores del mes de interes
    prono = prono_m[meses_m == mes]
    ppsincorr.extend(prono)
    corregidos = prono_m[meses_m == mes]
    idc = np.logical_or(prono > xm_min, np.logical_not(np.isnan(prono)))
    corregidos[prono <= xm_min] = 0.
    corregidos[np.isnan(prono)] = np.nan
    if tipo_ajuste == 'GG':
        # Ajustamos una gamma a los valores con precipitacion y corregimos
        obs_gamma = fit_gamma_param(d_obs, 0.1, mes, year_test)
        mod_gamma = fit_gamma_param(d_var, xm_min, mes, year_test)
        p1 = gamma.cdf(prono[idc], *mod_gamma)
        p1[p1>cdf_limite] = cdf_limite
        corr_o = gamma.ppf(p1, *obs_gamma)
        corr_m = gamma.ppf(p1, *mod_gamma)
        corregidos[idc] = corregidos[idc] + (corr_o - corr_m)
    elif tipo_ajuste == 'EG':
        obs_gamma = fit_gamma_param(d_obs, 0.1, mes, year_test)
        mod_ecdf, mod_precdias = fit_ecdf(d_var, xm_min, mes, year_test)
        p1 = mod_ecdf(prono[idc])
        p1[p1>cdf_limite] = cdf_limite
        corr_o = gamma.ppf(p1, *obs_gamma)
        corr_m = np.nanquantile(mod_precdias, p1, interpolation='linear')
        corregidos[idc] = corregidos[idc] + (corr_o - corr_m)
    elif tipo_ajuste == 'Mult-Shift':
        obs_ecdf, obs_precdias = fit_ecdf(d_obs, 0.1, mes, year_test)
        mod_ecdf, mod_precdias = fit_ecdf(d_var, xm_min, mes, year_test)
        xm_mean = np.nanmean(mod_precdias)
        xo_mean = np.nanmean(obs_precdias)
        corr_factor = xo_mean/xm_mean
        corregidos[idc] = corregidos[idc]*corr_factor

    #corregidos[corregidos > d_obs.loc[:,'precip'].max()] = d_obs.loc[:,'precip'].max()
    ppcorr.extend(corregidos)
#
# Datos para graficar
obs_gamma, obs_precdias, obs_cdf = fit_gamma_param(d_obs, 0.1, mes, 'None', 1)
mod_gamma, mod_precdias, mod_cdf = fit_gamma_param(d_var, xm_min, mes, 'None', 1)
label_obs = r'$\alpha$ = {:.2f}, loc = {}, $\beta$ = {:.2f}'.format(obs_gamma[0], obs_gamma[1], obs_gamma[2])
label_mod = r'$\alpha$ = {:.2f}, loc = {}, $\beta$ = {:.2f}'.format(mod_gamma[0], mod_gamma[1], mod_gamma[2])

# Datos Observados para el periodo total
g_obs = gamma.cdf(np.sort(obs_precdias), *obs_gamma)
# Datos modelados para el periodo total
g_mod = gamma.cdf(np.sort(mod_precdias), *mod_gamma)
# Datos modelados corregidos para el periodo total
in_corr = np.array([e > xm_min if ~np.isnan(e) else False
                    for e in ppcorr], dtype=bool)
corr_precdias = np.array(ppcorr)[in_corr]

print(len(obs_precdias), len(mod_precdias), len(np.array(ppcorr)[in_corr]))
corr_gamma = gamma.fit(np.array(ppcorr)[in_corr], floc=0)
g_corr = gamma.cdf(np.sort(corr_precdias), *corr_gamma)
label_corr = r'$\alpha$ = {:.2f}, loc = {}, $\beta$ = {:.2f}'.format(corr_gamma[0], corr_gamma[1], corr_gamma[2])
"""
frec_modc = 1. - 1.*np.array(ppcorr)[in_corr].shape[0]/datos_m.shape[0]
print('min PP mod-corr: ', xm_min)
print('Frec. Dias PP: ', frec_modc)
in_corr = np.array([e > xo_min if ~np.isnan(e) else False
                    for e in ppcorr_o], dtype=bool)
corr_cdf_o = ECDF(np.array(ppcorr_o)[in_corr])
in_corr = np.array([e > xm_min if ~np.isnan(e) else False
                    for e in ppcorr_m], dtype=bool)
corr_cdf_m = ECDF(np.array(ppcorr_m)[in_corr])
"""
# Figura
fig, ax = plt.subplots(nrows=1, ncols=1, facecolor='white')
ax.plot(np.sort(obs_precdias), g_obs, 'b--', label='OBS: ' + label_obs)
ax.plot(np.sort(mod_precdias), g_mod, 'r--', label='MODEL: ' + label_mod)
ax.plot(np.sort(corr_precdias), g_corr, 'g--', label='MODEL-CORR: ' + label_corr)
"""
for val in prono:
    ax.plot([val, val], [0, 1], '--', color='yellow' )
for val in corregidos:
    ax.plot([val, val], [0, 1], '--', color='coral' )
"""
#ax.set_xlim([0, 20])
plt.title(estacion + ' para mes: ' + str(mes) + ' min pp:' + str(xm_min))
plt.legend()
#plt.show()
#plt.close()
plt.savefig('./' + '_'.join([nomvar, tipo_ajuste, str(mes), str(xm_min)]) + '.png', dpi=200)
end = time.time()
print(end - start)
