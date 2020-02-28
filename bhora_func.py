import numpy as np
import pandas as pd
import datetime as dt

def get_initial_condition(date_i):
    '''
    '''
    infile = '../pde_salidas/BH-ORA/balance_RESIS_FL40-45_S1-VII_NORTE.xls'

    df = pd.read_excel(infile, sheet_name='DatosDiarios')
    ci_0 = df.loc[df['Fecha'] == date_i]
    #print(ci_0)
    ALM0 = ci_0['alm sin min'].values[0]
    EXC0 = ci_0['exceso'].values[0]
    PER0 = ci_0['per'].values[0]
    ESC0 = ci_0['esc'].values[0]

    return ALM0, EXC0, PER0, ESC0


def get_KC(idestacion, cultivo, **kwargs):
    '''
    '''
    from oramdb_func import read_fenologia
    from scipy.interpolate import interp1d
    d_bis = np.arange(1, 367)
    d_nbis = np.arange(1, 366)
    if cultivo == 'P':  # Pradera referencia
        kc_bis = np.empty(len(d_bis))
        kc_nbis = np.empty(len(d_nbis))
        kc_bis[:] = 1.
        kc_nbis[:] = 1.
    elif cultivo == 'CN':  # Campo Natural
        kc_bis = np.empty(len(d_bis))
        kc_nbis = np.empty(len(d_nbis))
        kc_bis[:] = 0.75
        kc_nbis[:] = 0.75
    else:
        dfeno = read_fenologia(idestacion, cultivo)
        d_bis = np.arange(1, 367)
        d_nbis = np.arange(1, 366)
        kc_o = dfeno.loc[:, 'Kc'].values
        jul = dfeno.loc[:, 'juliano'].values
        nombres = dfeno.loc[:, 'Nombre'].values
        x_label = nombres[np.argsort(jul)]
        kc_obis = np.empty(len(d_bis))
        kc_obis[:] = np.nan
        kc_onbis = np.empty(len(d_nbis))
        kc_onbis[:] = np.nan
        # Vemos los puntos en eje X (dias) e Y (valores KC)
        # Los ordenamos y luego interpolamos linealmente
        x = np.sort(jul)
        y = kc_o[np.argsort(jul)]
        kc_bis = np.interp(d_bis, x, y, period=len(d_bis))
        kc_nbis = np.interp(d_nbis, x, y, period=len(d_nbis))
        if kwargs:
            from plot_func import grafico_KC
            grafico_KC(x, d_bis, d_nbis, kc_bis, kc_nbis, y, x_label)

    return d_bis, kc_bis, d_nbis, kc_nbis


def var_to_save(Nt, A0, E0, P0, ES0):
    '''
    '''
    ALM = np.empty(Nt)
    ALM[0] = A0
    ALM[1::] = np.nan
    EXC = np.empty(Nt)
    EXC[0] = E0
    EXC[1::] = 0.
    PER = np.empty(Nt)
    PER[0] = P0
    PER[1::] = np.nan
    ESC = np.empty(Nt)
    ESC[0] = ES0
    ESC[1::] = np.nan
    ETC = np.empty(Nt)
    ETC[:] = np.nan
    ALMR = np.empty(Nt)
    ALMR[:] = np.nan
    ETR = np.empty(Nt)
    ETR[:] = np.nan

    return ALM, EXC, PER, ESC, ETC, ALMR, ETR


def run_bh_ora(datos, idestacion, cultivo, tipo_bh, **kwargs):
    '''
    This function implements the Hidric Balance that is made in ORA.
    The function use as input a DataFrame and run it for all
    the dates that come with it using as initial condition a Balance made by
    program developed for the office.
    datos: DF that contains three columns: Fechas, ETP and precip
    idestacion: string with id station on ora.mdb
    cultivo: string with the grow to calculate balance
    '''
    from oramdb_func import read_soil_parameter
    import calendar

    print('############ Corriendo el BH - ORA ##############')
    # ----- Datos del suelo
    ds = read_soil_parameter(idestacion, cultivo, tipo_bh)
    # ----- Obtenemos los KC
    d_bis, kc_bis, d_nbis, kc_nbis = get_KC(idestacion, cultivo)
    # ----- Condiciones Iniciales
    # Esta fecha debiera ser un dia antes de la fecha de los datos
    if kwargs['fecha_inicial']:
        fecha_i = kwargs['ini_date']
        print('Fecha Inicial: ', fecha_i)
    else:
        fecha_i = dt.datetime(1998,12,31)
        print('Fecha inicial', fecha_i)
    ALM0, EXC0, PER0, ESC0 = get_initial_condition(fecha_i)
    # Colocamos memoria para guardar variables asociadas al BH
    # 0: es condicion inicial
    Nt = len(datos) + 1
    ALM, EXC, PER, ESC, ETC, ALMR, ETR = var_to_save(Nt, ALM0, EXC0, PER0, ESC0)
    datos.reset_index(drop=True, inplace=True)
    # --- Comenzamos a iterar en las fechas para las que hay que calcular el BH
    for d in np.arange(1, Nt):  # d goes for data to save
        # Datos necesarios para calculos:
        fecha = datos.loc[d-1, 'Fecha']
        juliano = int(fecha.strftime('%j'))
        if kwargs['debug']:
            print('Fecha ', fecha, 'Juliano: ', juliano)
        # ----- Calculos de Percolacion
        CI = ds['CC'] - ALM[d - 1]
        if ALM[d - 1] > ds['UI']:
            PER[d] = ds['CP'] * (ALM[d - 1] - ds['UI'])
        else:
            PER[d] = 0.
        if kwargs['debug']:
            print('CI: ', CI, 'Percolacion: ', PER[d])
        # ----- Calculos escorrentia
        PP = np.nanmax([datos.loc[d - 1, 'precip'], 0])
        SUM = PP - EXC[d - 1]
        if SUM > 0.:
            ESC[d] = (ds['CE']**2)*SUM*np.exp(-CI/SUM)
        else:
            ESC[d] = 0.
        if kwargs['debug']:
            print('PP: ', PP, 'SUM: ', SUM, 'Escorrentia: ', ESC[d])
        # ----- Calculos Precip efectiva
        PPE = PP - ESC[d]
        # ----- Calculos ETP Cultivo
        if calendar.isleap(fecha.year):
            if kwargs['debug']:
                print('bisiesto')
            kc = kc_bis[d_bis == juliano]
        else:
            kc = kc_nbis[d_nbis == juliano]
        ETP = datos.loc[d - 1, 'ETP']
        ETC[d] = kc*ETP
        if kwargs['debug']:
            print('KC: ', kc, 'ETP: ', ETP, 'ETC: ', ETC[d])
        # ----- Calculos de ALMACENAJE
        DIF = PPE - ETC[d]
        if DIF > 0.:
            ALM[d] = ALM[d - 1] + EXC[d - 1] + PPE - ETC[d] - PER[d]
            if ALM[d] > ds['CCD']:
                EXC[d] = ALM[d] - ds['CCD']
                ALM[d] = ds['CCD']
        else:
            if kwargs['debug']:
                print('dif menor a 0')
            aux = np.exp( (ds['CCD']**(-1) + 1.29*ds['CCD']**(-1.88)) * DIF )
            ALM[d] = (ALM[d - 1] + EXC[d - 1]) * aux - PER[d]
            if ALM[d] > ds['CCD']:
                EXC[d] = ALM[d] - ds['CCD']
                ALM[d] = ds['CCD']
        if kwargs['debug']:
            print('DIF: ', DIF, 'ALM: ', ALM[d], 'EXC: ', EXC[d])
        # -------- FIN CALCULOS BH -----------
        # Calculos salidas
        ALMR[d] = ALM[d] + ds['ALM_MIN']
        ETR[d] = - ALM[d] + ALM[d-1] - EXC[d] + EXC[d-1] + PP - ESC[d] - PER[d]
        if kwargs['debug']:
            print('ALMR: ', ALMR[d], 'ETR: ', ETR[d])
            print('----------------------------------------------')

    df = pd.DataFrame(index=np.arange(0,Nt))
    df = df.assign(Fecha=datos.Fecha)
    df = df.assign(ALM=ALM)
    df = df.assign(EXC=EXC)
    df = df.assign(PER=PER)
    df = df.assign(ESC=ESC)
    df = df.assign(ETC=ETC)
    df = df.assign(ALMR=ALMR)
    df = df.assign(ETR=ETR)

    return df


if __name__ == '__main__':
    from procesadata_func import read_hist_obs
    from etp_func import CalcularETPconDatos
    from oramdb_func import get_latlon_mdb
    from etp_func import man_Falt_ETP

    # ##############################################

    tipo_estacion = 'SMN'
    idestacion = '107'
    cultivo = 'S1-VII'
    tipo_bh = 'profundo'
    fecha_i = dt.datetime(2000,1,1)
    lati, loni = get_latlon_mdb(idestacion)
    dfo = read_hist_obs(tipo_estacion, idestacion)
    dfo_etp = CalcularETPconDatos(dfo, idestacion)
    print(dfo_etp.loc[dfo_etp.i_ETPm == 1,:])
    #datos_bh = dfo_etp.loc[0:2, ['Fecha', 'precip', 'ETP']]
    #print(datos_bh.describe())
    #print(len(datos_bh))
    #run_bh_ora(datos_bh, idestacion, cultivo, tipo_bh)
