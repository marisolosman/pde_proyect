import sys
sys.path.append('/home/osman/proyectos/pde_proyect/lib/')
from class_operativa import class_operativa
from class_bhora import class_bhora

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
e = class_bhora(b, cultivo, tipo_bh, True)
#print(c.id_ora)
#print(c.clt_data)
#print(c.kc)
#print(dir(c))
fig, ax = plt.subplots(nrows=1, ncols=3)
imagen = ax[0].pcolormesh(e.ALMR, vmin=0, vmax=100)
plt.colorbar(imagen, ax=ax[0])
ax[0].set_title('Corregido QQ BH')
imagen = ax[1].pcolormesh(d.ALMR, vmin=0, vmax=100)
plt.colorbar(imagen, ax=ax[1])
ax[1].set_title('Original')
imagen = ax[2].pcolormesh(e.ALMR - d.ALMR, cmap='bwr', vmin=-10, vmax=10)
plt.colorbar(imagen, ax=ax[2])
ax[2].set_title('Corregido BH - Original')
#plt.title('original - corregido')
plt.show()

fig, ax = plt.subplots(nrows=1, ncols=2)
ax[0].plot(e.dtimes, e.ALMR)
ax[0].plot(e.fecha_obs, e.almr_obs,'k',linewidth=2)
ax[0].set_ylim(0, 120)
ax[0].set_xlim(e.dtimes[0], e.dtimes[-1])
ax[1].plot(d.dtimes, d.ALMR)
ax[1].plot(d.fecha_obs, d.almr_obs,'k',linewidth=2)
ax[1].set_ylim(0, 120)
ax[1].set_xlim(d.dtimes[0], d.dtimes[-1])

plt.show()
