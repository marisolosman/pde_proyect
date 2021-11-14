import glob
import os
import sys
import time
import pandas as pd
import numpy as np
import datetime as dt
# Librerias locales
sys.path.append('c:/felix/ora/python_scripts/pde_proyect/lib/')
from class_operativa import class_operativa
from class_bhora import class_bhora
sys.path.append('c:/felix/ora/python_scripts/pde_proyect/plot_functions/')
from ensemble_figure import ensemble_plot_base
#Plot Libraries
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

def genera_colores(b1):
    cs = ['#ccece6', '#fcc5c0', '#feb24c', '#c6dbef']
    cm = ['#13a84f', '#ba23b6', '#e64061', '#1f71c4']
    col_ens = np.empty(len(b1), dtype='U7')
    col_med = np.empty(len(b1), dtype='U7')
    col_ens[0::4] = cs[0]
    col_ens[1::4] = cs[1]
    col_ens[2::4] = cs[2]
    col_ens[3::4] = cs[3]
    col_med[0::4] = cm[0]
    col_med[1::4] = cm[1]
    col_med[2::4] = cm[2]
    col_med[3::4] = cm[3]
    return col_ens, col_med

# $$$ Initial data to work
start = time.time()
# --------------------------------------------------------------------
# Datos INPUT
carpeta = '../datos/datos_op/resistencia/'
estacion = 'resistencia'
fechas = [os.path.basename(c1) for c1 in glob.glob(carpeta + '200*')]
correccion = True
tipo_bh = 'profundo'
cultivo = 'S1-VII'

col_ens, col_med = genera_colores(fechas)

fig, ax = ensemble_plot_base()

for fecha, color1, color2 in zip(fechas, col_ens, col_med):
    a = class_operativa(estacion, fecha, correccion, 'GG')
    c = class_bhora(a, cultivo, tipo_bh)

    b = class_operativa(estacion, fecha, False)
    d = class_bhora(b, cultivo, tipo_bh)
    alex = np.nanmean(c.ALMR, axis=1) - np.nanmean(d.ALMR, axis=1)
    print(alex)
    #ax.plot(c.dtimes, c.ALMR, color=color1, zorder=2)
    ax.plot(c.dtimes, np.nanmean(c.ALMR, axis=1), color=color2, zorder=3)

plt.savefig('6_figura_correccion_BH-ALMR_LeadTime.png', dpi=200)
plt.close(fig)

# ---------------------------
end = time.time()
print(end - start)
