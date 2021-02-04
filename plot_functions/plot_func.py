import os
import glob
import pandas as pd
import numpy as np
import datetime as dt


import seaborn as sbn
import matplotlib.pyplot as plt
import matplotlib as mpl

from pandas.plotting import register_matplotlib_converters

from statsmodels.distributions.empirical_distribution import ECDF

register_matplotlib_converters()

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
    elif variable == 'hr':
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
    col_i = df_mod.columns[1]
    col = df_mod.loc[:, col_i::]
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


def grafica_distrib_pp(estacion, tipo, mes):
    '''
    Plots the distribution of precipitation according to
    tipo, where tipo is:
    GG --> Model = Gamma and Obs = Gamma
    EG --> Model = ECDF and Obs = Gamma
    '''
    #
    from scipy.stats import gamma
    from pdf_func import get_ecdf
    from pdf_func import calc_min_pp
    from statsmodels.distributions.empirical_distribution import ECDF
    #
    ecdf_m, datos_m, ecdf_o, datos_o = get_ecdf('precip', estacion, mes)
    # Trabajamos datos obs que son con distrib GAMMA
    xo_min, xm_min = calc_min_pp(estacion, mes)
    d_o_pp = np.logical_and(datos_o > xo_min, ~np.isnan(datos_o))
    obs_precdias = datos_o[d_o_pp]
    print(obs_precdias)
    ecdf_o_pp = ECDF(obs_precdias)
    pp_vals0 = np.arange(0, np.nanmax(obs_precdias) + 1.)
    obs_frecuencia = 1. - (1. * obs_precdias.shape[0] / datos_o.shape[0])
    obs_gamma = gamma.fit(obs_precdias, floc=0)
    g1 = gamma.pdf(pp_vals0, *obs_gamma)
    # Trabajamos datos modelo GG o EG
    if tipo == 'GG':
        xm_min = 0.1
        d_m_pp = np.logical_and(datos_m > xm_min, ~np.isnan(datos_m))
        mod_precdias = datos_m[d_m_pp]
        pp_vals1 = np.arange(0, np.nanmax(mod_precdias) + 1.)
        mod_frecuencia = 1. - (1. * mod_precdias.shape[0] / datos_m.shape[0])
        mod_gamma = gamma.fit(mod_precdias, floc=0)
        g2 = gamma.pdf(pp_vals1, *mod_gamma)
        g3 = gamma.cdf(np.sort(mod_precdias), *mod_gamma)
    elif tipo == 'EG':
        xm_min = 0.1
        d_m_pp = np.logical_and(datos_m > xm_min, ~np.isnan(datos_m))
        mod_precdias = datos_m[d_m_pp]
        mod_frecuencia = 1. - (1. * mod_precdias.shape[0] / datos_m.shape[0])
        ecdf_m_pp = ECDF(mod_precdias)
    bina = [0.2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180]
    # Comenzamos la figura 2 paneles
    sbn.set(style='ticks', palette='muted', color_codes=True,
            font_scale=0.8)
    fig, axes = plt.subplots(nrows=1, ncols=2, facecolor='white',
                             figsize=(10,4))
    # Histograma Observacion
    ax = axes[0]
    ax.hist(obs_precdias, bins=bina, density=True, rwidth=1)
    ax.plot(pp_vals0, g1, 'r-', linewidth=3, alpha=.6)
    ax.set_ylim([0., 0.25])
    ax.set_xlim([0., 200.])
    testo = 'shape = %.2f\nloc = %.2f\nscale = %.2f' %(obs_gamma)
    ax.annotate(s=testo, xy=(40,.2))
    ax.set_title('gamma fit observations')
    sbn.despine(ax=axes[0], offset=5, trim=True)
    # Histograma Modelo
    ax = axes[1]
    ax.hist(mod_precdias, bins=bina, density=True, rwidth=1)
    ax.set_title('Histogram model data')
    if tipo == 'GG':
        ax.plot(pp_vals1, g2, 'r-', linewidth=3, alpha=.6)
        testo = 'shape = %.2f\nloc = %.2f\nscale = %.2f' %(mod_gamma)
        ax.annotate(s=testo, xy=(40,.2))
        ax.set_title('gamma fit model')
    ax.set_ylim([0., 0.25])
    ax.set_xlim([0., 200.])
    sbn.despine(ax=axes[1], offset=5, trim=True)
    #
    outfolder = './datos/' + estacion + '/figuras/'
    os.makedirs(outfolder, exist_ok=True)
    fgnm =  outfolder + str(mes) + '_' + tipo + '_pp_histograma.jpg'
    plt.savefig(fgnm, dpi=200)
    plt.close(fig)


    # $$$$$$$$$$$$ Plot of ECDF $$$$$$$$$$$$$$$$$$$$
    sbn.set(style='ticks', palette='muted', color_codes=True,
            font_scale=0.8)
    fig, ax = plt.subplots(nrows=1, ncols=1, facecolor='white', figsize=(5,5))
    #fig, ax = plt.subplots(1, 1, figsize=(5,5))
    ax.plot(ecdf_o_pp.x, ecdf_o_pp.y, 'o', color='#1aba02', ms=2.5, label='OBS')
    if tipo == 'GG':
        ax.plot(np.sort(mod_precdias), g3, 'o', color='#ed2026',
                ms=2.5, label='CFS')
    elif tipo == 'EG':
        ax.plot(ecdf_m_pp.x, ecdf_m_pp.y, 'o', color='#ed2026',
                ms=2.5, label='CFS')
    ax.set_xlim([0., 200.])
    testo = u'Frecuencia días sin pp:\nOBS = %.2f\nCFS = %.2f' %(obs_frecuencia, mod_frecuencia)
    ax.annotate(s=testo, xy=(70,.4))
    ax.legend(loc='lower right', fancybox=True, prop={'size': 10},
              handletextpad=0.1)
    bbox_props = dict(boxstyle='round', fc='w', ec='0.5', alpha=0.9)
    sbn.despine(ax=ax, offset=5, trim=True)
    #
    fgnm =  outfolder + str(mes) + '_' + tipo + '_pp_ecdf.jpg'
    plt.savefig(fgnm, dpi=200)
    plt.close(fig)


def grafica_dispersion_etp(etp_o, etp_m, estacion, t_dato_m):
    '''
    Grafico de dispersion entre etp calculadas con modelo y observaciones
    considera que etp_o es un DataFrame que sale de la funcion etp_func
    '''
    from scipy import stats

    if 'ETP' in etp_o.columns and 'ETP' in etp_m.columns:
        x = etp_o.ETP.values
        y = etp_m.ETP.values
        # ---- Regresion Lineal ----
        i_nan = np.logical_and(~np.isnan(x), ~np.isnan(y))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x[i_nan], y[i_nan])
        print('r-squared:', r_value**2)
        x_reg = np.arange(1, 9)
        y_reg = slope*x_reg + intercept
        #
        sbn.set(style='ticks', palette='muted', color_codes=True,
                font_scale=0.8)
        fig, ax = plt.subplots(nrows=1, ncols=1, facecolor='white',
                               figsize=(4,4))
        ax.scatter(x, y, marker='.', label='Datos')
        ax.plot(x_reg, y_reg, 'r-', label='R-Squared: %.2f'%(r_value**2))
        ax.plot(x_reg, x_reg, 'g-', label='y = x')
        ax.set_title(estacion)
        # Eje X
        ax.set_xlabel('ETP FAO Obs (mm)')
        ax.set_xticks(range(1,9))
        # Eje Y
        ax.set_ylabel('ETP FAO Mod (mm)')
        ax.set_yticks(range(1,9))
        # Leyenda
        ax.legend(loc='upper left', fancybox=True, prop={'size': 9},
                  handletextpad=0.1)
        bbox_props = dict(boxstyle='round', fc='w', ec='0.5', alpha=0.9)
        #
        sbn.despine(ax=ax, offset=3, trim=True)
        #
        outfolder = './datos/' + estacion + '/figuras/'
        os.makedirs(outfolder, exist_ok=True)
        fgnm =  outfolder + 'dispersion_ETP_' + t_dato_m + '.jpg'
        plt.savefig(fgnm, dpi=200)
        plt.close(fig)
    else:
        print('ERROR No esta la variable ETP en el Dataframe')
        print(etp_o.columns)
        print(etp_m.columns)
        exit()


def grafico_KC(x, d_bis, d_nbis, z0, z1, y, x_label):
    '''
    '''
    fig, ax = plt.subplots(nrows=1, ncols=1, facecolor='white')
    ax.plot(d_bis, z0, '-', color='#1aba02', ms=3., alpha=0.8, label='bisiesto')
    ax.plot(d_nbis, z1, '-.', color='#3f12e3', ms=2.5, alpha=0.7, label='no bisiesto')
    ax.plot(x, y, 'o', color='#ed2026', ms=5.5, label='Valores Originales')
    # eje X
    ax.set_xticks(x)
    txt_dict = {'fontsize':7, 'verticalalignment': 'top','horizontalalignment': 'right'}
    ax.set_xticklabels(x_label, rotation=45, fontdict=txt_dict)
    ax.xaxis.grid(True, linestyle='--')
    # Set ticks on both sides of axes on
    ax.tick_params(axis='x', bottom=True, top=False, labelbottom=True, labeltop=False)
    # Rotate and align top ticklabels
    axT = ax.twiny()
    axT.set_xlim(ax.get_xlim())
    axT.tick_params(axis='x', bottom=False, top=True, labelbottom=False, labeltop=True)
    axT.set_xticks(x)
    axT.set_xticklabels(x, rotation=45, fontsize=7)
    # Eje y
    ax.set_yticks(y)
    ax.yaxis.grid(True, linestyle='--')
    # Leyenda
    ax.legend(loc='upper right', fancybox=True, prop={'size': 10},
              handletextpad=0.1)
    bbox_props = dict(boxstyle='round', fc='w', ec='0.5', alpha=0.9)
    plt.tight_layout()
    plt.show()


def plot_check_prono(almr, idest, nestacion, cultivo, tipo_bh):
    '''
    Function to review results from operation BH prognostic
    almr: Dataframe with the 30 prognostic variable (index has dates)
    ides: Id of station to retrieve data from correspondant soil.
    '''
    from oramdb_func import read_soil_parameter
    import matplotlib.dates as mdates

    # datos reales
    infile = '../pde_salidas/BH-ORA/balance_RESIS_FL40-45_S1-VII_NORTE.xls'

    df = pd.read_excel(infile, sheet_name='DatosDiarios')
    xo = df.Fecha
    yo = df['alm real'].values
    myfmt = mdates.DateFormatter('%d/%m')
    soil_p = read_soil_parameter(idest, cultivo, tipo_bh)
    x = almr.index
    y = almr.to_numpy()
    y_ave = np.nanmean(y, axis=1)
    x0 = x[1] - dt.timedelta(days=10)
    x1 = x[-1] + dt.timedelta(days=1)
    # Comenzamos con el grafico.
    fig, ax = plt.subplots(nrows=1, ncols=1, facecolor='white', figsize=(9,6))
    # --- Pronosticos
    ax.plot(x, y, color='#c7e9c0')
    ax.plot(x, y_ave, color='#006d2c', label='Promedio')
    # Valor real
    ax.plot(xo, yo, color='black', label='Observado')
    # --- Caracteristicas suelo
    ax.plot([x0, x1], soil_p['CC']*np.ones((2,1)), color='#6baed6')
    ax.plot([x0, x1], soil_p['PMP']*np.ones((2,1)), color='#de2d26')
    # --- Eje x
    ax.set_xlim([x0, x1])
    ax.set_xticks([x0, x[1], x[1] + dt.timedelta(days=10),\
                   x[1] + dt.timedelta(days=20), x[-1]])
    ax.xaxis.set_major_formatter(myfmt)
    ax.xaxis.set_minor_locator(mdates.DayLocator())
    ax.xaxis.grid(b=True, which='major', color='#bdbdbd', linestyle='--' )
    # --- Eje y
    ax.set_ylim([0, 1.2*soil_p['CC']])
    # --- Titulo
    ax.set_title('Seguimiento de reserva de agua en el suelo',
                 fontdict={'fontweight':'bold'})
    ax.text(x0 + dt.timedelta(days=1), 1.1*soil_p['CC'],
            'Resistencia - Soja primera (VII)', style='italic', fontsize=8,
            bbox={'facecolor': 'white', 'alpha': 0.5, 'pad': 10})
    # --- Leyenda
    ax.legend(loc='lower right', fancybox=True, prop={'size': 10},
              handletextpad=0.1)
    bbox_props = dict(boxstyle='round', fc='w', ec='0.5', alpha=0.9)
    plt.tight_layout()
    # Se guarda la figura
    outfolder = './datos/' + nestacion + '/bh/'
    os.makedirs(outfolder, exist_ok=True)
    fstr = x[1].strftime('%Y%m%d')
    fgnm =  outfolder + 'bh_prono_' + fstr + '_' + cultivo + '_qq_corr.jpg'
    plt.savefig(fgnm, dpi=200)
    plt.close(fig)


if __name__ == '__main__':
    # ----------------
    from pdf_func import calc_pdf_OBS
    # ----------------
    of = './datos/'
    of_p = 'figuras/'
    estac = 'resistencia'
    vari = 'hr'
    tipo = 'CFS'
    dic0 = {'outf': of + of_p, 'estacion': estac, 'var':vari, 'type': tipo}
    for m in range(1, 2):
            dic0['mes'] = m
            n_csv = of + estac + '/percentiles_CFS' + '_' + vari + '.txt'
            df_CFS = pd.read_csv(n_csv, sep=';', decimal=',', header=0).drop(['Unnamed: 0'],axis=1)
            n_csv = of + estac + '/percentiles_OBS' + '_' + vari + '.txt'
            df_o = pd.read_csv(n_csv, sep=';', decimal=',', header=0).drop(['Unnamed: 0'],axis=1)
            #grafica_percentiles(df_CFS, df_o, dic0)
    # . . . . . . . . . . . . . . . . . . . . . . . .
    # Datos del modelo
    of = './datos/'
    of_p = 'figuras/'
    estac = 'resistencia'
    vari = 'hr'

    dic0 = {'outf': of + of_p, 'estacion': estac, 'var':vari, 'type':'CFS'}

    # Datos para extraer observaciones
    idest = '107'
    dic1 = {'outfo': of, 'estacion': estac, 'iest': idest, 't_estac':'SMN',
            'var':vari, 'type':'OBS'}
    for m in range(1, 13):
        grafica_distrib_pp(estac, 'GG', m)
        grafica_distrib_pp(estac, 'EG', m)
        dic0['mes'] = m
        n_csv = of + estac + '/data_final' + '_' + vari + '.txt'
        df_CFS = pd.read_csv(n_csv, sep=';', decimal=',',
                             header=0).drop(['Unnamed: 0'],axis=1)
        df_OBS = calc_pdf_OBS(dic1)
        #grafica_ecdf(df_CFS, df_OBS, dic0)
