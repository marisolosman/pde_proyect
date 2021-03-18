import sys
sys.path.append('/home/osman/proyectos/pde_proyect/lib/')
from class_operativa import class_operativa
from class_bhora import class_bhora
import numpy as np
from numpy.random import default_rng
import matplotlib.pyplot as plt
# Datos INPUT
carpeta = '/home/osman/proyectos/pde_proyect/datos/datos_op/resistencia/20081203/'
estacion = 'resistencia'
fecha = '20090216'
correccion = True
tipo_bh = 'profundo'
cultivo = 'S1-VII'

a = class_operativa(estacion, fecha, True, 'GG')
b = class_operativa(estacion, fecha, False)

c = class_bhora(a, cultivo, tipo_bh)
d = class_bhora(b, cultivo, tipo_bh)
e = class_bhora(b, cultivo, tipo_bh) #, True)
#print(c.id_ora)
#print(c.clt_data)
#print(c.kc)
#print(dir(c))
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
ax[0].axhline(97, color='blue')
# punto de marchitez en rojo
ax[0].axhline(40, color='brown')
# minimo historico: linea punteada gris
rng = default_rng()
ax[0].plot(c.dtimes, rng.standard_normal(len(c.dtimes)) + 35, color='black', linestyle='--',
           alpha=0.3)
#período critico exceso: linea celeste. periodo crifico deficit: linea amarilla
ax[0].fill_between(c.dtimes[12:18], 0, 105, facecolor='aqua', alpha=0.2, hatch='/', color='aqua')
ax[0].fill_between(c.dtimes[22:25], 0, 105, facecolor='gold', alpha=0.2, hatch='/', color='gold')

# prono: intervalo intercuartil, maximo y minimo
ax[0].fill_between(c.dtimes, np.quantile(c.ALMR, 0.25, axis=1), np.quantile(c.ALMR, 0.75, axis=1),
                   alpha=0.3,
                   facecolor='black')
ax[0].fill_between(c.dtimes, np.min(c.ALMR, axis=1), np.max(c.ALMR, axis=1),
                   alpha=0.4, facecolor='black')
# prono: media del ensamble
ax[0].plot(c.dtimes, np.mean(c.ALMR,axis=1), color='yellow')
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
ax[1].axhline(97, color='blue')
# punto de marchitez en rojo
ax[1].axhline(40, color='brown')
# minimo historico: linea punteada gris
rng = default_rng()
ax[1].plot(d.dtimes, rng.standard_normal(len(d.dtimes)) + 35, color='black', linestyle='--',
           alpha=0.3)
#período critico exceso: linea celeste. periodo crifico deficit: linea amarilla
ax[1].fill_between(d.dtimes[12:18], 0, 105, facecolor='aqua', alpha=0.2, hatch='/', color='aqua')
ax[1].fill_between(d.dtimes[22:25], 0, 105, facecolor='gold', alpha=0.2, hatch='/', color='gold')

# prono: intervalo intercuartil, maximo y minimo
ax[1].fill_between(d.dtimes, np.quantile(d.ALMR, 0.25, axis=1), np.quantile(d.ALMR, 0.75, axis=1),
                   alpha=0.3, facecolor='black')
ax[1].fill_between(d.dtimes, np.min(d.ALMR, axis=1), np.max(d.ALMR, axis=1),
                   alpha=0.4, facecolor='black')
ax[1].plot(d.dtimes, d.ALMR, color='black', alpha=0.2, linewidth=0.5)
# prono: media del ensamble
ax[1].plot(d.dtimes, np.mean(d.ALMR, axis=1), color='yellow')
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

