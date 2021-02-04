import numpy as np
import pandas as pd
#Plot Libraries
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

def figura_bias(df, titulo, colores, leyenda, estilo, ylimit):
    fig, ax = plt.subplots()
    for col, color, label, lineaest in zip(df.columns, colores, leyenda, estilo):
        ax.plot(df.index, df[col], color= color, label=label, ls=lineaest)
    # Generales del grafico
    ax.set_title(titulo, fontsize=13)
    ax.set_xlabel(u'Días de pronóstico', fontsize=11)
    ax.set_ylabel(u'mm', fontsize=11)
    # Eje X
    ax.xaxis.set_major_locator(FixedLocator([1, 5, 10, 15, 20, 25, 30]))
    ax.xaxis.set_minor_locator(FixedLocator(np.arange(1, 31)))
    ax.xaxis.grid(which='major')
    ax.xaxis.grid(which='minor', linestyle=':')
    # Eje Y
    ax.set_ylim(ylimit[0], ylimit[1])
    ax.yaxis.grid(linestyle='--')
    plt.tight_layout()  # Para que no quede tanto espacio en blanco
    ax.legend(loc='best')
    return fig, ax


df1 = pd.read_excel('./resumen_bias_2002_2003.xlsx', index_col=0)
df2 = pd.read_excel('./resumen_bias_2008_2009.xlsx', index_col=0)
df3 = pd.read_excel('./resumen_rmse_2002_2003.xlsx', index_col=0)
df4 = pd.read_excel('./resumen_rmse_2008_2009.xlsx', index_col=0)

colores = ['green', 'gray', 'brown', 'blue', 'red', 'orange', 'violet']
leyenda = ['Esc. Hum.', 'Esc. Norm.', 'Esc. Seco', 'BH-SC', 'BH-GG', 'BH-MuSh', 'BH-CAlm']
estilo = [':', ':', ':', '-', '-', '-', '-']

titulo = ' BIAS medio 2002-2003'
fig, ax = figura_bias(df1, titulo, colores, leyenda, estilo, [-20, 40])
plt.savefig('bias_2002_2003.png', dpi=200)
plt.close(fig)

titulo = ' BIAS medio 2008-2009'
fig, ax = figura_bias(df2, titulo, colores, leyenda, estilo, [-20, 40])
plt.savefig('bias_2008_2009.png', dpi=200)
plt.close(fig)

titulo = ' 1 - RMSE/STD 2002-2003'
fig, ax = figura_bias(df3, titulo, colores, leyenda, estilo, [-1, 1])
plt.savefig('rmse_2002_2003.png', dpi=200)
plt.close(fig)

titulo = ' 1 - RMSE/STD 2008-2009'
fig, ax = figura_bias(df4, titulo, colores, leyenda, estilo, [-1, 1])
plt.savefig('rmse_2008_2009.png', dpi=200)
plt.close(fig)
