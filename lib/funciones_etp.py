import numpy as np
import pandas as pd
import datetime as dt
import sys
sys.path.append('../mdb_process/')
from oramdb_func import get_latlon_mdb
from oramdb_func import get_medias_ETP

np.seterr(divide='ignore', invalid='ignore')
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
