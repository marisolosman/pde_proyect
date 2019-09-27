import os
import glob
import pandas as pd
import numpy as np

import seaborn as sbn
import matplotlib.pyplot as plt
import matplotlib as mpl

from statsmodels.distributions.empirical_distribution import ECDF

def defi_title(variable, lang):
    '''
    Define titulo de grafico dada la variable
    '''
    titulo = ''
    if lang == 'Esp':
        if variable == 'tmin':
            titulo = u'Temperatura mínima (\u00b0C)'
        elif variable == 'tmax':
            titulo = u'Temperatura máxima (\u00b0C)'
        elif variable == 'prate':
            titulo = u'Precipitacion (mm)'
        elif variable == 'rh':
            titulo = u'Humedad relativa'
        elif variable == 'dswsfc':
            titulo = 'Radiacion (MJ/m2)'
        elif variable == 'wnd10m':
            titulo = u'Viento medio (m/s)'
    elif lang == 'Ing':
        if variable == 'tmin':
            titulo = u'Minimum Temperature (\u00b0C)'
        elif variable == 'tmax':
            titulo = u'Maximum Temperature (\u00b0C)'
        elif variable == 'prate':
            titulo = u'Precipitation (mm)'
        elif variable == 'rh':
            titulo = u'Relative Humidity'
        elif variable == 'dswsfc':
            titulo = 'Radiation (MJ/m2)'
        elif variable == 'wnd10m':
            titulo = u'Mean wind speed (m/s)'

    return titulo


def get_xlim(variable):
    '''
    Define x limits acoording to the variable
    '''
    resultado = [0, 100]
    if variable == 'tmin':
        resultado = [-5, 35]
    elif variable == 'tmax':
        resultado = [10, 45]
    elif variable == 'prate':
        resultado = [0, 40]
    elif variable == 'rh':
        resultado = [0, 100]
    elif variable == 'dswsfc':
        resultado = [0, 50]
    elif variable == 'wnd10m':
        resultado = [-1, 12]

    return resultado


def grafica_percentiles(df_mod, df_obs, in_di):
    '''
    Funcion para graficar percentiles.
    Recibe un DataFrame como el generado
    por pdf_func.py tanto para OBS, como
    para CFS
    '''
    yo = df_obs.iloc[:, 0].values  # Variable (Tmax, Tmin, PP, etc.)
    xo = df_obs.iloc[:, in_di['mes']].values  # Percentiles
    ym = df_mod.iloc[:, 0].values  # Variable (Tmax, Tmin, PP, etc.)
    xm = df_mod.iloc[:, in_di['mes']].values  # Percentiles
    sbn.set(style='ticks', palette='muted', color_codes=True,
            font_scale=0.8)
    fig, ax = plt.subplots(nrows=1, ncols=1, facecolor='white')
    ax.plot(xm, ym, 'o', color='#ed2026', ms=2.5, label='CFS')
    ax.plot(xo, yo, 'o', color='#1aba02', ms=2.5, label='OBS')
    # Eje X -------------------------------------------------------------
    lim_eje_x = get_xlim(in_di['var'])
    ax.set_xlim(lim_eje_x)
    ax.set_xlabel('Variable', fontsize=10)
    # Eje Y -------------------------------------------------------------
    ax.yaxis.grid(True, linestyle='--')
    ax.set_ylabel('Percentil', fontsize=10)
    #
    titu_plot = defi_title(in_di['var'], 'Esp')
    ax.set_title(titu_plot, fontsize=10)
    #
    ax.legend(loc='upper left', fancybox=True, prop={'size': 10},
              handletextpad=0.1)
    bbox_props = dict(boxstyle='round', fc='w', ec='0.5', alpha=0.9)
    #
    sbn.despine(ax=ax, offset=5, trim=True)
    # -----------------
    # Save Figure
    # -------------------
    outfolder = in_di['outf'] + '/' + in_di['estacion'] + '_plot/'
    os.makedirs(outfolder, exist_ok=True)
    fgnm = outfolder + 'percentil_' + in_di['var'] + '_' + str(in_di['mes']) + '.jpg'
    plt.savefig(fgnm, dpi=200)
    # Close figure
    plt.close(fig)


def grafica_ecdf(df_mod, df_o, in_di):
    '''
    Plots the Empirical Cumulative Distribution (ECDF)
    of the variable using the provided DataFrame
    '''
    # Seleccionamos el trimestre a trabajar segun el mes
    if in_di['mes'] - 1 <= 0:
        cnd = [12, 1, 2]
    elif in_di['mes'] + 1 >= 13:
        cnd = [11, 12, 1]
    else:
        cnd = [in_di['mes'] - 1, in_di['mes'], in_di['mes'] + 1]
    # -------------------------------------
    # Para las OBS
    df_o.columns = ['fecha', 'variable']
    df_o['fecha'] = pd.to_datetime(df_o['fecha'], format='%Y-%m-%d')
    df_o['month'] = pd.DatetimeIndex(df_o['fecha']).month
    fmat = np.empty((99, 13))
    fmat.fill(np.nan)
    fmat[:, 0] = np.arange(1, 100)
    datos_o = df_o[df_o['month'].isin(cnd)]
    ecdf_o = ECDF(datos_o.variable.values)
    # -------------------------------------
    # Para el modelo
    ncol = in_di['var'] + '_00'
    col = df_mod.loc[:, ncol::]
    if in_di['var'] == 'tmax' or in_di['var'] == 'tmin':
        df_mod['ens_mean'] = col.mean(axis=1) - 273.
    else:
        df_mod['ens_mean'] = col.mean(axis=1)
    df_mod['fecha'] = pd.to_datetime(df_mod['fecha'], format='%Y-%m-%d')
    df_mod['month'] = pd.DatetimeIndex(df_mod['fecha']).month
    datos = df_mod[df_mod['month'].isin(cnd)]
    ecdf_m = ECDF(datos.ens_mean.values)
    # ---------------------------------------
    # Seteamos los datos para el grafico
    yo = ecdf_o.y  # Variable (Tmax, Tmin, PP, etc.)
    xo = ecdf_o.x  #
    ym = ecdf_m.y  # Variable (Tmax, Tmin, PP, etc.)
    xm = ecdf_m.x  #
    # ---- Comenzamos a graficar -------------------------
    sbn.set(style='ticks', palette='muted', color_codes=True,
            font_scale=0.8)
    fig, ax = plt.subplots(nrows=1, ncols=1, facecolor='white')
    ax.plot(xm, ym, 'o', color='#ed2026', ms=2.5, label='CFS')
    ax.plot(xo, yo, 'o', color='#1aba02', ms=2.5, label='OBS')
    # Eje X -------------------------------------------------------------
    lim_eje_x = get_xlim(in_di['var'])
    ax.set_xlim(lim_eje_x)
    ax.set_xlabel('Variable', fontsize=10)
    # Eje Y -------------------------------------------------------------
    ax.yaxis.grid(True, linestyle='--')
    ax.set_ylabel('Percentil', fontsize=10)
    #
    titu_plot = defi_title(in_di['var'], 'Esp')
    ax.set_title(titu_plot, fontsize=10)
    #
    ax.legend(loc='upper left', fancybox=True, prop={'size': 10},
              handletextpad=0.1)
    bbox_props = dict(boxstyle='round', fc='w', ec='0.5', alpha=0.9)
    #
    sbn.despine(ax=ax, offset=5, trim=True)
    # -----------------
    # Save Figure
    # -------------------
    outfolder = in_di['outf'] + '/' + in_di['estacion'] + '_plot/'
    os.makedirs(outfolder, exist_ok=True)
    fgnm = outfolder + 'ecdf_' + in_di['var'] + '_' + str(in_di['mes']) + '.jpg'
    plt.savefig(fgnm, dpi=200)
    # Close figure
    plt.close(fig)


if __name__ == '__main__':
    # ----------------
    from pdf_func import calc_pdf_OBS
    # ----------------
    of = '../pde_salidas/'
    of_p = 'figuras/'
    estac = 'resistencia'
    vari = 'prate'
    tipo = 'CFS'
    dic0 = {'outf': of + of_p, 'estacion': estac, 'var':vari, 'type': tipo}
    for m in range(1, 13):
            dic0['mes'] = m
            n_csv = of + estac + '/percentiles_CFS' + '_' + vari + '.txt'
            df_CFS = pd.read_csv(n_csv, sep=';', decimal=',', header=0).drop(['Unnamed: 0'],axis=1)
            n_csv = of + estac + '/percentiles_OBS' + '_' + vari + '.txt'
            df_o = pd.read_csv(n_csv, sep=';', decimal=',', header=0).drop(['Unnamed: 0'],axis=1)
            grafica_percentiles(df_CFS, df_o, dic0)
    # . . . . . . . . . . . . . . . . . . . . . . . .
    # Datos del modelo
    of = '../pde_salidas/'
    of_p = 'figuras/'
    estac = 'resistencia'
    vari = 'prate'

    dic0 = {'outf': of + of_p, 'estacion': estac, 'var':vari, 'type':'CFS'}

    # Datos para extraer observaciones
    idest = '107'
    dic1 = {'outfo': of, 'estacion': estac, 'iest': idest, 't_estac':'SMN',
            'var':vari, 'type':'OBS'}
    for m in range(1, 13):
            dic0['mes'] = m
            n_csv = of + estac + '/data_final' + '_' + vari + '.txt'
            df_CFS = pd.read_csv(n_csv, sep=';', decimal=',',
                                 header=0).drop(['Unnamed: 0'],axis=1)
            df_OBS = calc_pdf_OBS(dic1)
            grafica_ecdf(df_CFS, df_OBS, dic0)
