from class_historico import class_historico
import numpy as np
import matplotlib.pyplot as plt

a = class_historico('trenque_lauquen', 10)
t1 = a.dtimes
nomvar = 'precip'
radsup_obs = a.datos_obs[nomvar]
mo_radsup = a.mask_obs[nomvar]
m_radsup = a.mask_mod[nomvar]
radsup_mod = a.datos_mod[nomvar]
print(radsup_mod)
b1 = np.logical_and(t1 >= '01/01/2009',
                    t1 <= '12/31/2009')
m_hist = np.array([a.month for a in a.dtimes])
ind_data = np.isin(m_hist, np.array([3, 4, 5]))
im_tot = np.logical_and(ind_data, np.logical_not(b1))
mask_o = np.logical_and(np.logical_not(a.mask_mod[nomvar]), im_tot)
plt.plot(a.dtimes, radsup_mod, 'xg')
plt.plot(a.dtimes, radsup_obs, 'sk', lw=0.5)
#plt.plot(a.dtimes[m_radsup], radsup_mod[m_radsup],'sg')
#plt.plot(a.dtimes[mask_o], radsup_mod[mask_o], '<r')
plt.show()
