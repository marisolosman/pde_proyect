import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

'''
df = df.assign(juliano=df['Fecha'].dt.dayofyear)
minimos = df.groupby('juliano').min()
almr_min = minimos['alm real'].to_numpy()
jul_min = np.arange(1,367)
yri = self.fecha_inicio_plot.year
jui = self.fecha_inicio_plot.timetuple().tm_yday
yrf = self.fecha_fin_plot.year
juf = self.fecha_fin_plot.timetuple().tm_yday
feh = pd.date_range(self.fecha_inicio_plot, self.fecha_fin_plot)
if jui > juf:# e.g 340 y 120 (campaña 2002-2003)
    ju1 = dt.datetime(yri,12,31).timetuple().tm_yday
    alm1 = almr_min[jui-1:ju1]
    alm2 = almr_min[0:juf]
    al_min = np.hstack([alm1,alm2])
if jui < juf:
    alm1 = almr_min[jui-1:juf]
    al_min = alm1
'''

estacion = 'junin'
c1 = '../datos/bhora_init/'
df = pd.read_csv('../datos/estaciones.txt', sep=';')
infile = 'balance_JUN_ROJAS_TL_PERG_montecarlo.xls'#df.loc[df['nom_est'] == estacion, 'archivo_in'].values[0]
print(infile)
df = pd.read_excel(c1 + infile, sheet_name='DatosDiarios', index_col='Fecha')
df_g = pd.read_excel(c1 + infile, sheet_name=u'DatosGráfico', index_col=u'Década')
df0 = df.loc['1970-01-01':'2022-05-01',]
minimos = df0.groupby([df0.index.month, df0.index.day]).min()
#minimos['alm real'].rolling(8, center=True, min_periods=1).mean()
valores = minimos['alm real'].to_numpy()
# Bisiesto
mbis = np.zeros(366+8)
mbis[0:4] = valores[-4:]
mbis[4:-4] = valores
mbis[-4:] = valores[0:4]
v1 = pd.Series(data=mbis, index=np.arange(0,len(mbis)))
min_bis = v1.rolling(8, center=True, min_periods=4).mean().to_numpy()[4:-4]

# No Bisiesto
mnbis = np.zeros(365+8)
mnbis[0:4] = valores[-4:]
mnbis[4:-4] = np.concatenate((valores[0:59], valores[60:]), axis=0)
mnbis[-4:] = valores[0:4]
v1 = pd.Series(data=mnbis, index=np.arange(0,len(mnbis)))
min_nbis = v1.rolling(8, center=True, min_periods=4).mean().to_numpy()[4:-4]
#

xy = pd.date_range(start='2016-01-01', end='2017-12-31')
xy_g = pd.date_range(start='2016-05-19', end='2017-01-06')

plt.plot(xy, np.concatenate((min_bis, min_nbis), axis=0), 'k')
plt.plot(xy_g, df_g[u'Mínimo histórico'].to_numpy(),'r')
plt.ylim([0,350])
plt.show()
