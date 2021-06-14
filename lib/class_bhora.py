import glob
import pandas as pd
import numpy as np
import datetime as dt
from funciones_bhora import get_KC
from funciones_correccion import qq_correction

import sys
sys.path.append('/home/osman/projects/pde_proyect/mdb_process/')
from oramdb_cultivos_excel import read_soil_parameter

np.seterr(divide='ignore', invalid='ignore')

class class_bhora:
    def __init__(self, opera, clt, t_bh, corr_bh=False):
        carpeta = '../datos/salidas_op/'
        self.opera = opera
        self.fecha = opera.fecha
        self.clt = clt
        self.t_bh = t_bh
        # Calculamos los datos necesarios para correr BH-ORA
        self.get_times()
        self.get_id()
        self.get_cultivo_data()
        self.get_kc_cultivo()
        # Inicializamos variables
        self.gen_init_cond()
        # Calculamos el BH
        self.calc_bhora()
        if corr_bh:
            self.correct_bhora()

    def get_times(self):
        t_ini = self.opera.dtimes[0] - dt.timedelta(days=1)
        self.dtimes = np.insert(self.opera.dtimes, 0, t_ini)

    def get_id(self):
        from netCDF4 import Dataset
        archivo = '../datos/datos_hist/obs/tmax_199901_201012.nc'
        nc = Dataset(archivo, "r")
        id = nc.variables[self.opera.estacion].id_ora
        nc.close()
        self.id_ora = id

    def get_cultivo_data(self):
        ds = read_soil_parameter(self.id_ora, self.clt, self.t_bh)
        self.clt_data = ds

    def get_kc_cultivo(self):
        import calendar
        julianos = np.array([float(j.timetuple().tm_yday) for j in self.dtimes])
        d_bis, kc_bis, d_nbis, kc_nbis = get_KC(self.id_ora, self.clt)
        kc_local = np.zeros(len(julianos))
        for i, juliano in enumerate(julianos):
            if calendar.isleap(self.dtimes[i].year):
                kc_local[i] = kc_bis[d_bis == juliano]
            else:
                kc_local[i] = kc_nbis[d_nbis == juliano]
        self.djul = julianos
        self.kc = kc_local

    def gen_init_cond(self):
        c1 = '../datos/bhora_init/'
        infile = 'balance_RESIS_FL40-45_S1-VII_NORTE.xls'
        self.balance_real = c1 + infile
        df = pd.read_excel(c1 + infile, sheet_name='DatosDiarios')
        self.almr_obs = df['alm real'].values
        self.fecha_obs = df['Fecha'].dt.to_pydatetime()
        shape = (len(self.dtimes), self.opera.nens)
        fi = self.dtimes[0]
        # Las columnas para extraer datos iniciales
        co1 = ['alm sin min', 'exceso', 'per', 'esc', 'etp',
                u'etr (evapotranspiración real)', 'etc', 'alm real',
                u'precipitación']
        # Nombres
        llaves = ['ALM', 'EXC', 'PER', 'ESC', 'ETP', 'ETR', 'ETC', 'ALMR', 'PP']
        bhvar = {}
        for ky, co in zip(llaves, co1):
            bhvar[ky] = np.zeros(shape)
            try:
                bhvar[ky][0,:] = df.loc[df['Fecha'] == fi, co].values
            except:
                bhvar[ky][0,:] = np.nan

            if ky == 'ETP':
                bhvar[ky][1:,:] = self.opera.etp
            elif ky == 'PP':
                bhvar[ky][1:,:] = self.opera.precip
            setattr(self, ky, bhvar[ky])

    def calc_bhora(self):
        #print('######## ')
        Nt = len(self.ALM)
        for d in np.arange(1, Nt):
            # Capacidad de Infiltracion
            CI = self.clt_data['CC'] - self.ALM[d - 1,:]
            # Indice donde se supera limite de percolacion
            i_ui = self.ALM[d - 1,:] > self.clt_data['UI']
            i_nui = np.logical_not(i_ui)
            # Calculamos Percolacion
            self.PER[d,i_ui] = self.clt_data['CP'] * (self.ALM[d - 1, i_ui] - self.clt_data['UI'])
            self.PER[d,i_nui] = 0.
            # Precipitacion para el dia
            SUM = self.PP[d, :] - self.EXC[d - 1, :]
            # Escorrentia
            i_esc = SUM > 0.
            i_nesc = np.logical_not(i_esc)
            self.ESC[d, i_esc] = (self.clt_data['CE']**2)*SUM[i_esc]*np.exp(-CI[i_esc]/SUM[i_esc])
            self.ESC[d, i_nesc] = 0.
            # ----- Precipitacion efectiva
            PPE = self.PP[d,:] - self.ESC[d,:]
            # ----- Calculos ETP Cultivo
            self.ETC[d,:] = self.kc[d]*self.ETP[d,:]
            # ----- Calculos de ALMACENAJE
            DIF = PPE - self.ETC[d,:]
            i_alm = DIF > 0.
            i_nalm = np.logical_not(i_alm)
            aux = np.exp( (self.clt_data['CCD']**(-1) + 1.29*self.clt_data['CCD']**(-1.88)) * DIF )
            # DIF mayor que cero
            self.ALM[d,i_alm] = self.ALM[d - 1,i_alm] + self.EXC[d - 1,i_alm] +\
                            PPE[i_alm] - self.ETC[d, i_alm] - self.PER[d,i_alm]
            # DIF menor que cero
            self.ALM[d,i_nalm] = (self.ALM[d-1,i_nalm] +\
                            self.EXC[d-1,i_nalm]) * aux[i_nalm] - self.PER[d,i_nalm]
            # excesos
            i_ccd = self.ALM[d,:] > self.clt_data['CCD']
            self.EXC[d, i_ccd] = self.ALM[d, i_ccd] - self.clt_data['CCD']
            self.ALM[d, i_ccd] = self.clt_data['CCD']
            # Calculos salidas
            self.ALMR[d,:] = self.ALM[d,:] + self.clt_data['ALM_MIN']
            self.ETR[d,:] = - self.ALM[d,:] + self.ALM[d-1,:] - self.EXC[d,:] +\
                    self.EXC[d-1,:] + self.PP[d,:] - self.ESC[d,:] - self.PER[d,:]
        # Hasta aca se calcula el BH

    def correct_bhora(self):
        print('CORRIGIENDO BH por BH')
        print(self.ALMR)
        dato_c = qq_correction(self.ALMR[1:,:].copy(), 'ALMR', self.opera.dtimes,
                               self.opera.estacion)
        dato_c[np.isnan(self.ALMR[1:,:])] = np.nan
        self.ALMR[1:,:] = dato_c
