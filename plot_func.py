import os
import glob
import pandas as pd
import numpy as np

import seaborn as sbn
import matplotlib.pyplot as plt
import matplotlib as mpl


def defi_title(variable, lang):
    """
    Define titulo de grafico dada la variable
    """
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
            titulo = 'Radiacion (W/m2)'
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
            titulo = 'Radiation (W/m2)'

    return titulo


def get_xlim(variable):
    """
    Define x limits acoording to the variable
    """
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
        resultado = [0, 100]

    return resultado


def grafica_percentiles(df_mod, df_obs, in_di):
    """
    Funcion para graficar percentiles.
    Recibe un DataFrame como el generado
    por pdf_func.py tanto para OBS, como
    para CFS
    """
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


if __name__ == '__main__':
    of = '../pde_salidas/'
    of_p = 'figuras/'
    estac = 'resistencia'
    vari = 'tmax'
    tipo = 'CFS'
    dic0 = {'outf': of + of_p, 'estacion': estac, 'var':vari, 'type': tipo}
    for m in range(1, 13):
            dic0['mes'] = m
            n_csv = of + estac + '/percentiles_CFS' + '_' + vari + '.txt'
            df_CFS = pd.read_csv(n_csv, sep=';', decimal=',', header=0).drop(['Unnamed: 0'],axis=1)
            n_csv = of + estac + '/percentiles_OBS' + '_' + vari + '.txt'
            df_o = pd.read_csv(n_csv, sep=';', decimal=',', header=0).drop(['Unnamed: 0'],axis=1)
            grafica_percentiles(df_CFS, df_o, dic0)
