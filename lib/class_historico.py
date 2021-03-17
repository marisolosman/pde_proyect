import glob
import os
import calendar
import pandas as pd
import numpy as np
from netCDF4 import Dataset, num2date
import datetime as dt
from funciones_bhora import get_KC, run_bh_ora
import sys
sys.path.append('../mdb_process/')
from etp_func import CalcularETPconDatos

from oramdb_cultivos_excel import read_soil_parameter

np.seterr(divide='ignore', invalid='ignore')

class class_historico:
    def __init__(self, estacion):
        carpeta = '../datos/datos_hist/'
        self.estacion = estacion
        self.carpeta_obs = carpeta + '/obs/'
        self.carpeta_mod = carpeta + '/modelo/' + estacion + '/'
        self.archivos_obs = glob.glob(self.carpeta_obs + '*.nc')
        self.archivos_mod = glob.glob(self.carpeta_mod + '*.txt')
        self.var = ['tmax', 'tmin','velviento', 'radsup', 'hrmean', 'precip', 'etp']
        self.dtimes = pd.date_range(start='1999-01-01', end='2010-12-31')  # Obtenemos los tiempos del prono
        self.get_data_obs()  # Obtenemos los datos observados
        self.get_data_mod()  # Obtenemos los datos modelados
        self.calc_etp_mod()  # Calculamos la ETP
        self.calc_almr_mod()

    def get_data_obs(self):
        datos = {}
        mask = {}
        for archivo in self.archivos_obs:
            nomvar = os.path.basename(archivo).split('_')[0]
            nc = Dataset(archivo, "r")
            fill_value = nc.variables[self.estacion]._FillValue
            datos[nomvar] = nc.variables[self.estacion][:]
            mask[nomvar] = np.array(datos[nomvar] == fill_value)
        self.datos_obs = datos
        self.mask_obs = mask
        self.id_ora = nc.variables[self.estacion].id_ora
        self.lat = nc.variables[self.estacion].lat
        self.lon = nc.variables[self.estacion].lon
        nc.close()

    def get_data_mod(self):
        datos = {}
        mask = {}
        for archivo in self.archivos_mod:
            nomvar = os.path.basename(archivo).split('_')[2].split('.')[0]
            df = pd.read_csv(archivo, sep=';', decimal=',',
                             header=0).drop(['Unnamed: 0'],axis=1)
            df.loc[:, 'fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')
            if len(df) != len(self.dtimes):
                col = df.loc[:, df.columns[1]::]
                df = df.assign(media_ens=col.mean(axis=1).to_numpy())
                df1 = df.loc[:, ['fecha', 'media_ens']]
                datos_completos = completar(df1, self.dtimes)
                datos[nomvar] = np.squeeze(datos_completos.to_numpy())
                if nomvar == 'tmax' or nomvar == 'tmin':
                    datos[nomvar] = datos[nomvar] - 273.
            else:
                col = df.loc[:,df.columns[1]::]
                datos[nomvar] = col.mean(axis=1).to_numpy()
                if nomvar == 'tmax' or nomvar == 'tmin':
                    datos[nomvar] = datos[nomvar] - 273.
            mask[nomvar] = np.isnan(datos[nomvar])
        self.datos_mod = datos
        self.mask_mod = mask

    def calc_etp_mod(self):
        dic = self.datos_mod.copy()
        dic['Fecha'] = self.dtimes
        ds = pd.DataFrame(data=dic)
        ds1 = CalcularETPconDatos(ds, self.id_ora)
        self.datos_mod['etp'] = ds1['ETP'].to_numpy()
        self.mask_mod['etp'] = ds1['i_ETPm'].to_numpy()

    def calc_almr_mod(self):
        # Calculamos BHORA
        fi = self.dtimes[0] - dt.timedelta(days=1)
        bhvar = {'Fecha':self.dtimes, 'ETP': self.datos_mod['etp'], 'precip':self.datos_mod['precip']}
        DF1 = pd.DataFrame(index=np.arange(len(bhvar['precip'])), data=bhvar)
        DF2 = run_bh_ora(DF1, self.id_ora,'S1-VII' , 'profundo',
                         **{'fecha_inicial':True, 'ini_date':fi, 'debug':False})
        #print(DF2.head())
        self.datos_mod['ALMR'] = np.squeeze(DF2.loc[1:,'ALMR'].to_numpy())
        self.mask_mod['ALMR'] = np.ones(len(self.datos_mod['ALMR']), dtype=bool)




# ------------------
# OTRAS FUNCIONES
# ------------------
def completar(df, fechas ):
    nomvar = df.columns[1]
    faltante = {'fecha':fechas, nomvar:-999.9*np.ones(len(fechas))}
    da = pd.DataFrame(index=np.arange(0, len(fechas)), data=faltante)
    D1 = pd.merge(df, da, on='fecha', how='outer', indicator=True)
    if 'right_only' in D1._merge.values:
        D1.loc[D1._merge == 'right_only', nomvar + '_x'] = -999.9
    D1.sort_values(by=['fecha'], inplace=True)
    D2 = pd.DataFrame(index=fechas, data={nomvar:D1[nomvar + '_x'].values})
    D2.loc[D2[nomvar] == -999] = np.nan
    return D2

def calc_bh_hist(bhvar, ds, kc):
    Nt = len(bhvar['ALM'])
    print(bhvar['PP'][0:3,:])
    for d in np.arange(1, Nt):
        # Capacidad de Infiltracion
        CI = ds['CC'] - bhvar['ALM'][d - 1,:]
        # Indice donde se supera limite de percolacion
        i_ui = bhvar['ALM'][d - 1,:] > ds['UI']
        i_nui = np.logical_not(i_ui)
        # Calculamos Percolacion
        bhvar['PER'][d,i_ui] = ds['CP'] * (bhvar['ALM'][d - 1, i_ui] - ds['UI'])
        bhvar['PER'][d,i_nui] = 0.
        # Precipitacion para el dia
        SUM = bhvar['PP'][d, :] - bhvar['EXC'][d - 1, :]
        # Escorrentia
        i_esc = SUM > 0.
        i_nesc = np.logical_not(i_esc)
        bhvar['ESC'][d, i_esc] = (ds['CE']**2)*SUM[i_esc]*np.exp(-CI[i_esc]/SUM[i_esc])
        bhvar['ESC'][d, i_nesc] = 0.
        # ----- Precipitacion efectiva
        PPE = bhvar['PP'][d,:] - bhvar['ESC'][d,:]
        # ----- Calculos ETP Cultivo
        bhvar['ETC'][d,:] = kc[d]*bhvar['ETP'][d,:]
        # ----- Calculos de ALMACENAJE
        DIF = PPE - bhvar['ETC'][d,:]
        i_alm = DIF > 0.
        i_nalm = np.logical_not(i_alm)
        aux = np.exp( (ds['CCD']**(-1) + 1.29*ds['CCD']**(-1.88)) * DIF )
        # DIF mayor que cero
        bhvar['ALM'][d,i_alm] = bhvar['ALM'][d - 1,i_alm] + bhvar['EXC'][d - 1,i_alm] +\
                        PPE[i_alm] - bhvar['ETC'][d, i_alm] - bhvar['PER'][d,i_alm]
        # DIF menor que cero
        bhvar['ALM'][d,i_nalm] = (bhvar['ALM'][d-1,i_nalm] +\
                        bhvar['EXC'][d-1,i_nalm]) * aux[i_nalm] - bhvar['PER'][d,i_nalm]
        # excesos
        i_ccd = bhvar['ALM'][d,:] > ds['CCD']
        bhvar['EXC'][d, i_ccd] = bhvar['ALM'][d, i_ccd] - ds['CCD']
        bhvar['ALM'][d, i_ccd] = ds['CCD']
        # Calculos salidas
        bhvar['ALMR'][d,:] = bhvar['ALM'][d,:] + ds['ALM_MIN']
        bhvar['ETR'][d,:] = - bhvar['ALM'][d,:] + bhvar['ALM'][d-1,:] - bhvar['EXC'][d,:] +\
                bhvar['EXC'][d-1,:] + bhvar['PP'][d,:] - bhvar['ESC'][d,:] - bhvar['PER'][d,:]
    # Hasta aca se calcula el BH
    almr = bhvar['ALMR']
    return almr
