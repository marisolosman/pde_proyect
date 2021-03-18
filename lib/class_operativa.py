import glob
import pandas as pd
import numpy as np

from funciones_correccion import qq_correction, qq_correction_pp

np.seterr(divide='ignore', invalid='ignore')

class class_operativa:
    def __init__(self, est, fecha, corr, corr_pp='GG'):
        carpeta = '/home/osman/proyectos/pde_proyect/datos/datos_op/'
        self.estacion = est
        self.fecha = fecha
        self.carpeta = carpeta + est + '/' + fecha + '/'
        self.get_latlon()
        self.corr_pp = corr_pp
        self.nens = 16
        self.var = ['tmax', 'tmin','velviento', 'radsup', 'hrmean', 'precip']
        self.get_time()  # Obtenemos los tiempos del prono
        self.get_data(corr)  # Obtenemos los datos
        self.calc_etp()  # Calculamos la ETP

    def get_time(self):
        from datetime import datetime
        lf = glob.glob(self.carpeta + 'tmax*.txt')
        dateparse = lambda x: datetime.strptime(x, '%Y-%m-%d')
        df = pd.read_csv(lf[0], index_col=None, header=0, sep=';', decimal=',',
                         parse_dates=['fecha'], date_parser=dateparse)
        self.dtimes = df.fecha.dt.to_pydatetime()
        self.fecha_inicio = self.dtimes[0]

    def get_data(self, correccion):
        for vari in self.var:
            lf = glob.glob(self.carpeta + vari + '*.txt')
            dato = get_var_prono(lf, vari)
            if correccion:
                if vari == 'precip':
                    dato_c = qq_correction_pp(dato, self.dtimes, self.estacion, self.corr_pp)
                    dato_c[np.isnan(dato)] = np.nan
                else:
                    dato_c = qq_correction(dato, vari, self.dtimes, self.estacion)
                    dato_c[np.isnan(dato)] = np.nan
                setattr(self, vari, dato_c)
            else:
                setattr(self, vari, dato)

    def get_latlon(self):
        from netCDF4 import Dataset
        archivo = '/home/osman/proyectos/pde_proyect/datos/datos_hist/obs/tmax_199901_201012.nc'
        nc = Dataset(archivo, "r")
        Latitud = nc.variables[self.estacion].lat
        Longitud = nc.variables[self.estacion].lon
        nc.close()
        self.lat = Latitud
        self.lon = Longitud


    def calc_etp(self):
        from funciones_etp import calcularDr, calcularOmegaS, calcularRa, calcularDelta
        # Constantes
        GS = 0.082
        GAMMA = 0.067
        ALFA = 0.23
        SIGMA = 0.000000004903
        # Variables extras
        Latitud = self.lat
        julianos = np.array([float(j.timetuple().tm_yday) for j in self.dtimes])
        #Datos Extras
        dr = calcularDr(julianos)
        delta = calcularDelta(julianos)
        omega = calcularOmegaS(Latitud, delta)
        auxRa = calcularRa(julianos, Latitud, delta, omega)
        Ra = np.stack([auxRa for i in range(16)], axis=1)
        #### Viento 10m --> 2m -- 0.75 constante para pasar de 10m --> 2m
        viento2 = 0.75 * self.velviento

        # CALCULA TENSION DE VAPOR Y PENDIENTE DE SU CURVA
        Temp = 0.5 * (self.tmax + self.tmin)
        ES = 0.6108 * np.exp((17.27 * Temp) / (Temp + 237.3))
        EA = ES * self.hrmean / 100.
        Pend = 4098. * ES / np.power((Temp + 237.3), 2)

        ### CALCULA LA RADIACION RN
        RSO = 0.75 * Ra;
        RNS = (1. - ALFA) * self.radsup;
        dAux = (np.power(self.tmax + 273., 4) + np.power(self.tmin + 273., 4)) / 2.
        RNL = SIGMA * dAux * (0.34 - 0.14 * np.sqrt(EA)) *\
             (1.35 * self.radsup / RSO - 0.35)
        RN = RNS - RNL
        #
        ### CALCULA ETP en mm
        n1 = 0.408*Pend*RN + GAMMA*(900. / (Temp + 273.))*viento2*(ES - EA)
        n2 = Pend + GAMMA * (1. + 0.34 * viento2)
        ETP = n1/n2
        #in_etp = np.array([e < 0. if ~np.isnan(e) else False for e in ETP],
        #                   dtype=bool)
        ETP[ ETP < 0. ] = 0.
        setattr(self, 'etp', ETP)



# -------------------------------------------
#        OTRAS FUNCIONES AUXILIARES
# -------------------------------------------
def get_var_prono(prono_files, n_var):
    '''
This function add the ensemble members in one pandas
DataFrame. Name of the columns are the number of each ensemble.
    '''
    matriz = np.empty((30, 16))
    matriz[:] = np.nan
    for filename in prono_files:
        nens = int(filename.split('_')[3])
        df = pd.read_csv(filename, index_col=None, header=0,\
                         sep=';', decimal=',')
        matriz[:, nens] = df[n_var].to_numpy()
    #
    if n_var == 'tmax' or n_var == 'tmin':
        matriz = matriz - 273.
    return matriz
