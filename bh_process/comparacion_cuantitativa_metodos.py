import glob
import os
import sys
import time
import pandas as pd
import numpy as np
import datetime as dt
#
sys.path.append('c:/felix/ora/python_scripts/pde_proyect/lib/')
from class_operativa import class_operativa
from class_bhora import class_bhora
#Plot Libraries
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


def read_escenarios(archivo, tipo):
    df = pd.read_excel(archivo, sheet_name=u'DatosGráfico')
    x = pd.to_datetime(df[u'Década']).dt.to_pydatetime()
    if tipo == 'seco':
        y = df['Escenario seco'].to_numpy()
    elif tipo == 'normal':
        y = df['Escenario normal'].to_numpy()
    elif tipo == 'humedo':
        y = df['Escenario húmedo'].to_numpy()
    return x, y


def calc_media():
    archivo_t = '../datos/bhora_init/balance_RESIS_FL40-45_S1-VII_NORTE.xls'
    df = pd.read_excel(archivo_t, sheet_name='DatosDiarios')
    df1 = df.loc[(df.Fecha>='1999-01-01') & (df.Fecha<='2010-12-31'),:]
    almr_obs = df1['alm real'].values
    fecha_obs = df1['Fecha'].dt.to_pydatetime()
    dymo = [m.strftime('%d%m') for m in fecha_obs]
    auxdf = pd.DataFrame(index=np.arange(0, len(almr_obs)), data={'almr':almr_obs, 'dymo':dymo})
    mediaclima = auxdf.groupby(dymo).mean()
    return mediaclima


# $$$ Initial data to work
start = time.time()
# --------------------------------------------------------------------
calc_bias = True # True --> BIAS; False --> 1 - rmse/std
years = '2008_2009'
# BH-CLIM
carpeta = '../datos/datos_op/resistencia/'
estacion = 'resistencia'

tipo_bh = 'profundo'
cultivo = 'S1-VII'
# BHORA Escenarios
escenario = 'normal'
escenarios = '../datos/bhora_esce/2008-2009/*.xls'
archivos = glob.glob(escenarios)
# LA VerdA
archivo_t = '../datos/bhora_init/balance_RESIS_FL40-45_S1-VII_NORTE.xls'
df = pd.read_excel(archivo_t, sheet_name='DatosDiarios')
almr_obs = df['alm real'].values
fecha_obs = df['Fecha'].dt.to_pydatetime()

media_hist = calc_media()

# --- script principal ---
resumen = np.empty((30, 7))
resumen[:] = np.nan
i_res = 0
# ----- BHORA ESCENARIOS RESUMEN -----
for escenario in ['humedo', 'normal', 'seco']:
    print(escenario)
    bias = np.empty((len(archivos), 30))
    cldif = np.empty((len(archivos), 30))
    bias[:] = np.nan
    cldif[:] = np.nan
    for it, archivo in enumerate(archivos):
        x, y = read_escenarios(archivo, escenario)
        fx = x[np.logical_not(np.isnan(y))]
        fy = y[np.logical_not(np.isnan(y))]
        almr = np.squeeze(np.array([almr_obs[np.where(fecha_obs == fi)] for fi in fx]))
        if len(fy)>1:
            if calc_bias:
                bias[it, 0:len(fy[1:])] = (fy[1:] - almr[1:])
            else:
                climalmr = [media_hist.loc[fi.strftime('%d%m'),:].values[0] for fi in fx]
                bias[it, 0:len(fy[1:])] = (fy[1:] - almr[1:])**2
                cldif[it, 0:len(fy[1:])] = (almr[1:] - climalmr[1:])**2
    if calc_bias:
        resumen[:, i_res] = np.nanmean(bias, axis=0)
    else:
        rmse = np.sqrt(np.nanmean(bias, axis=0))
        print(rmse)
        std  = np.sqrt(np.nanmean(cldif, axis=0))
        print(std)
        resumen[:, i_res] = 1. - rmse/std
    i_res += 1
print(i_res)
# ----- BHCLIM RESUMEN -------

tcorr = ['GG', 'GG', 'Mult-Shift', 'GG']
icorr = [False, True, True, False]
bhcorr = [False, False, False, True]
fechas = [os.path.basename(c1) for c1 in glob.glob(carpeta + '200*')]
for correccion, tipo_corr, bhc in zip(icorr, tcorr, bhcorr):
    print(tipo_corr)
    bias = np.empty((len(fechas), 30))
    cldif = np.empty((len(fechas), 30))
    bias[:] = np.nan
    cldif[:] = np.nan
    for ix, fecha in enumerate(fechas):
        a = class_operativa(estacion, fecha, correccion, tipo_corr)
        c = class_bhora(a, cultivo, tipo_bh, bhc)
        almr = np.squeeze(np.array([almr_obs[np.where(fecha_obs == fi)] for fi in c.dtimes]))
        fx = np.nanmean(c.ALMR, axis=1) # media del ensamble
        if calc_bias:
            bias[ix, :] = (fx[1:] - almr[1:])
        else:
            climalmr = [media_hist.loc[fi.strftime('%d%m'),:].values[0] for fi in c.dtimes]
            bias[ix, :] = (fx[1:] - almr[1:])**2
            cldif[ix, :] = (almr[1:] - climalmr[1:])**2
    ###############
    if calc_bias:
        resumen[:, i_res] = np.nanmean(bias, axis=0)
    else:
        rmse = np.sqrt(np.nanmean(bias, axis=0))
        print(rmse)
        std  = np.sqrt(np.nanmean(cldif, axis=0))
        print(std)
        resumen[:, i_res] = 1. - rmse/std
    i_res += 1

print(i_res)

columnas = ['bhora-humedo', 'bhora-normal', 'bhora-seco', 'bhclim-SC',
            'bhclim-GG', 'bhclim-MultShift', 'bhclim-ALMR']
df = pd.DataFrame(data=resumen, index=np.arange(1, 31), columns=columnas)
if calc_bias:
    df.to_excel('./resumen_bias_' + years + '.xlsx')
else:
    df.to_excel('./resumen_rmse_' + years + '.xlsx')



# ---------------------------
end = time.time()
print(end - start)
