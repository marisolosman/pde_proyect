import glob
import pandas as pd
import numpy as np
import datetime as dt
import calendar
from dateutil.relativedelta import relativedelta
from funciones_bhora import get_KC
from funciones_correccion import qq_correction

import sys
sys.path.append('../mdb_process/')
from oramdb_cultivos_excel import read_soil_parameter

np.seterr(divide='ignore', invalid='ignore')

class class_bhora:
    def __init__(self, opera, clt, t_bh, yr_c, corr_bh=False):
        '''
        opera: Objeto con las variables operativas para calcular el BH
        clt: String con el cultivo para el cual se quiere calcular el BH
        t_bh: String con el tipo de balance a utilizar: 'Superficial' o 'Profundo'
        yr_c: int con el año del comienzo de campaña -> se utiliza para obtener
              los datos del grafico (inicio, fin y periodos criticos)
        corr_bh: Logical que indica si se realiza correccion al ALMR utilizando el
                 historico de ALMR
        '''
        carpeta = '../datos/salidas_op/'
        self.opera = opera
        self.fecha = opera.fecha
        self.clt = clt
        self.t_bh = t_bh
        self.yr_c = yr_c
        self.c1 = '/datos/osman/datos_pde_project/' # carpeta con datos actualizados
        # Calculamos los datos necesarios para correr BH-ORA
        self.get_times()
        self.get_id()
        self.get_cultivo_data()
        self.get_kc_cultivo()
        # Inicializamos variables
        self.gen_init_cond()
        # Calculamos el BH
        self.calc_bhora()
        # Agregamos datos para los graficos
        self.get_plot_data()
        # Corregimos por ALM en caso se requiera
        if corr_bh:
            self.correct_bhora()

    def get_times(self):
        t_ini = self.opera.dtimes[0] # - dt.timedelta(days=1)
        self.dtimes = np.insert(self.opera.dtimes, 0, t_ini)

    def get_id(self):
        from netCDF4 import Dataset
        archivo = '../datos/datos_hist/obs/tmax_199901_201012.nc'
        nc = Dataset(archivo, "r")
        id = nc.variables[self.opera.estacion].id_ora
        n1 = nc.variables[self.opera.estacion].long_name
        p1 = nc.variables[self.opera.estacion].provincia
        t1 = nc.variables[self.opera.estacion].tipo
        nc.close()
        self.id_ora = id
        self.data_estacion = {'nombre':n1, 'prov':p1, 'tipoe':t1}

    def get_cultivo_data(self):
        df = pd.read_csv('../datos/estaciones.txt', sep=';')
        i1 =  (df['nom_est'] == self.opera.estacion) & (df['cultivo'] == self.clt)
        nombre_cultivo = df.loc[i1, 'nombre_cultivo'].values[0]
        ds = read_soil_parameter(self.id_ora, self.clt, self.t_bh)
        self.clt_data = ds
        self.nombre_cultivo = nombre_cultivo

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
        c1 = self.c1
        # Cultivos BH
        df = pd.read_csv('../datos/estaciones.txt', sep=';')
        infile = df.loc[np.logical_and(df['nom_est'] == self.opera.estacion,
                                       df['cultivo'] == self.clt),
                        'archivo_in'].values[0]
        self.balance_real = c1 + infile
        df = pd.read_excel(c1 + infile, sheet_name='DatosDiarios')
        self.almr_obs = df['alm real'].values
        self.fecha_obs = df['Fecha'].dt.to_pydatetime()
        df = df.assign(juliano=df['Fecha'].dt.dayofyear)
        minimos = df.groupby('juliano').min()
        self.almr_min = minimos['alm real'].to_numpy()
        self.almr_min_jul = np.arange(1,367)
        #
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
                try:
                    bhvar[ky][1:,:] = self.opera.etp
                except:
                    bhvar[ky][1:,:] = np.nan
            elif ky == 'PP':
                try:
                    bhvar[ky][1:,:] = self.opera.precip
                except:
                    bhvar[ky][1:,:] = np.nan

            setattr(self, ky, bhvar[ky])

    def get_plot_data(self):
        c1 = '../datos/oramdb/DatosGraficos.xlsx'
        df0 = pd.read_excel(c1, sheet_name='Dptos Fenologia')
        df1 = pd.read_excel(c1, sheet_name='Etapas')
        df2 = pd.read_excel(c1, sheet_name='PriodosCriticos')
        df3 = pd.read_excel(c1, sheet_name='ResumenPDE')
        # Fecha Inicio: Siembra; Fecha Fin: Cosecha
        cnd_i = (df3.estacion == self.opera.estacion) & (df3.Cultivo == self.clt) & (df3.ETAPA == 'Siembra')
        cnd_f = (df3.estacion == self.opera.estacion) & (df3.Cultivo == self.clt) & (df3.ETAPA == 'Cosecha')
        mesi = df3.loc[cnd_i, 'Mes'].values[0]
        diai = df3.loc[cnd_i, u'Día'].values[0]
        if self.clt[0] == 'S':
            year_end = self.yr_c + 1
        else:
            year_end = self.yr_c
        self.fecha_inicio_plot = dt.datetime(self.yr_c, mesi, diai) - relativedelta(months=1)
        self.fecha_media_siembra = dt.datetime(self.yr_c, mesi, diai)
        mesf = df3.loc[cnd_f, 'Mes'].values[0]
        diaf = df3.loc[cnd_f, u'Día'].values[0]

        self.fecha_fin_plot = dt.datetime(year_end, mesf, diaf) + relativedelta(months=2)
        self.fecha_media_cosecha = dt.datetime(year_end, mesf, diaf)
        # Periodo Critico Deficit
        # Inicio
        cnd = (df3.estacion == self.opera.estacion) & (df3.Cultivo == self.clt)
        cultivo = df3.loc[cnd,'Ncultivo'].values[0]
        di = int(df2.loc[df2.CULTIVO == cultivo,'di'].values[0])
        E_di = df2.loc[df2.CULTIVO == cultivo,u'INICIO DÉFICIT'].values[0]
        cnd_id = (df3.estacion == self.opera.estacion) & (df3.Cultivo == self.clt) & (df3.ETAPA == E_di)
        mes_id = df3.loc[cnd_id, 'Mes'].values[0]
        dia_id = df3.loc[cnd_id, u'Día'].values[0]
        self.fecha_inicio_deficit = dt.datetime(year_end, mes_id, dia_id) + dt.timedelta(days=di)
        # Fin
        cnd = (df3.estacion == self.opera.estacion) & (df3.Cultivo == self.clt)
        cultivo = df3.loc[cnd,'Ncultivo'].values[0]
        df = int(df2.loc[df2.CULTIVO == cultivo,'df'].values[0])
        E_df = df2.loc[df2.CULTIVO == cultivo,u'FIN DÉFICIT'].values[0]
        cnd_fd = (df3.estacion == self.opera.estacion) & (df3.Cultivo == self.clt) & (df3.ETAPA == E_df)
        mes_fd = df3.loc[cnd_fd, 'Mes'].values[0]
        dia_fd = df3.loc[cnd_fd, u'Día'].values[0]
        self.fecha_fin_deficit = dt.datetime(year_end, mes_fd, dia_fd) + dt.timedelta(days=df)
        # Periodo Critico Excesos
        # Inicio
        cnd = (df3.estacion == self.opera.estacion) & (df3.Cultivo == self.clt)
        cultivo = df3.loc[cnd,'Ncultivo'].values[0]
        di = int(df2.loc[df2.CULTIVO == cultivo,'ei'].values[0])
        E_di = df2.loc[df2.CULTIVO == cultivo,u'INICIO EXCESOS'].values[0]
        cnd_id = (df3.estacion == self.opera.estacion) & (df3.Cultivo == self.clt) & (df3.ETAPA == E_di)
        mes_id = df3.loc[cnd_id, 'Mes'].values[0]
        dia_id = df3.loc[cnd_id, u'Día'].values[0]
        self.fecha_inicio_excesos = dt.datetime(year_end, mes_id, dia_id) + dt.timedelta(days=di)
        # Fin
        cnd = (df3.estacion == self.opera.estacion) & (df3.Cultivo == self.clt)
        cultivo = df3.loc[cnd,'Ncultivo'].values[0]
        df = int(df2.loc[df2.CULTIVO == cultivo,'ef'].values[0])
        E_df = df2.loc[df2.CULTIVO == cultivo,u'FIN EXCESOS'].values[0]
        cnd_fd = (df3.estacion == self.opera.estacion) & (df3.Cultivo == self.clt) & (df3.ETAPA == E_df)
        mes_fd = df3.loc[cnd_fd, 'Mes'].values[0]
        dia_fd = df3.loc[cnd_fd, u'Día'].values[0]
        self.fecha_fin_excesos = dt.datetime(year_end, mes_fd, dia_fd) + dt.timedelta(days=df)

    def calc_min_hist(self):
        c1 = self.c1
        df = pd.read_csv('../datos/estaciones.txt', sep=';')
        cnd = (df.nom_est == self.opera.estacion) & (df.cultivo == self.clt)
        infile = df.loc[cnd,'archivo_in'].values[0]
        df = pd.read_excel(c1 + infile, sheet_name='DatosDiarios', index_col='Fecha')
        fd = dt.datetime.strptime(self.fecha, '%Y%m%d') - dt.timedelta(days=1)
        df0 = df.loc['1970-01-01':fd.strftime('%Y-%m-%d'),]
        minimos = df0.groupby([df0.index.month, df0.index.day]).min()
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
        feh = pd.date_range(start=dt.datetime(self.yr_c, 1, 1), end=dt.datetime(self.yr_c+1, 12, 31))
        if (calendar.isleap(self.yr_c)) & (~calendar.isleap(self.yr_c+1)):
            al_min = np.concatenate((min_bis, min_nbis), axis=0)
        elif (~calendar.isleap(self.yr_c)) & (calendar.isleap(self.yr_c+1)):
            al_min = np.concatenate((min_nbis, min_bis), axis=0)
        elif (~calendar.isleap(self.yr_c)) & (~calendar.isleap(self.yr_c+1)):
            al_min = np.concatenate((min_nbis, min_nbis), axis=0)

        return al_min, feh

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
        dato_c = qq_correction(self.ALMR[1:,:].copy(), 'ALMR', self.opera.dtimes,
                               self.opera.estacion)
        dato_c[np.isnan(self.ALMR[1:,:])] = np.nan
        self.ALMR[1:,:] = dato_c
