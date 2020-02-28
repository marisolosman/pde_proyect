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
import time

import numpy as np
import pandas as pd
import datetime as dt

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
    variables = ['Fecha', 'precip', 'tmax', 'tmin', 'radsup', 'velviento', 'hr']
    corr_var = {'Fecha': df.Fecha, 'precip': df.precip}
    for var in variables[2::]:
         df_corr = qq_correction(df.loc[:, ['Fecha', var]], estacion)
         corr_var[var] = df_corr[var + '_corr'].values
    resultado = pd.DataFrame(columns=variables, data=corr_var)

    return resultado

def gen_qq_corrected_precip(df, estacion):
    '''
    This function calibrate and returns data to calculate BH, ie:
    Fecha, precip, ETP
    '''
    variables = ['Fecha', 'precip', 'ETP']
    corr_var = {'Fecha': df.Fecha, 'ETP': df.ETP}
    pp_corre = qq_correction_precip(df.loc[:, ['Fecha', 'precip']],
                                    estacion, 'GG')
    corr_var['precip'] = pp_corre['precip_corr'].values

    resultado = pd.DataFrame(columns=variables, data=corr_var)

    return resultado

#
# ------  Start the script ---------------
# $$$ Initial data to work
start = time.time()

list_files = glob.glob('./datos/resistencia/data_final_*.txt')
ens_mem = 4
tipo_est = 'SMN'
id_est = '107'
estacion = 'resistencia'
cultivo = 'S1-VII'
tipo_bh = 'profundo'
year_test = 2007  # Use data from this year to test
# Datos a utilizar
ini_m = read_hist_cfsr(list_files, ens_mem)
ini_o = read_hist_obs(tipo_est, id_est)
index_fecha_m = np.logical_and(ini_m.Fecha >= '06/01/'+str(year_test),
                               ini_m.Fecha <= '06/30/'+str(year_test))
index_fecha_o = np.logical_and(ini_o.Fecha >= '06/01/'+str(year_test),
                               ini_o.Fecha <= '06/30/'+str(year_test))
df_m = ini_m.loc[index_fecha_m]
df_o = ini_o.loc[index_fecha_o]

fecha_inicial = df_m['Fecha'].iloc[0] - dt.timedelta(days=1)
yr_i = fecha_inicial.year
mo_i = fecha_inicial.month
dy_i = fecha_inicial.day

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
kwargs = {'debug':False, 'fecha_inicial': True, 'ini_date':dt.datetime(yr_i, mo_i, dy_i)}
datos_bh_o = etp_o.loc[:, ['Fecha', 'precip', 'ETP']]
# BH con Observaciones
dbh_o = run_bh_ora(datos_bh_o, id_est, cultivo, tipo_bh, **kwargs)
datos_bh_m = etp_m.loc[:, ['Fecha', 'precip', 'ETP']]
# BH con datos de Modelo
dbh_m = run_bh_ora(datos_bh_m, id_est, cultivo, tipo_bh, **kwargs)
datos_bh_mc = etp_mc.loc[:, ['Fecha', 'precip', 'ETP']]
# BH con datos de modelo corregido para calcular ETP
dbh_mc = run_bh_ora(datos_bh_mc, id_est, cultivo, tipo_bh, **kwargs)
# BH con datos de modelo corregido para calcular ETP y PP
datos_bh_mcpp = gen_qq_corrected_precip(etp_mc, estacion)
dbh_mc_pp = run_bh_ora(datos_bh_mcpp, id_est, cultivo, tipo_bh, **kwargs)


end = time.time()
print(end - start)

# ------ ## --------- ## --------- ## ---------- ## -----
# ------ Graficamos dispersion entre ETP ----------------
#grafica_dispersion_etp(etp_o, etp_m, estacion, 'modelo')
#grafica_dispersion_etp(etp_o, etp_mc, estacion, 'corregida')
