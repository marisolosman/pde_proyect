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
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches

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
    cdf_limite = .9999999
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
        #print(np.unique(pd.DatetimeIndex(df.loc[im_tot, 'Fecha']).year.to_numpy()))
        #print(np.unique(pd.DatetimeIndex(df.loc[im_tot, 'Fecha']).month.to_numpy()))
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
    cdf_limite = .9999999
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
#mes = 1  # Mes en el cual se realiza el analisis
tipo_est = 'SMN'
id_est = '107'
estacion = 'resistencia'
cdf_limite = .9999999
# Datos a utilizar
var_file = './datos/resistencia/data_final_' + nomvar + '.txt'
# d_var = Media ensamble de precipitacion --> Ajustar Gamma
# d_ens = Un miembro del ensamble con el que se construye el historico
# de precipitacion.
d_var, d_ens = variables_a_trabajar(nomvar, var_file, ens_mem)
d_obs = read_pp_mdb(tipo_est, id_est, '1/1/1999', '12/31/2010')
# pdf con figuras
archivo = './diagnostico_pp.pdf'
if os.path.isfile(archivo):
    os.remove(archivo)
pdf = PdfPages(archivo)
props = dict(boxstyle='round', facecolor='white', alpha=0.8)
meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
for xm_min in [0.1, 0.5, 1]:
    for tipo_ajuste in ['GG', 'EG', 'Mult-Shift']:
        fig, ejes = plt.subplots(nrows=4, ncols=3, sharey=True, sharex=True, facecolor='white')
        fig.set_size_inches(9, 10, forward=True)
        fig1, ejes1 = plt.subplots(nrows=4, ncols=3, sharey=True, sharex=True, facecolor='white')
        fig1.set_size_inches(11, 9, forward=True)
        for ax, ax1, mes, st_mes in zip(ejes.flatten(), ejes1.flatten(), np.arange(1, 13), meses):
            print(mes)
            ppsincorr = []
            ppcorr = []
            ppobs = []
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
                obsdelmes = d_obs.loc[id_fm, 'precip'].values[meses_m==mes]
                ppobs.extend(obsdelmes)
                corregidos = prono_m[meses_m == mes]
                # Corregimos 0's y NaN
                corregidos[prono <= xm_min] = 0.
                corregidos[np.isnan(prono)] = np.nan
                # Corregimos los mayores a xm_min y que no son NaN's
                idc = np.logical_and(prono > xm_min, np.logical_not(np.isnan(prono)))
                if tipo_ajuste == 'GG':
                    # Ajustamos una gamma a los valores con precipitacion y corregimos
                    obs_gamma = fit_gamma_param(d_obs, 0.1, mes, year_test)
                    mod_gamma = fit_gamma_param(d_var, xm_min, mes, year_test)
                    p1 = gamma.cdf(prono[idc], *mod_gamma)
                    p1[p1>cdf_limite] = cdf_limite
                    corr_o = gamma.ppf(p1, *obs_gamma)
                    corregidos[idc] = corr_o
                elif tipo_ajuste == 'EG':
                    obs_gamma = fit_gamma_param(d_obs, 0.1, mes, year_test)
                    mod_ecdf, mod_precdias = fit_ecdf(d_var, xm_min, mes, year_test)
                    p1 = mod_ecdf(prono[idc])
                    p1[p1>cdf_limite] = cdf_limite
                    corr_o = gamma.ppf(p1, *obs_gamma)
                    corregidos[idc] = corr_o
                elif tipo_ajuste == 'Mult-Shift':
                    obs_ecdf, obs_precdias = fit_ecdf(d_obs, 0.1, mes, year_test)
                    mod_ecdf, mod_precdias = fit_ecdf(d_var, xm_min, mes, year_test)
                    xm_mean = np.nanmean(mod_precdias)
                    xo_mean = np.nanmean(obs_precdias)
                    corr_factor = xo_mean/xm_mean
                    corregidos[idc] = corregidos[idc]*corr_factor
                # Corregir los valores maximos con los maximos observados?????
                # corregidos[corregidos > d_obs.loc[:,'precip'].max()] = d_obs.loc[:,'precip'].max()
                ppcorr.extend(corregidos)
            #------- year_test -----------
            # Datos para graficar
            obs_gamma, obs_precdias, obs_cdf = fit_gamma_param(d_obs, 0.1, mes, 'None', 1)
            mod_gamma, mod_precdias, mod_cdf = fit_gamma_param(d_var, xm_min, mes, 'None', 1)
            label_obs = '$\\alpha$ = {:.2f},\n loc = {},\n $\\beta$ = {:.2f}'.format(obs_gamma[0], obs_gamma[1], obs_gamma[2])
            label_mod = '$\\alpha$ = {:.2f},\n loc = {},\n $\\beta$ = {:.2f}'.format(mod_gamma[0], mod_gamma[1], mod_gamma[2])
            # Datos Observados para el periodo total
            g_obs = gamma.cdf(np.sort(obs_precdias), *obs_gamma)
            # Datos modelados para el periodo total
            g_mod = gamma.cdf(np.sort(mod_precdias), *mod_gamma)
            # Datos No Corregidos para el mes:
            in_corr = np.array([e > xm_min if ~np.isnan(e) else False
                                for e in ppsincorr], dtype=bool)
            scorr_precdias = np.array(ppsincorr)[in_corr]
            corr_gamma = gamma.fit(scorr_precdias, floc=0)
            g_scorr = gamma.cdf(np.sort(scorr_precdias), *corr_gamma)
            label_scorr = '$\\alpha$ = {:.2f},\n loc = {},\n $\\beta$ = {:.2f}'.format(corr_gamma[0], corr_gamma[1], corr_gamma[2])
            # Datos modelados corregidos para el periodo total
            in_corr = np.array([e > xm_min if ~np.isnan(e) else False
                                for e in ppcorr], dtype=bool)
            corr_precdias = np.array(ppcorr)[in_corr]
            corr_gamma = gamma.fit(corr_precdias, floc=0)
            g_corr = gamma.cdf(np.sort(corr_precdias), *corr_gamma)
            label_corr = '$\\alpha$ = {:.2f},\n loc = {},\n $\\beta$ = {:.2f}'.format(corr_gamma[0], corr_gamma[1], corr_gamma[2])
            # Frecuencia dias sin pp
            frec_sin_corr = calc_freq_pp(np.array(ppsincorr), xm_min)
            frec_con_corr = calc_freq_pp(np.array(ppcorr), xm_min)
            frec_obs = calc_freq_pp(np.array(ppobs), 0.1)
            text_frec = 'Frec. Dias sin PP\n obs: {:.2f},\n mod: {:.2f},\n corr: {:.2f}'.format(frec_obs, frec_sin_corr, frec_con_corr)
            # Figura 1
            ax.plot(np.sort(obs_precdias), g_obs, 'b--', label='OBS: ' + label_obs, zorder=1)
            ax.plot(np.sort(mod_precdias), g_mod, 'r--', label='MODEL: ' + label_scorr, zorder=1)
            ax.plot(np.sort(corr_precdias), g_corr, 'g--', label='MODEL-CORR: ' + label_corr, zorder=1)
            ax.set_title(st_mes, loc = "left", fontsize=9)
            ax.tick_params(axis='both', labelsize=8)
            ax.grid(color='gray', linestyle='--', zorder=0)
            ax.legend(loc=4, fontsize=6)
            # Figura 2
            bins =[0.1, 0.5, 1, 5, 10, 15, 20, 30, 50, 70, 100, 1000]
            lbin = ['[0.1,0.5)', '[0.5,1)', '[1,5)', '[5,10)', '[10,15)',
                    '[15,20)', '[20,30)', '[30,50)', '[50,70)', '[70,100)', '>100']
            y2,x2 = np.histogram(np.array(ppcorr)[np.logical_not(np.isnan(ppcorr))],
                                 bins=bins, density=False)
            y1,x1 = np.histogram(np.array(ppsincorr)[np.logical_not(np.isnan(ppsincorr))],
                                 bins=bins, density=False)
            ax1.bar(np.arange(len(bins)-1)-0.2, y1, width=0.4, color='b', zorder=1)
            ax1.bar(np.arange(len(bins)-1)+0.2, y2, width=0.4, color='orange', zorder=1)
            ax1.text(6, 60, text_frec, fontsize=9, ha='left', va='top', zorder=2, bbox=props)
            ax1.set_title(st_mes, loc = "left", fontsize=9)
            ax1.set_xticks(np.arange(len(bins)-1))
            ax1.set_xticklabels(lbin, horizontalalignment='right')
            ax1.tick_params(axis='x', labelsize=8, labelrotation=45)
            ax1.grid(color='gray', linestyle='--', zorder=0)
        # ------- meses ----------
        fig.subplots_adjust(left = 0.05, right = 0.95,
                            bottom = 0.05, top = 0.90,
                            wspace = 0.2, hspace = 0.4)
        fig1.subplots_adjust(left = 0.05, right = 0.95,
                             bottom = 0.11, top = 0.90,
                             wspace = 0.2, hspace = 0.4)
        fig.suptitle(estacion + ' utilizando pp > ' + str(xm_min) + ' Metodo: ' + tipo_ajuste)
        fig1.suptitle(estacion + ' utilizando pp > ' + str(xm_min) + ' Metodo: ' + tipo_ajuste)
        # Leyenda Figura 1
        patch0 = mpatches.Patch(color='b', label='MODEL SIN-CORR')
        patch1 = mpatches.Patch(color='orange', label='MODEL CORR ')
        fig1.legend(handles=[patch0, patch1], fontsize=9)
        # Guardamos figuras
        #fig.savefig('./resistencia_1.png'  ,dpi=200)
        #fig1.savefig('./resistencia_2.png'  ,dpi=200)
        pdf.savefig(fig)
        pdf.savefig(fig1)
    # ---------- tipo ajuste ------------
#-------- valor minimo de precipitacion ---------------------
pdf.close()
# ---------------------------
end = time.time()
print(end - start)
