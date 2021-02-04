import glob
import os
import sys
import time
import pandas as pd
import numpy as np
import datetime as dt
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

def read_escenarios(archivo, tipo):
    df = pd.read_excel(archivo, sheet_name=u'DatosGráfico')
    x = pd.to_datetime(df[u'Década'])
    if tipo == 'seco':
        y = df['Escenario seco'].to_numpy()
    elif tipo == 'normal':
        y = df['Escenario normal'].to_numpy()
    elif tipo == 'humedo':
        y = df['Escenario húmedo'].to_numpy()
    return x, y

# $$$ Initial data to work
start = time.time()
# --------------------------------------------------------------------
# Datos INPUT
estacion = 'resistencia'
escenario = 'seco'
escenarios = '../datos/bhora_esce/2008-2009/*.xls'
archivos = glob.glob(escenarios)

col_ens, col_med = genera_colores(archivos)

fig, ax = ensemble_plot_base()

for archivo, color1, color2 in zip(archivos, col_ens, col_med):
    x, y = read_escenarios(archivo, escenario)
    ax.plot(x, y, color=color2, zorder=3)

plt.savefig('5_figura_escenario_' + escenario + '.png', dpi=200)

plt.close(fig)

# ---------------------------
end = time.time()
print(end - start)
