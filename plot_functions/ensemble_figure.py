
import pandas as pd
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
from matplotlib.dates import DateFormatter
from matplotlib.dates import MO, TU, WE, TH, FR, SA, SU
from matplotlib.ticker import MultipleLocator
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

def ensemble_plot_base():
    # Datos graficos
    archivo = '../datos/bhora_init/balance_RESIS_FL40-45_S1-VII_NORTE.xls'
    df = pd.read_excel(archivo, sheet_name='DatosDiarios')
    almr_obs = df['alm real'].values
    fecha_obs = df['Fecha'].dt.to_pydatetime()
    # Datos extras
    ds = pd.read_excel(archivo, sheet_name=u'DatosGráfico')
    PMP = pd.unique(ds['Punto de marchitez'])[0]
    CC = pd.unique(ds['Capacidad de campo'])[0]
    dh = [datetime(2009,2,17), datetime(2009,4,5), datetime(2009,4,5), datetime(2009,2,17)]
    eh = [datetime(2009,4,8), datetime(2009,4,17), datetime(2009,4,17), datetime(2009,4,8)]
    fechas_limite = [datetime(2008,11,25), datetime(2009,6,30)]
    # Grafico
    fig, ax = plt.subplots()
    fig.set_size_inches(8, 5)
    ax.plot(fecha_obs, almr_obs, 'k', lw=3, zorder=2)
    ax.plot(fechas_limite,[CC, CC], color=[51./255.,102./255.,255./255.],zorder=1)
    ax.plot(fechas_limite,[PMP, PMP], color=[255./255.,0,0],zorder=1)
    ax.fill(dh, [0,0,107,107], color=[255./255.,204./255.,0, 0.4], zorder=0)
    ax.fill(eh, [0,0,107,107], color=[0.,204./255.,1., 0.4], zorder=0)
    # Eje X
    ax.set_xlim(fechas_limite[0], fechas_limite[1])
    loc = mdates.WeekdayLocator(byweekday=(MO))
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(DateFormatter("%d/%b"))
    ax.tick_params(axis='x', which='major', labelsize=7, rotation=90)
    # Eje Y
    ax.set_ylim(0, 110)
    ax.set_ylabel(u'milímetros')
    #
    ax.xaxis.grid(True, linestyle='--', color='gray', alpha=0.3)
    ax.yaxis.grid(True, linestyle='--', color='gray', alpha=0.3)
    return fig, ax

#fig, ax = ensemble_plot_base()
#fig.savefig('test_base_figura.png', dpi=200)
