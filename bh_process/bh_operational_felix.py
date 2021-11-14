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
# Datos INPUT
# carpeta = '/home/osman/proyectos/pde_proyect/datos/datos_op/resistencia/20081203/'

ini_camp = 2020
fecha = '20210307'
correccion = True
tipo_bh = 'profundo'

df = pd.read_csv('../datos/estaciones.txt', sep=';')
for index, row in df.loc[0:1, :].iterrows():
    estacion = row['nom_est']
    cultivo = row['cultivo']
    exc_archivo = row['archivo_in']
    print(estacion, cultivo)
    a = class_operativa(estacion, fecha, correccion, 'GG')
    for i in range(0, 16, 4):
        a.radsup[0, i:i + 4] = a.radsup[0, i]
        a.etp[0, i:i + 4] = a.etp[0, i]
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
            linewidth=2, zorder=3, label='Almacenaje pronosticado')
    plt.legend(bbox_to_anchor=(0.6, 1.02, 1., .102), loc=3)
    plt.savefig(estacion + '_test_felix.jpg', dpi=200, bbox_inches='tight')
    plt.close(fig)

    # FIGURA del Balance climatico #######
    f1 = '../datos/bhora_init/' + exc_archivo
    df = pd.read_excel(f1, sheet_name='DatosGráfico')
    x = pd.to_datetime(df[u'Década'])
    ys = df['Escenario seco'].to_numpy()
    yn = df['Escenario normal'].to_numpy()
    yh = df['Escenario húmedo'].to_numpy()
    # ------------
    fig, ax = campaign_plot(bh)
    ax.plot(x, ys, color='#008000', zorder=3, label='Escenario seco')
    ax.plot(x, yn, color='#ff6600', zorder=3, label='Escenario normal')
    ax.plot(x, yh, color='#0000ff', zorder=3, label=u'Escenario húmedo')
    plt.legend(bbox_to_anchor=(0.6, 1.02, 1., .102), loc=3)
    plt.savefig(estacion + '_bhclim_test_felix.jpg', dpi=200, bbox_inches='tight')
    plt.close(fig)
