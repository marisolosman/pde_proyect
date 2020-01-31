import numpy as np
import datetime as dt
import calendar

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
