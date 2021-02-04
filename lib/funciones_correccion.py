import math
import numpy as np
# Gamma Module from scipy
from scipy.stats import gamma
# ECDF function
from statsmodels.distributions.empirical_distribution import ECDF

from class_historico import class_historico

np.seterr(divide='ignore', invalid='ignore')
'''
This set of function receives data to correct the values
using the quantile-quantile technique.
it uses as base a matrix data

dtimes: The date in a datetime format Pandas
data: Matrix of ntimes x n_ens dimension with data
nomvar: Name of the variable
it can take the following values:
['tmax', 'tmin', 'precip', 'hrmean', 'velviento', 'radsup']

This function retrieves the historical values of model and observation
and generate the ECDF/Gamma Parameters for both of them and depending the variable.

After this, returns the data of corrected values

Reference: Boe et al., 2007. 'Statistical and dynamical downscaling of the
Seine basin climate for hydro-meteorological studies'
'''

def select_data_period(estacion, nomvar, mes, year_test='None'):
    df = class_historico(estacion)

    if mes - 1 <= 0:
        cnd = [12, 1, 2]
    elif mes + 1 >= 13:
        cnd = [11, 12, 1]
    else:
        cnd = [mes - 1, mes, mes + 1]
    if year_test == 'None':
        m_hist = np.array([a.month for a in df.dtimes])
        ind_data = np.isin(m_hist, np.array(cnd))
        mask_o = np.logical_or(df.mask_obs[nomvar], ind_data)
        mask_m = np.logical_or(df.mask_mod[nomvar], ind_data)
        do = df.datos_obs[nomvar][mask_o]
        dm = df.datos_mod[nomvar][mask_m]
    else:
        id_fm = np.logical_and(df.dtimes >= '01/01/'+str(year_test),
                               df.dtimes <= '12/31/'+str(year_test))
        # generate index to work in cnd and out of year considered.
        m_hist = np.array([a.month for a in df.dtimes])
        ind_data = np.isin(m_hist, np.array(cnd))
        exc_data = np.logical_and(ind_data, np.logical_not(id_fm))
        # extract data to generate the distribution of historical data.
        mask_o = np.logical_or(df.mask_obs[nomvar], exc_data)
        mask_m = np.logical_or(df.mask_mod[nomvar], exc_data)
        do = df.datos_obs[nomvar][mask_o]
        dm = df.datos_mod[nomvar][mask_m]

    return do, dm

def precipitation_days(ppdata, ppmin):
    ind_pp = np.array([e > ppmin if ~np.isnan(e) else False
                        for e in ppdata], dtype=bool)
    return ppdata[ind_pp]


def fit_ecdf(estacion, nomvar, mes, year_test='None'):
    """
    """
    do, dm = select_data_period(estacion, nomvar, mes)
    #
    if nomvar == 'precip':
        ppo_data = precipitation_days(do, 0.1)
        ppm_data = precipitation_days(dm, 1.)
        ecdf_obs = ECDF(ppo_data)
        ecdf_mod = ECDF(ppm_data)
    else:
        ecdf_obs = ECDF(do)
        ecdf_mod = ECDF(dm)

    return ecdf_obs, ecdf_mod, do, dm


def fit_gamma_param(estacion, mes, xo_min=0.1, xm_min=1., year_test='None'):
    # Ajusta parametros de Gamma para precipitacion
    do, dm = select_data_period(estacion, 'precip', mes)
    cdf_limite = .9999999
    #
    # Days with precipitacion
    ppo_data = precipitation_days(do, xo_min)
    ppm_data = precipitation_days(dm, xm_min)
    # Fit a Gamma distribution over days with precipitation
    obs_gamma_param = gamma.fit(ppo_data, floc=0)
    mod_gamma_param = gamma.fit(ppm_data, floc=0)

    return obs_gamma_param, mod_gamma_param


def qq_correction(data, nomvar, dtimes, estacion):

    #print(' ################# Correccion Q-Q ', nomvar, ' #################')
    cdf_limite = .9999999
    meses = [a.month for a in dtimes]
    data_corr = np.empty(data.shape)
    data_corr[:] = np.nan
    for mes in np.unique(meses):
        prono = data[meses==mes, :]
        corr = data[meses==mes,:]
        obs_ecdf, mod_ecdf, obs_datos, mod_datos = fit_ecdf(estacion, nomvar, mes)
        p1 = mod_ecdf(prono)
        p1[p1 > cdf_limite] = cdf_limite
        corr_o = np.nanquantile(obs_datos, p1.flatten(), interpolation='linear')
        data_corr[meses==mes, :] = np.reshape(corr_o, p1.shape)

    return data_corr


def qq_correction_pp(data, dtimes, estacion, tipo_ajuste='GG',
                     xo_min=0.1, xm_min=1.):
    cdf_limite = .9999999
    meses = [a.month for a in dtimes]
    data_corr = np.empty(data.shape)
    data_corr[:] = np.nan
    for mes in np.unique(meses):
        prono = data[meses==mes, :]
        corr = data[meses==mes,:]
        corr[prono <= xm_min] = 0.
        corr[np.isnan(prono)] = np.nan
        # Corregimos los mayores a xm_min y que no son NaN's
        idc = np.logical_and(prono > xm_min, np.logical_not(np.isnan(prono)))
        if tipo_ajuste == 'GG':
            # Ajustamos una gamma a los valores con precipitacion y corregimos
            obs_gamma, mod_gamma = fit_gamma_param(estacion, mes, xo_min, xm_min)

            p1 = gamma.cdf(prono[idc], *mod_gamma)
            p1[p1>cdf_limite] = cdf_limite
            corr_o = gamma.ppf(p1, *obs_gamma)
            corr[idc] = corr_o
            data_corr[meses==mes, :] = corr
        elif tipo_ajuste == 'EG':
            obs_gamma, mod_gamma = fit_gamma_param(estacion, mes, xo_min, xm_min)
            mod_ecdf, mod_precdias, d1, d2 = fit_ecdf(estacion, 'precip', mes)
            p1 = mod_ecdf(prono[idc])
            p1[p1>cdf_limite] = cdf_limite
            corr_o = gamma.ppf(p1, *obs_gamma)
            corr[idc] = corr_o
            data_corr[meses==mes, :] = corr
        elif tipo_ajuste == 'Mult-Shift':
            ecdf_obs, ecdf_mod, do, dm = fit_ecdf(estacion, 'precip', mes)
            mod_precdias = precipitation_days(dm, xm_min)
            obs_precdias = precipitation_days(do, xo_min)
            xm_mean = np.nanmean(mod_precdias)
            xo_mean = np.nanmean(obs_precdias)
            corr_factor = xo_mean/xm_mean
            corr[idc] = corr[idc]*corr_factor
            data_corr[meses==mes, :] = corr

    return data_corr
