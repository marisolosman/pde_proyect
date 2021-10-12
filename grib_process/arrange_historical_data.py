import os
import sys
import glob
import datetime as dt
import time
import multiprocess as mp

def llamado_funcion(variable):
    os.system('python historical_read_var.py ' + variable)
nombre = ['tmax', 'tmin', 'hrmean', 'wnd10m', 'prate', 'dswsfc']

for j in nombre:
    print(j)
    llamado_funcion(j)




