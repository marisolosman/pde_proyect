import os
import sys
import glob
import datetime as dt
import time
import multiprocess as mp

def llamado_funcion(variable, fecha):
    os.system('python operational_read_var.py ' + variable + ' ' + fecha.strftime('%Y-%m-%d'))
RUTA = '/home/osman/proyectos/pde_proyect/datos/datos_op/resistencia/'
#variable = sys.argv[1]
#fech = dt.datetime(2012, 2, 9)
#while (fech <= dt.datetime(2012 , 5, 1)):
#    if (fech.weekday()==0) | (fech.weekday()==3):
#        llamado_funcion(variable, fech)
#        fech += dt.timedelta(hours=24)
#    else:
#        fech += dt.timedelta(hours=24)
#tmax 28 12 2017
#llamado_funcion('tmax', dt.datetime(2017, 12, 28))
nombre = ['prate']
#nombre_files = ['tmax', 'tmin', 'radsup', 'velviento', 'precip', 'hrmean']
nombre_files = ['precip']
for i in range(2020, 2021):
    fech = dt.datetime(i+1, 3, 1)
    while (fech <= dt.datetime(i + 1 , 5, 1)):
        if (fech.weekday()==0) | (fech.weekday()==3):
            for j in [0]:
                if len(glob.glob(RUTA + fech.strftime('%Y%m%d') + '/' + nombre_files[j] + '_*.txt')) < 16:
                    print(fech.strftime('%Y-%m-%d'), nombre[j])
                    llamado_funcion(nombre[j], fech)
         #print('---termino la fecha ' + fecha.strftime('%Y-%m-%d') + ' en ' + str(time.time() - comienzo))
        fech += dt.timedelta(hours=24)




