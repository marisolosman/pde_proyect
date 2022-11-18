import os
import sys
import glob
import datetime as dt
import time
import multiprocess as mp

def llamado_funcion(variable, fecha):
    os.system('python operational_read_var_par.py ' + variable + ' ' + fecha.strftime('%Y-%m-%d'))
RUTA = '/home/osman/proyectos/pde_proyect/datos/datos_op/ceres/'

nombre = ['tmax', 'tmin', 'dswsfc', 'wnd10m', 'prate', 'hrmean']
nombre_files = ['tmax', 'tmin', 'radsup', 'velviento', 'precip', 'hrmean']
for i in range(2011, 2021):
    fech = dt.datetime(i, 12, 1)
    while (fech <= dt.datetime(i + 1 , 5, 1)):
        if (fech.weekday()==0) | (fech.weekday()==3):
            comienzo = time.time()
            for j in [0]:
                if len(glob.glob(RUTA + fech.strftime('%Y%m%d') + '/' + nombre_files[j] + '_*.txt')) < 16:
                    llamado_funcion(nombre[j], fech)
        print('---termino la fecha ' + fech.strftime('%Y-%m-%d') + ' en ' + str(time.time() - comienzo))
        fech += dt.timedelta(hours=24)




