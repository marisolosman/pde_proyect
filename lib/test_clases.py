from class_historico import class_historico
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
estacion = 'venado_tuerto'
nomvar = 'velviento'
a = class_historico(estacion, 20)
t1 = a.dtimes
var_o = a.datos_obs[nomvar]
msk_o = a.mask_obs[nomvar]
msk_m = a.mask_mod[nomvar]
var_m = a.datos_mod[nomvar]
b1 = np.logical_and(t1 >= '01/01/2009',
                    t1 <= '12/31/2009')
m_hist = np.array([a.month for a in a.dtimes])
ind_data = np.isin(m_hist, np.array([3, 4, 5]))
im_tot = np.logical_and(ind_data, np.logical_not(b1))
mask_o = np.logical_and(msk_o, im_tot)
mask_m = np.logical_and(msk_m, im_tot)
#plt.plot(t1[msk_o], var_o[msk_o], 'sk', lw=0.5)
plt.plot(t1[msk_m], var_m[msk_m], 'xg')
#plt.plot(t1[mask_o], var_o[mask_o],'sb')
plt.plot(t1[mask_m], var_m[mask_m], '<r')
plt.show()
#plt.tight_layout()
#plt.savefig(estacion + '_' + nomvar + '.jpg')
