import sys
sys.path.append('../lib/')
from class_operativa import class_operativa
from class_bhora import class_bhora
sys.path.append('../plot_functions/')
from operational_plots import campaign_plot

import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib
import multiprocessing as mp
import argparse
from pathos.multiprocessing import ProcessingPool as Pool

CORES = mp.cpu_count()
RUTA_FIGURAS = '/datos/osman/datos_pde_project/FIGURAS/'
# Instantiate the parser
parser = argparse.ArgumentParser(description='Plot forecast bh for stations')

# Required positional argument
#parser.add_argument('inicamp', type=int,
#                                        help='Year of begininning of campain')
# Optional positional argument
parser.add_argument('date', type=str, help='Date of IC in YYYYMMMDD')

# Switch
parser.add_argument('--correccion', action='store_true',
                                        help='Bias correct forecast')
# Optional argument
parser.add_argument('--method', type=str,
                                        help='Correction method')

args = parser.parse_args()

fecha = args.date

if args.correccion:
    method = args.method
else:
    method = 'SC'
fecha = dt.datetime.strptime(fecha, "%Y%m%d")
  
tipo_bh = 'profundo'
df = pd.read_csv('../datos/estaciones.txt', sep=';')

def PlotForecast(row):
    estacion = row['nom_est']
    cultivo = row['cultivo']
    exc_archivo = row['archivo_in']
    print(estacion, cultivo)
    a = class_operativa(estacion, fecha.strftime('%Y%m%d'), args.correccion, method)
    for i in range(0, 16, 4):
        a.etp[0, i:i + 4] = a.etp[0, i]
    if cultivo[0] == 'S' and fecha.month <= 7:
        ini_camp = fecha.year - 1
    else:
        ini_camp = fecha.year
    bh = class_bhora(a, cultivo, tipo_bh, ini_camp)
    bh.calc_min_hist()
    # FIGURA del Balance sin Correccion #######
    fig, ax = campaign_plot(bh)
    ## prono: intervalo intercuartil, maximo y minimo
    q25 = np.nanquantile(bh.ALMR, 0.25, axis=1)
    q75 = np.nanquantile(bh.ALMR, 0.75, axis=1)
    qmx = np.nanmax(bh.ALMR, axis=1)
    qmn = np.nanmin(bh.ALMR, axis=1)
    ax.fill_between(bh.dtimes, q25, q75, alpha=0.7, facecolor='#969696', zorder=2,
                    label=u'50% ensamble pronosticado')
    ax.fill_between(bh.dtimes, qmn, qmx, alpha=0.4, facecolor='#969696', zorder=2,
                    label=u'Min y Max del ensamble pronosticado')
    # prono: mediana del ensamble
    ax.plot(bh.dtimes, np.nanquantile(bh.ALMR, 0.5, axis=1), color='green',
            linewidth=2, zorder=3, label='Perspectiva Promedio')
    handles, labels = ax.get_legend_handles_labels()
    handles = handles[2: 4] + handles[0: 2]+ handles[4: 9]
    labels =  labels[2: 4] + labels[0: 2]  + labels[4: 9]
    ax.legend(handles, labels, bbox_to_anchor=(0.6, 1.02, 1., .102), loc=3)
    plt.savefig(RUTA_FIGURAS + estacion + '_' + cultivo + '_' +\
                fecha.strftime('%Y%m%d') + '_' + method + '.jpg', dpi=200, bbox_inches='tight')
    plt.close(fig)

    # FIGURA del Balance climatico #######
    f1 = bh.c1 + exc_archivo
    df = pd.read_excel(f1, sheet_name='DatosGráfico')
    x = pd.to_datetime(df[u'Década'])
    ys = df['Escenario seco'].to_numpy()
    yn = df['Escenario normal'].to_numpy()
    yh = df['Escenario húmedo'].to_numpy()
    # ------------
    fig, ax = campaign_plot(bh)
    ax.plot(x, ys, color='#ff6600', zorder=3, label='Escenario seco')
    ax.plot(x, yn, color='#008000',zorder=3, label='Escenario normal')
    ax.plot(x, yh, color='#0000ff', zorder=3, label=u'Escenario húmedo')
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, bbox_to_anchor=(0.6, 1.02, 1., .102), loc=3)
    plt.savefig(RUTA_FIGURAS + estacion + '_' + cultivo + '_' +\
                fecha.strftime('%Y%m%d') + '_bhclim.jpg', dpi=200, bbox_inches='tight')
    plt.close(fig)

pool = mp.Pool(CORES)
rows = [row for index, row in df.loc[0: 22].iterrows()]

rows = [i for i in rows if ((i['cultivo'][0] == 'S' and (fecha.month < 6 | fecha.month >=10)) |
        (i['cultivo'][0] == 'T' and fecha.month >= 5)) ]

results = [pool.map(PlotForecast, rows)]
#PlotForecast(df.loc[1])
pool.close()

