import numpy as np
import pandas as pd
import datetime as dt
import calendar
import os

from pdf_func import (qq_correction, qq_correction_precip)

def clas_decada(fechas):
    """
    Funcion para crear array que clasifica las fechas
    por decada diaria mensual.
    """
    #
    r_i = np.zeros(np.shape(fechas))
    r_d = []  #np.zeros(np.shape(fechas))
    years = np.unique([i.year for i in fechas])
    # print(len(years)*12*3)
    nindex = 1
    for yr in years:
        for mo in np.arange(1,13):
            i1 = np.logical_and(fechas >= dt.datetime(yr,mo,1),
                                fechas <= dt.datetime(yr,mo,10))
            i2 = np.logical_and(fechas >= dt.datetime(yr,mo,11),
                                fechas <= dt.datetime(yr,mo,20))
            u_day = calendar.monthrange(yr, mo)[1]
            i3 = np.logical_and(fechas >= dt.datetime(yr,mo,21),
                                fechas <= dt.datetime(yr,mo,u_day))
            r_i[i1] = 1
            r_i[i2] = 2
            r_i[i3] = 3
            r_d.append(dt.datetime(yr,mo,1))
            r_d.append(dt.datetime(yr,mo,11))
            r_d.append(dt.datetime(yr,mo,21))
            #nindex = nindex + 3

    return r_i, r_d


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


def gen_qq_corrected_precip(df, estacion, tipo, **kwargs):
    '''
    This function calibrate and returns data to calculate BH, ie:
    Fecha, precip, ETP
    '''
    variables = ['Fecha', 'precip', 'ETP']
    corr_var = {'Fecha': df.Fecha, 'ETP': df.ETP}
    pp_corre = qq_correction_precip(df.loc[:, ['Fecha', 'precip']],
                                    estacion, tipo, **kwargs)
    corr_var['precip'] = pp_corre['precip_corr'].values

    resultado = pd.DataFrame(columns=variables, data=corr_var)

    return resultado

def comparar_precip(fecha, pp_pron):
    '''
    Compare two dataframes of precip:
    mod: --> 16 ensambles crudos del Modelo
    mod_corr: --> 16 ensambles corregidos por QQ
    obs: --> Datos observados.
    '''
    import pyodbc
    from scipy import stats
    import matplotlib.pyplot as plt
    #
    drv = '{Microsoft Access Driver (*.mdb, *.accdb)}'
    pwd = 'pw'
    db = 'c:/Felix/ORA/base_datos/BaseNueva/ora.mdb'
    #
    estacion = 'resistencia'
    id_est = '107'
    tipo_estacion = 'SMN'
    carpeta_datos = './datos/'
    carpeta_prono = '../pde_salidas/'
    fecha_in = dt.datetime.strptime(fecha, '%Y-%m-%d')
    fold_prono = carpeta_prono + estacion + '/' + fecha_in.strftime('%Y%m%d') + '/'
    outfolder = carpeta_prono + 'extras/'
    os.makedirs(outfolder, exist_ok=True)

    #
    SQL_q1 = '''
        SELECT Fecha, Precipitacion FROM DatoDiario
        WHERE Estacion = {}
        AND (((DatoDiario.Fecha)>=#2/18/2009#))
        AND (((DatoDiario.Fecha)<=#3/19/2009#))
        ORDER BY Fecha
        '''.format(id_est)
    cnxn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(drv, db, pwd))
    pp_obs = pd.read_sql_query(SQL_q1, cnxn)
    cnxn.close()
    for i_ens in range(5, 6):
        df_pp = pd.DataFrame(index=np.arange(0, len(pp_pron)),
                             data={'Fecha': pp_pron.index,
                                   'precip': pp_pron.loc[:, i_ens].values})
        pp_corr = qq_correction_precip(df_pp, estacion, 'EG', **{'fix_val':1.})
        print(pp_corr)
        # Grafico de dispersion PP obs vs PP modelo y corregido
        x = pp_obs['Precipitacion'].to_numpy()
        y1 = pp_corr['precip'].to_numpy()
        y2 = pp_corr['precip_corr'].to_numpy()
        # regresion
        in1 = np.logical_and(~pd.isnull(x), ~pd.isnull(y1))
        in2 = np.logical_and(~pd.isnull(x), ~pd.isnull(y2))
        sl1, ite1, r1, p1, std1 = stats.linregress(x[in1], y1[in1])
        sl2, ite2, r2, p2, std2 = stats.linregress(x[in2], y2[in2])
        print('r-squared 1:', r1**2)
        print('r-squared 2:', r2**2)
        x_reg = np.arange(0, 100)
        y_reg1 = sl1*x_reg + ite1
        y_reg2 = sl2*x_reg + ite2
        #
        fig, ax = plt.subplots(nrows=1, ncols=2, facecolor='white', sharey=True,
                               sharex=True, figsize=(7,5))
        ax[0].scatter(x, y1, marker='s', label='Datos')
        #ax[0].plot(x_reg, y_reg1, 'r-', label='R-Squared: %.2f'%(r1**2))
        ax[0].plot(x_reg, x_reg, 'g--', label='y = x')
        ax[0].set_ylim(-5, 150)
        ax[0].set_xlim(-5, 150)
        ax[0].set_xlabel('Observacion')
        ax[0].set_ylabel('CFSR')
        ax[0].set(aspect='equal', adjustable='box')
        #
        ax[1].scatter(x, y2, marker='s', label='Datos')
        #ax[1].plot(x_reg, y_reg2, 'r-', label='R-Squared: %.2f'%(r1**2))
        ax[1].plot(x_reg, x_reg, 'g--', label='y = x')
        ax[1].set_ylim(-5, 150)
        ax[1].set_xlim(-5, 150)
        ax[1].set_xlabel('Observacion')
        ax[1].set_ylabel('CFSR-Corregida')
        ax[1].set(aspect='equal', adjustable='box')
        #
        fig.tight_layout()
        fgnm =  outfolder + 'dispersion_temp_' + str(i_ens) + '.jpg'
        plt.savefig(fgnm, dpi=200)
        plt.close(fig)
        #
        fig, ax0 = plt.subplots(nrows=1, ncols=1)
        colors = ['forestgreen', 'orange', 'mediumorchid']
        leg = ['obs', 'cfsr', 'cfsr-corr']
        x1 = [x, y1, y2]
        bina = [0.1, 10, 40, 70, 100, 130, 160, 220]
        ax0.hist(x1, bina, histtype='bar', color=colors, label=leg)
        ax0.legend(prop={'size': 10})
        ax0.set_title(u'Distribucion precipitaciones')
        ax0.set_ylim(0, 20)
        ax0.set_yticks(np.arange(0,21,2))
        ax0.set_xticks(bina)
        ax0.tick_params(which='both', labelsize=8)
        fig.tight_layout()
        fgnm =  outfolder + 'barras_temp_' + str(i_ens) + '.jpg'
        plt.savefig(fgnm, dpi=200)
        plt.close(fig)
        # -----
        df_comp = pd.DataFrame(index=np.arange(0, len(pp_pron)),
                               data={'Fecha': pp_pron.index,
                                     'pp-obs': x, 'pp-cfsr': y1,
                                     'pp-cfsr-corr': y2})
        print(df_comp.max())
        print(df_comp.loc[:,'pp-obs'::].sum())
        df_comp.to_excel(outfolder + str(i_ens) + '.xlsx')
