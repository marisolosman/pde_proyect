import sys
sys.path.append('../lib/')
from class_operativa import class_operativa
from class_bhora import class_bhora
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# Datos INPUT
fecha = '20090105'
carpeta = '../datos/datos_op/resistencia/' + fecha + '/'
estacion = 'resistencia'
correccion = True
tipo_bh = 'profundo'
cultivo = 'S1-VII'

a = class_operativa(estacion, fecha, True, 'GG')
b = class_operativa(estacion, fecha, False)

c = class_bhora(a, cultivo, tipo_bh)
d = class_bhora(b, cultivo, tipo_bh)
print(np.nanmean(c.ALMR, axis=1))
print(np.nanmean(d.ALMR, axis=1))
#e = class_bhora(b, cultivo, tipo_bh, True)

#print(c.id_ora)
print(c.clt_data)
#print(c.kc)
#print(dir(c))
#open xls file

exc_file = '../datos/bhora_init/balance_RESIS_FL40-45_S1-VII_NORTE.xls'
hist_data = pd.read_excel(exc_file)
fechas = [i.strftime('%m-%d') for i in hist_data.iloc[:, 0]]
print(fechas)
startd = fechas.index(c.dtimes[0].strftime('%m-%d'))
endd = fechas.index(c.dtimes[-1].strftime('%m-%d'))
periodo_excesos = hist_data.iloc[startd:endd+1, 11]
periodo_def = hist_data.iloc[startd:endd+1, 10]
min_historico = hist_data.iloc[startd:endd+1, 3]

fig, ax = plt.subplots(nrows=1, ncols=3)
imagen = ax[0].pcolormesh(c.ALMR, vmin=0, vmax=100)
plt.colorbar(imagen, ax=ax[0])
ax[0].set_title('Corregido QQ BH')
imagen = ax[1].pcolormesh(d.ALMR, vmin=0, vmax=100)
plt.colorbar(imagen, ax=ax[1])
ax[1].set_title('Original')
imagen = ax[2].pcolormesh(c.ALMR - d.ALMR, cmap='bwr', vmin=-10, vmax=10)
plt.colorbar(imagen, ax=ax[2])
ax[2].set_title('Corregido QQ BH - Original')
plt.title('corregido - original')
plt.savefig('BH_pcolor_ic_' + fecha + '.png')

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(19, 8))
# capacidad de campo el azul
ax[0].axhline(c.clt_data['CC'], color='blue')
# punto de marchitez en rojo
ax[0].axhline(c.clt_data['PMP'], color='brown')
# minimo historico: linea punteada gris
ax[0].plot(c.dtimes, min_historico.values, color='black', linestyle='--',
           alpha=0.3)
#período critico exceso: linea celeste. periodo crifico deficit: linea amarilla
if 107 in periodo_excesos.values:
    ax[0].fill_between(c.dtimes[np.where(periodo_excesos.values==107)], 0, 105, facecolor='aqua', alpha=0.2, hatch='/', color='aqua')
if 107 in periodo_def.values:
    ax[0].fill_between(c.dtimes[np.where(periodo_def.values==107)], 0, 105, facecolor='gold', alpha=0.2, hatch='/', color='gold')
# prono: intervalo intercuartil, maximo y minimo
ax[0].fill_between(c.dtimes, np.nanquantile(c.ALMR, 0.25, axis=1), np.quantile(c.ALMR, 0.75, axis=1),
                   alpha=0.3,
                   facecolor='limegreen')
ax[0].fill_between(c.dtimes, np.nanmin(c.ALMR, axis=1), np.nanmax(c.ALMR, axis=1),
                   alpha=0.4, facecolor='limegreen')
# prono: media del ensamble
ax[0].plot(c.dtimes, np.nanmean(c.ALMR,axis=1), color='yellow', linewidth=2)
# observado
ax[0].plot(c.fecha_obs, c.almr_obs,'k',linewidth=2)
ax[0].set_ylim(0, 120)
ax[0].set_xlim(c.dtimes[0], c.dtimes[-1])
ax[0].set_xticks(c.dtimes[::5])
xlab = [i.strftime('%m-%d') for i in c.dtimes[::5]]
ax[0].set_xticklabels(xlab, fontsize=8, rotation=45)
ax[0].axes.set_xlabel('Fecha')
ax[0].axes.set_ylabel('Milimetros')
ax[0].set_title('Corregido GG')

# capacidad de campo el azul
ax[1].axhline(c.clt_data['CC'], color='blue')
# punto de marchitez en rojo
ax[1].axhline(c.clt_data['PMP'], color='brown')
# minimo historico: linea punteada gris
ax[1].plot(d.dtimes, min_historico.values, color='black', linestyle='--',
           alpha=0.3)
#período critico exceso: linea celeste. periodo crifico deficit: linea amarilla
if 107 in periodo_excesos.values:
    ax[1].fill_between(c.dtimes[np.where(periodo_excesos.values==107)], 0, 105, facecolor='aqua', alpha=0.2, hatch='/', color='aqua')
if 107 in periodo_def.values:
    ax[1].fill_between(c.dtimes[np.where(periodo_def.values==107)], 0, 105, facecolor='gold', alpha=0.2, hatch='/', color='gold')

# prono: intervalo intercuartil, maximo y minimo
ax[1].fill_between(d.dtimes, np.nanquantile(d.ALMR, 0.25, axis=1), np.nanquantile(d.ALMR, 0.75, axis=1),
                   alpha=0.3, facecolor='black')
ax[1].fill_between(d.dtimes, np.nanmin(d.ALMR, axis=1), np.nanmax(d.ALMR, axis=1),
                   alpha=0.4, facecolor='black')
ax[1].plot(d.dtimes, d.ALMR, color='black', alpha=0.2, linewidth=0.5)
# prono: media del ensamble
ax[1].plot(d.dtimes, np.nanmean(d.ALMR, axis=1), color='yellow')
ax[1].plot(d.fecha_obs, d.almr_obs,'k',linewidth=2)
ax[1].set_ylim(0, 120)
ax[1].set_xlim(d.dtimes[0], d.dtimes[-1])
ax[1].set_xticks(d.dtimes[::5])
xlab = [i.strftime('%m-%d') for i in d.dtimes[::5]]
ax[1].set_xticklabels(xlab, fontsize=8, rotation=45)
ax[1].axes.set_xlabel('Fecha')
ax[1].axes.set_ylabel('Milimetros')
plt.title('Sin corregir')

plt.suptitle('Perspectiva Reserva de agua en el suelo - ' + str.title(estacion) + ' - CI: ' + fecha)
plt.savefig('BH_ic_' + fecha + '.png')
