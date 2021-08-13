import os
import sys
import glob
import datetime as dt
import time
import multiprocess as mp

def llamado_funcion(variable):
    os.system('python historical_read_var.py ' + variable)
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
#nombre = ['tmax', 'tmin', 'hrmean', 'wnd10m', 'prate', 'dswsfc']
nombre = ['hrmean', 'wnd10m', 'dswsfc']

#nombre_files = ['tmax', 'tmin', 'radsup', 'velviento', 'precip', 'hrmean']

for j in nombre:
    print(j)
    llamado_funcion(j)




