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

def read_var_mdb(var, tipo, idest):
    '''
    Lee precipitaciones en fechas indicadas
    '''
    sys.path.append("./mdb_process/")
    from oramdb_func import read_data_hist_mdb
    df = read_data_hist_mdb(var, tipo, idest)
    df = df.assign(month=pd.DatetimeIndex(df.loc[:, 'Fecha']).month)
    if var == 'tmin':
        df.rename(columns={'Tmin': var}, inplace=True)
    elif var == 'tmax':
        df.rename(columns={'Tmax': var}, inplace=True)
    elif var == 'hr':
        df.rename(columns={'Humedad': var}, inplace=True)
    elif var == 'velviento':
        df.rename(columns={'Viento': var}, inplace=True)
    elif var == 'radsup':
        df.rename(columns={'Rs': var}, inplace=True)
    elif var == 'precip':
        df.rename(columns={'Precipitacion': var}, inplace=True)
    return df


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
    if nombre == 'tmax' or nombre == 'tmin':
        df1.loc[:, nombre] = df1.loc[:, nombre] - 273.
        df2.loc[:, nombre] = df2.loc[:, nombre] - 273.

    return df1, df2


def fit_ecdf(df, var, mes, year_test='None', option=0):
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
        datos = df.loc[df['month'].isin(cnd), var].values
    else:
        id_fm = np.logical_and(df.Fecha >= '01/01/'+str(year_test),
                               df.Fecha <= '12/31/'+str(year_test))
        # generate index to work in cnd and out of year considered.
        im_tot = np.logical_and(df['month'].isin(cnd), np.logical_not(id_fm))
        # extract data to generate the distribution of historical data.
        print(np.unique(pd.DatetimeIndex(df.loc[im_tot, 'Fecha']).year.to_numpy()))
        print(np.unique(pd.DatetimeIndex(df.loc[im_tot, 'Fecha']).month.to_numpy()))
        datos = df.loc[im_tot, var].values
    #
    ecdf_var = ECDF(datos)
    if option == 0:
        return ecdf_var, datos
    else:
        return ecdf_var


#
# ------  Start the script ---------------
# $$$ Initial data to work
start = time.time()
# Archivo con datos historicos de la variable:
# precip, tmax, tmin, velviento, radsup, hr
nomvar = 'hr'
ens_mem = 1  # Miembro a utilizar como prueba
mes = 1  # Mes en el cual se realiza el analisis
tipo_est = 'SMN'
id_est = '107'
estacion = 'resistencia'
cdf_limite = .99999999
# Datos a utilizar
var_file = './datos/resistencia/data_final_' + nomvar + '.txt'
# d_var = Media ensamble --> Ajustar ECDF
# d_ens = Un miembro del ensamble.
d_var, d_ens = variables_a_trabajar(nomvar, var_file, ens_mem)
d_obs = read_var_mdb(nomvar, tipo_est, id_est)

varsincorr = []
varcorr = []
for year_test in np.arange(1999, 2011):
    print('--------', year_test, '----------')
    id_fm = np.logical_and(d_ens.Fecha >= '01/01/'+str(year_test),
                           d_ens.Fecha <= '12/31/'+str(year_test))
    # data of year to work.
    prono_m = d_ens.loc[id_fm, nomvar].values
    meses_m = d_ens.loc[id_fm, 'month'].values
    # Corregimos los valores del mes de interes
    prono = prono_m[meses_m == mes]
    varsincorr.extend(prono)
    corregidos = prono_m[meses_m == mes]
    # Ajustamos ECDF con los datos historicos
    #fit_ecdf(df, var, mes, year_test='None', option=0)
    obs_ecdf, datos_o = fit_ecdf(d_obs, nomvar, mes, year_test)
    mod_ecdf, datos_m = fit_ecdf(d_var, nomvar, mes, year_test)
    p1 = mod_ecdf(corregidos)
    p1[p1 > cdf_limite] = cdf_limite
    corr_o = np.nanquantile(datos_o, p1, interpolation='linear')
    corr_m = np.nanquantile(datos_m, p1, interpolation='linear')
    corregidos = corregidos + (corr_o - corr_m)
    varcorr.extend(corregidos)
#
# Datos para graficar
obs_ecdf = fit_ecdf(d_obs, nomvar, mes, 'None', 1)
mod_ecdf = fit_ecdf(d_var, nomvar, mes, 'None', 1)
# Datos modelados corregidos para el periodo total
corr_ecdf = ECDF(varcorr)
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
ax.plot(obs_ecdf.x, obs_ecdf.y, 'b.', label='OBS')
ax.plot(mod_ecdf.x, mod_ecdf.y, 'r.', label='MODEL')
ax.plot(corr_ecdf.x, corr_ecdf.y, 'g.', label='MODEL-CORR')
plt.title(estacion + '; mes: ' + str(mes) + '; variable: ' + nomvar )
plt.legend()
#plt.show()
#plt.close()
plt.savefig('./' + '_'.join([nomvar, str(mes)]) + '.png', dpi=200)
end = time.time()
print(end - start)
