import numpy as np
import pandas as pd
import datetime as dt
import sys
sys.path.append('/home/osman/proyectos/pde_proyect/extra_func/')
from extras_func import clas_decada
'''
Listado de funciones para calcular ETP.
Considera como base un DataFrame (DF) de Pandas.
Dicho DF debe contener las siguientes columnas:

fecha, tmax, tmin, velocidad de viento, radiacion, humedad relativa
'''
# Definimos constantes usadas en todos los calculos
GS = 0.082
GAMMA = 0.067
ALFA = 0.23
SIGMA = 0.000000004903


def calcularDelta(diaJuliano):
    '''
    '''
    del_ta = 0.409 * np.sin(2. * np.pi * diaJuliano / 365. - 1.39)

    return del_ta


def calcularOmegaS(elatitud, delta):
    '''
    '''
    ome_ga = np.arccos(-np.tan(elatitud * np.pi / 180.) * np.tan(delta))

    return ome_ga


def calcularInsolacionMaxima(omega_s):
    '''
    '''
    I_Max = 24. * omega_s / np.pi

    return I_Max


def calcularDr(diaJuliano):
    '''
    '''
    d_r = 1. + 0.033 * np.cos(2. * np.pi * diaJuliano / 365.)

    return d_r


def calcularRa(diaJuliano, elatitud, delta, omega_s):
    '''
    '''
    r_a = 24 * 60 * GS * calcularDr(diaJuliano) / np.pi *\
         (omega_s * np.sin(elatitud * np.pi / 180.) * np.sin(delta) +\
          np.cos(elatitud * np.pi / 180.) * np.cos(delta) * np.sin(omega_s))

    return r_a


def calculaRSdeHeliofania(Heliofania, omega_s, Ra):
    '''
    '''
    r_s = (0.25 + 0.5 * Heliofania / calcularInsolacionMaxima(omega_s)) * Ra

    return r_s

def CalcularETPconDatos(df, idestacion):
    '''
    Using the columns of the DataFrame, calculates a column with the etp
    using the FAO formula.
    The variable df, MUST contain the following column names:
    'Fecha', 'tmax', 'tmin', 'radsup', 'velviento', 'hr'
    if any of these is not present, throws an error message and stop
    '''
    from oramdb_func import get_latlon_mdb

    # ----------------------------------

    list1 = df.columns
    list2 = ['Fecha', 'tmax', 'tmin', 'radsup', 'velviento', 'hrmean']
    result =  all(elem in list1  for elem in list2)
    try:
        Latitud, longi = get_latlon_mdb(idestacion)
    except:
        Latitud = -27
        longi = -59
    if result:
        #print(' ################# Calculando ETP #################')
        a_juliano = np.array(df['Fecha'].dt.strftime('%j').values,
                             dtype=np.float64)
        #### Valores extras
        dr = calcularDr(a_juliano)
        delta = calcularDelta(a_juliano)
        omega = calcularOmegaS(Latitud, delta)
        Ra = calcularRa(a_juliano, Latitud, delta, omega)

        #### Viento 10m --> 2m -- 0.75 constante para pasar de 10m --> 2m
        viento2 = 0.75 * df.velviento

        # CALCULA TENSION DE VAPOR Y PENDIENTE DE SU CURVA
        Temp = 0.5 * (df.tmax + df.tmin)
        ES = 0.6108 * np.exp((17.27 * Temp) / (Temp + 237.3))
        EA = ES * df.hrmean / 100.
        Pend = 4098. * ES / np.power((Temp + 237.3), 2)

        ### CALCULA LA RADIACION RN
        RSO = 0.75 * Ra;
        RNS = (1. - ALFA) * df.radsup;
        dAux = (np.power(df.tmax + 273., 4) + np.power(df.tmin + 273., 4)) / 2.
        RNL = SIGMA * dAux * (0.34 - 0.14 * np.sqrt(EA)) *\
             (1.35 * df.radsup / RSO - 0.35)
        RN = RNS - RNL

        ### CALCULA ETP en mm
        n1 = 0.408*Pend*RN + GAMMA*(900. / (Temp + 273.))*viento2*(ES - EA)
        n2 = Pend + GAMMA * (1. + 0.34 * viento2)
        ETP = (n1/n2).to_numpy()
        in_etp = np.array([e < 0. if ~np.isnan(e) else False for e in ETP],
                           dtype=bool)
        ETP[ in_etp ] = 0.
        df = df.assign(ETP=ETP)
        df = df.assign(i_ETPm=np.isnan(df.ETP.values))
        df0 = man_Falt_ETP(df, idestacion)

        return df0

    else :
        print(list1)
        print(list2)
        err_txt = '''
                     ########### ERROR ##############\n
        No estan todas las columnas para calcular ETP con datos.\n
                    exit()\n
                     ################################

                  '''
        print(err_txt)
        exit()


def man_Falt_ETP(d_etp, idestacion):
    '''
    This function give the Monthly mean to dates where there was no possible
    to calculate the ETP (in case is missing).
    '''
    import datetime as dt
    from oramdb_func import get_latlon_mdb
    from oramdb_func import get_medias_ETP

    t_etp = get_medias_ETP(idestacion)
    # Get index of NaN Values for ETP
    i_nan = np.isnan(d_etp.ETP.values)
    r_i, r_d = clas_decada(d_etp['Fecha'].dt.to_pydatetime())
    d_etp = d_etp.assign(mes=d_etp['Fecha'].dt.month)
    d_etp = d_etp.assign(decada=r_i)
    for m1 in np.arange(1, 13):
        for de1 in np.arange(1, 4):
            i_deca = np.logical_and(d_etp.mes == m1, d_etp.decada == de1)
            i_deca_t = np.logical_and(t_etp.Mes == m1, t_etp.Decada == de1)
            valor_etp = t_etp.loc[i_deca_t, 'ETPMedia'].values[0]
            d_etp.loc[i_nan & i_deca, 'ETP'] = valor_etp

    d_etp = d_etp.drop(columns=['mes', 'decada'])

    return d_etp
