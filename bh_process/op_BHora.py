import glob
import time
import os

import pandas as pd
import numpy as np
import datetime as dt

import matplotlib.pyplot as plt

from etp_func import CalcularETPconDatos
from bhora_func import run_bh_ora
from extras_func import (gen_qq_corrected_precip, gen_qq_corrected_df, comparar_precip)
from plot_func import plot_check_prono
# Funciones
def get_var_prono(prono_folder, n_var):
    '''
    This function add the ensemble members in one pandas
    DataFrame. Name of the columns are the number of each ensemble.
    '''
    prono_files = glob.glob( prono_folder + n_var + '*.txt' )
    li = []

    for filename in prono_files:
        df = pd.read_csv(filename, index_col=None, header=0,\
                         sep=';', decimal=',')
        li.append(df[n_var])

    frame = pd.concat(li, axis=1, ignore_index=True)
    datos = pd.DataFrame(index=df.fecha, data=frame.values, dtype='float32')
    return datos


def get_df_to_ETP(iens, txp, tmp, hrp, rsp, vip, ppp):
    '''
    This function generates for the "iens" ensemble the DataFrame to
    calculate the ETP with the function CalcularETPconDatos:

    The output variable df, MUST contain the following column names:
    'Fecha', 'tmax', 'tmin', 'radsup', 'velviento', 'hr'

    Temperatures in Degree Celsius.
    '''
    fecha = txp.index
    vacio = False
    try:
        tx = txp.loc[:, iens] - 273.
    except:
        print('No existe el ensamble: ', iens, 'para Tmax')
        vacio = True
    try:
        tm = tmp.loc[:, iens] - 273.
    except:
        print('No existe el ensamble: ', iens, 'para Tmin')
        vacio = True
    try:
        hr = hrp.loc[:, iens]
    except:
        print('No existe el ensamble: ', iens, 'para HR')
        vacio = True
    try:
        vi = vip.loc[:, iens]
    except:
        print('No existe el ensamble: ', iens, 'para Velviento')
        vacio = True
    try:
        rs = rsp.loc[:, iens]
    except:
        print('No existe el ensamble: ', iens, 'para rs')
        vacio = True
    try:
        pp = ppp.loc[:, iens]
    except:
        print('No existe el ensamble: ', iens, 'para precip')
        vacio = True
    # ------------- work with variable columns ---------
    if not vacio:
        clnas = ['Fecha', 'tmax', 'tmin', 'radsup', 'velviento', 'hr', 'precip']
        datos = {'Fecha':fecha, 'tmax':tx.values,
                 'tmin':tm.values, 'radsup':rs.values,
                 'velviento':vi.values, 'hr':hr.values,
                 'precip':pp.values}
        df_out = pd.DataFrame(index=np.arange(0, len(fecha)),
                              columns=clnas, data=datos)
        df_out['Fecha'] = pd.to_datetime(df_out['Fecha'], format='%Y-%m-%d')
    else:
        df_out = pd.DataFrame({'A':[]})
    # --------
    return df_out


# ------------------------- INICIO CODIGO -------------------------------------#
# Contabilizamos el tiempo de realizacion del script
start = time.time()

# -----------------------------------
# INPUT
fecha = '2009-02-18'
tipo_bh = 'profundo'
estacion = 'resistencia'
id_est = '107'
tipo_estacion = 'SMN'
cultivo = 'S1-VII'
carpeta_datos = './datos/'
carpeta_prono = '../pde_salidas/'
con_correccion = True

# -----------------------------------
# Codigos de calculo
fecha_in = dt.datetime.strptime(fecha, '%Y-%m-%d')
fold_prono = carpeta_prono + estacion + '/' + fecha_in.strftime('%Y%m%d') + '/'

# Guardamos las variables de pronostico
tx_prono = get_var_prono(fold_prono, 'tmax')
tm_prono = get_var_prono(fold_prono, 'tmin')
hr_prono = get_var_prono(fold_prono, 'hrmean')
rs_prono = get_var_prono(fold_prono, 'radsup')
vi_prono = get_var_prono(fold_prono, 'velviento')
pp_prono = get_var_prono(fold_prono, 'precip')
#tx_prono.plot.bar()
#plt.show()
#comparar_precip(fecha, pp_prono)
#exit()


# Vamos iterando en cada ensamble y realizamos BH.
almr_array = []
almr_exc_array = []

for i_ens in range(0, 16):
    print('######## Trabajando en el ensamble: ', i_ens, ' #################')
    df_prono = get_df_to_ETP(i_ens, tx_prono, tm_prono, hr_prono, rs_prono,\
                             vi_prono, pp_prono)
    if df_prono.empty:
        break
    else:
        print('Calculamos ETP para ensamble: ' + str(i_ens))
        if con_correccion:
            print(' ######### QQ-correction a realizar en datos ##########')
            # --- Correccion a datos para ETP
            df_1 = gen_qq_corrected_df(df_prono, estacion)
            print(df_1.columns)
            # --- Calculo de ETP con datos corregidos
            etp_iens = CalcularETPconDatos(df_1, id_est)
            # --- Corregimos precipitacion
            datos_bh_o = gen_qq_corrected_precip(etp_iens, estacion,
                                                 'GG', **{'fix_val':1.})
            # Hacemos el balance hidrico
            kwargs = {'debug': False, 'fecha_inicial': True,
                      'ini_date':fecha_in - dt.timedelta(days=1)}
            bh_iens = run_bh_ora(datos_bh_o, id_est, cultivo, tipo_bh, **kwargs)
        else:
            etp_iens = CalcularETPconDatos(df_prono, id_est)
            # Arreglar bien el tema de la CondicionInicial en el BH.
            kwargs = {'debug': False, 'fecha_inicial': True,
                      'ini_date':fecha_in - dt.timedelta(days=1)}
            datos_bh_o = etp_iens.loc[:, ['Fecha', 'precip', 'ETP']]
            bh_iens = run_bh_ora(datos_bh_o, id_est, cultivo, tipo_bh, **kwargs)
        # --- Final del IF para trabajar con correccion o no ---
        # Guardamos las columnas necesarias para los graficos.
        almr_array.append(bh_iens['ALMR'])
        almr_exc_array.append(bh_iens['ALMR'] + bh_iens['EXC'])
# Fin Loop miembros ensamble
frame = pd.concat(almr_array, axis=1, ignore_index=True)
almr_prono = pd.DataFrame(index=bh_iens.Fecha, data=frame.values, dtype='float32')

frame = pd.concat(almr_exc_array, axis=1, ignore_index=True)
almr_exc_prono = pd.DataFrame(index=bh_iens.Fecha, data=frame.values, dtype='float32')


plot_check_prono(almr_prono, id_est, estacion, cultivo, tipo_bh)

#print(almr_prono)
#almr_prono.plot()
#plt.show()

#almr_exc_prono.plot()
#plt.show()

# Contabilizamos el tiempo requerido
end = time.time()
print(end - start)
