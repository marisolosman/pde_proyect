import sys
sys.path.append('/home/osman/proyectos/pde_proyect/lib/')
from class_operativa import class_operativa
from class_bhora import class_bhora
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
# Datos INPUT
# carpeta = '/home/osman/proyectos/pde_proyect/datos/datos_op/resistencia/20081203/'
estacion = 'resistencia'
fecha = '20210218'
correccion = True
tipo_bh = 'profundo'
cultivo = 'S1-VII'
carpeta_input = '/home/osman/proyectos/pde_proyect/datos/bhora_init/'
carpeta_output = '/home/osman/proyectos/pde_proyect/pde_salidas/' + estacion + '/forecast_bh/'


b = class_operativa(estacion, fecha, False)
a = class_operativa(estacion, fecha, True, 'GG')
for i in range(0,16,4):
    a.radsup[0, i:i + 4] = a.radsup[0, i]
    b.radsup[0, i: i + 4 ] = b.radsup[0, i]
    a.etp[0, i:i + 4] = a.etp[0, i]
    b.etp[0, i: i + 4 ] = b.etp[0, i]

c = class_bhora(a, cultivo, tipo_bh)
d = class_bhora(b, cultivo, tipo_bh)
#e = class_bhora(b, cultivo, tipo_bh, True)

#print(d.ALMR)
#print(c.clt_data)
#print(c.kc)
#print(c.ALMR[0:10,:])
#print(np.nanquantile(c.ALMR, 0.25, axis=1))
#open xls file
comienzo = c.dtimes[0] - dt.timedelta(hours=24 * 5)
xaxx = pd.date_range(start=comienzo.strftime('%Y-%m-%d'), end=c.dtimes[-1].strftime('%Y-%m-%d'))
exc_file = carpeta_input + 'balance_RESIS_FL40-45_S1-VII_NORTE.xls'
hist_data = pd.read_excel(exc_file)
fechas = [i.strftime('%m-%d') for i in hist_data.iloc[:, 0]]
period = [i for i, e in enumerate(fechas) if e in set(xaxx.strftime('%m-%d'))]
clim_times = pd.date_range(start=hist_data.iloc[period[0], 0].strftime('%Y-%m-%d'),
                           end=hist_data.iloc[period[-1], 0].strftime('%Y-%m-%d'))
periodo_excesos = hist_data.iloc[period, 11]
periodo_def = hist_data.iloc[period, 10]
min_historico = hist_data.iloc[period, 3]
int_norm_inf = hist_data.iloc[period, 4]
int_norm_sup = hist_data.iloc[period, 5]

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
plt.savefig(carpeta_output + 'BH_pcolor_ic_' + fecha + '.png')

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(19, 8))
# capacidad de campo el azul
ax[0].axhline(c.clt_data['CC'], color='blue')
# punto de marchitez en rojo
ax[0].axhline(c.clt_data['PMP'], color='brown')
# minimo historico: linea punteada gris
ax[0].plot(clim_times, min_historico.values, color='black', linestyle=(0, (5, 10)),
           alpha=0.3)
# intervalor normal
ax[0].plot(clim_times, int_norm_inf, color='black', alpha=0.3)
ax[0].plot(clim_times, int_norm_sup, color='black', alpha=0.3)

#período critico exceso: linea celeste. periodo crifico deficit: linea amarilla
if 107 in periodo_excesos.values:
    ax[0].fill_between(clim_times[np.where(periodo_excesos.values==107)], 0, 105, facecolor='aqua', alpha=0.2, hatch='/', color='aqua')
if 107 in periodo_def.values:
    ax[0].fill_between(clim_times[np.where(periodo_def.values==107)], 0, 105, facecolor='gold', alpha=0.2, hatch='/', color='gold')
## prono: intervalo intercuartil, maximo y minimo
#ax[0].fill_between(c.dtimes, np.nanquantile(c.ALMR, 0.25, axis=1), np.nanquantile(c.ALMR, 0.75, axis=1),
#                   alpha=0.3,
#                  facecolor='limegreen')
# ax[0].fill_between(c.dtimes, np.nanmin(c.ALMR, axis=1), np.nanmax(c.ALMR, axis=1),
#                   alpha=0.4, facecolor='limegreen')
ax[0].plot(c.dtimes, np.nanmax(c.ALMR, axis=1), color='limegreen', linestyle='--')
ax[0].plot(c.dtimes, np.nanmin(c.ALMR, axis=1), color='limegreen', linestyle='--')
ax[0].plot(c.dtimes, c.ALMR, color='green', alpha=0.2, linewidth=0.9)
# prono: mediana del ensamble
ax[0].plot(c.dtimes, np.nanquantile(c.ALMR, 0.5, axis=1), color='green', linewidth=2)
# observado
ax[0].plot(c.fecha_obs, c.almr_obs,'k',linewidth=2)
ax[0].set_ylim(0, 120)
ax[0].set_xlim(comienzo, c.dtimes[-1])
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
ax[1].plot(clim_times, min_historico.values, color='black', linestyle=(0, (5, 10)),
           alpha=0.3)
# intervalor normal
ax[1].plot(clim_times, int_norm_inf, color='green', alpha=0.3)
ax[1].plot(clim_times, int_norm_sup, color='green', alpha=0.3)

#período critico exceso: linea celeste. periodo crifico deficit: linea amarilla
if 107 in periodo_excesos.values:
    ax[1].fill_between(clim_times[np.where(periodo_excesos.values==107)], 0, 105, facecolor='aqua', alpha=0.2, hatch='/', color='aqua')
if 107 in periodo_def.values:
    ax[1].fill_between(clim_times[np.where(periodo_def.values==107)], 0, 105, facecolor='gold', alpha=0.2, hatch='/', color='gold')

# prono: intervalo intercuartil, maximo y minimo
ax[1].fill_between(d.dtimes, np.nanquantile(d.ALMR, 0.25, axis=1), np.nanquantile(d.ALMR, 0.75, axis=1),
                   alpha=0.3, facecolor='black')
ax[1].fill_between(d.dtimes, np.nanquantile(d.ALMR, 0.1, axis=1), np.nanquantile(d.ALMR, 0.9, axis=1),
                   alpha=0.4, facecolor='black')
ax[1].plot(d.dtimes, d.ALMR, color='black', alpha=0.2, linewidth=0.9)
# prono: mediana del ensamble
ax[1].plot(d.dtimes, np.nanquantile(d.ALMR, 0.5, axis=1), color='yellow')
ax[1].plot(d.fecha_obs, d.almr_obs,'k',linewidth=2)
ax[1].set_ylim(0, 120)
ax[1].set_xlim(xaxx[0], xaxx[-1])
ax[1].set_xticks(d.dtimes[::5])
xlab = [i.strftime('%m-%d') for i in d.dtimes[::5]]
ax[1].set_xticklabels(xlab, fontsize=8, rotation=45)
ax[1].axes.set_xlabel('Fecha')
ax[1].axes.set_ylabel('Milimetros')
ax[1].set_title('Sin corregir')
plt.suptitle('Perspectiva Reserva de agua en el suelo - ' + str.title(estacion) + ' - CI: ' + fecha)
plt.savefig(carpeta_output + 'BH_ic_' + fecha + '_2.png')

