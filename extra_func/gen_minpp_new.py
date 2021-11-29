import sys
# sys.path.append('c:/felix/ora/python_scripts/pde_proyect/lib/')
sys.path.append('../lib/')
from class_historico import class_historico
import numpy as np
import pandas as pd

'''
Este script genera un archivo excel con los minimos de precipitacion modelada
para cada estacion y cada mes.

El calculo de cada minimo se hace basado en las discusiones con Marisol Osman,
que permita tener un minimo de precipitacion mensual que mejor ajuste con lo que
se tiene en la distribucion de precipitacion observada en terminos de la frecuencia
de dias sin precipitacion.
'''
def select_data_period(df, mes):
    nomvar = 'precip'
    if mes - 1 <= 0:
        cnd = [12, 1, 2]
    elif mes + 1 >= 13:
        cnd = [11, 12, 1]
    else:
        cnd = [mes - 1, mes, mes + 1]
    cnd = [mes]
    m_hist = np.array([a.month for a in df.dtimes])
    ind_data = np.isin(m_hist, np.array(cnd))
    mask_o = np.logical_or(df.mask_obs[nomvar], ind_data)
    mask_m = np.logical_or(df.mask_mod[nomvar], ind_data)
    do = df.datos_obs[nomvar][mask_o]
    dm = df.datos_mod[nomvar][mask_m]
    return do, dm

def calc_freq_pp(datos, ppmin):
    '''
    '''
    ind = np.array([e > ppmin if ~np.isnan(e) else False for e in datos],
                    dtype=bool)
    precdias = datos[ind]
    frec = 1. - 1.*precdias.shape[0]/datos.shape[0]

    return frec


estaciones = ['concordia','junin', 'resistencia', 'rio_cuarto', 'trenque_lauquen',
              'venado_tuerto', 'parana', 'ceres', 'vmrs']
meses = np.arange(1, 13)
resumen = pd.DataFrame(index=meses, columns=estaciones)
for idx in range(31):
    print(idx)
    for estacion in estaciones:
        print(estacion)
        df = class_historico(estacion, idx)
        minimos_pp = np.empty(12)
        for mes in np.arange(1, 13):
            do, dm = select_data_period(df, mes)
            frec_o = calc_freq_pp(do, 0.1)
            dm = dm[~np.isnan(dm)]
            dm_sorted = np.sort(dm[dm!=0])
            pos_min = np.int(np.shape(dm_sorted)[0] - (1 - frec_o) * np.shape(dm)[0])
            ppmin_int = dm_sorted[pos_min-1]
            frec_m = calc_freq_pp(dm, ppmin_int)
            minimos_pp[mes-1] = np.round(ppmin_int, 2)
        resumen.loc[:,estacion] = minimos_pp
    resumen.to_excel('../datos/datos_hist/modelo/minimos_pp_' + '{:02d}'.format(idx) + '.xlsx')
