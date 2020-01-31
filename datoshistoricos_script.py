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
import glob
import os

import numpy as np
import pandas as pd

from etp_func import CalcularETPconDatos
from oramdb_func import get_latlon_mdb
from pdf_func import (qq_correction, qq_correction_precip)
from procesadata_func import read_hist_cfsr
from procesadata_func import read_hist_obs
from pdf_func import qq_correction
from bhora_func import run_bh_ora

from plot_func import grafica_dispersion_etp
#
def gen_qq_corrected_df(df, estacion):
    '''
    This function applies a QQ-correction to each column:
    tmax, tmin, radsup, velviento and hr.

    Generates the dataframe and returned it
    '''
    #
    variables = ['Fecha', 'tmax', 'tmin', 'radsup', 'velviento', 'hr']
    corr_var = {'Fecha': df.Fecha}
    for var in variables[1::]:
         df_corr = qq_correction(df.loc[:, ['Fecha', var]], estacion)
         corr_var[var] = df_corr[var + '_corr'].values
    resultado = pd.DataFrame(columns=variables, data=corr_var)

    return resultado

#
# ------  Start the script ---------------
# $$$ Initial data to work
list_files = glob.glob('./datos/resistencia/data_final_*.txt')
ens_mem = 2
tipo_est = 'SMN'
id_est = '107'
estacion = 'resistencia'
cultivo = 'S1-VII'
tipo_bh = 'profundo'
year_test = 2007  # Use data from this year to test
# Datos a utilizar
ini_m = read_hist_cfsr(list_files, ens_mem)
ini_o = read_hist_obs(tipo_est, id_est)
df_m = ini_m.loc[ini_m.Fecha < '01/01/2009']
df_o = ini_o.loc[ini_o.Fecha < '01/01/2009']
# Calculamos ETP para datos historicos observados y modelados
etp_o = CalcularETPconDatos(df_o, id_est)
#print(etp_o.head())
etp_m = CalcularETPconDatos(df_m, id_est)
#print(etp_m.head())
df_mc = gen_qq_corrected_df(df_m, estacion)
#print(df_mc.head())
etp_mc = CalcularETPconDatos(df_mc, id_est)
#print(etp_mc.head())

# Calculamos BH para estos datos:
kwargs = {'debug':False}
datos_bh_o = etp_o.loc[:, ['Fecha', 'precip', 'ETP']]
dbh_o = run_bh_ora(datos_bh_o, id_est, cultivo, tipo_bh, **kwargs)
datos_bh_m = etp_m.loc[:, ['Fecha', 'precip', 'ETP']]
dbh_m = run_bh_ora(datos_bh_m, id_est, cultivo, tipo_bh, **kwargs)
datos_bh_mc = etp_mc.loc[:, ['Fecha', 'precip', 'ETP']]
dbh_mc = run_bh_ora(datos_bh_mc, id_est, cultivo, tipo_bh, **kwargs)
print(datos_bh_o.head())
print(datos_bh_m.head())
print(datos_bh_mc.head())
#
# # Seleccionamos los datos a utilizar
# index_fecha_hist_m = np.logical_or(df_m.Fecha < '01/01/'+str(year_test),
#                                    df_m.Fecha > '31/12/'+str(year_test))
# index_fecha_test_m = np.logical_and(df_m.Fecha >= '01/01/'+str(year_test),
#                                     df_m.Fecha <= '31/12/'+str(year_test))
# index_fecha_hist_o = np.logical_or(df_o.Fecha < '01/01/'+str(year_test),
#                                    df_o.Fecha > '31/12/'+str(year_test))
# index_fecha_test_o = np.logical_and(df_o.Fecha >= '01/01/'+str(year_test),
#                                     df_o.Fecha <= '31/12/'+str(year_test))
# #
# df_mh = df_m.loc[index_fecha_hist_m]
# print(df_mh.tail())
# df_oh = df_o.loc[index_fecha_hist_o]
# print(df_oh.tail())
# df_mt = df_m.loc[index_fecha_test_m]
# df_ot = df_o.loc[index_fecha_test_o]
# print(df_mt.head())
# print(df_ot.head())
# etp_o = CalcularETPconDatos(df_ot, id_est)
# print(etp_o.head())
# etp_m = CalcularETPconDatos(df_mt, id_est)
# print(etp_m.head())
# df_mt.reset_index(drop=True, inplace=True)
# df_mc = gen_qq_corrected_df(df_mt, estacion)
# print(df_mc.head(), df_mc.dtypes)
# etp_mc = CalcularETPconDatos(df_mc, id_est)
# print(etp_mc.head())
# ------ ## --------- ## --------- ## ---------- ## -----
# ------ Graficamos dispersion entre ETP ----------------
#grafica_dispersion_etp(etp_o, etp_m, estacion, 'modelo')
#grafica_dispersion_etp(etp_o, etp_mc, estacion, 'corregida')
