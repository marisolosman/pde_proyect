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

fecha = '20030217'
tipo_bh = 'profundo'
estacion = 'junin'
cultivo = 'TL'
exc_archivo = 'balance_JUN_ROJAS_TL_PERG_montecarlo.xls'
a = class_operativa(estacion, fecha, True, 'GG')
bh = class_bhora(a, cultivo, tipo_bh, 2003)
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
plt.savefig('./' + estacion + '_' + cultivo + '_' + fecha + '_GG' + '.jpg',
            dpi=200, bbox_inches='tight')
plt.close(fig)
