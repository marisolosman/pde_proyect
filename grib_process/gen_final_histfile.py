import pandas as pd
import numpy as np
import glob
import os


folder = '../../pde_salidas/yearly_data/junin/'
variables = ['hr', 'precip', 'radsup', 'tmax', 'tmin', 'velviento']
folder_s = '../datos/datos_hist/modelo/junin/'
os.makedirs(folder_s, exist_ok=True)
for var in variables:
    txt0 = folder + 'data_' + var + '_*.txt'
    archivos = glob.glob(txt0)
    arrayc = [pd.read_csv(f, sep=';', decimal=',', index_col=0) for f in archivos]
    big_frame = pd.concat(arrayc, ignore_index=True)
    big_frame = big_frame.sort_values(by='fecha')
    big_frame.reset_index(drop=True, inplace=True)
    if var == 'hr':
        var = 'hrmean'
    sel_col = list(big_frame)[1::]
    big_frame[sel_col] = big_frame[sel_col].apply(pd.to_numeric, errors='ignore')
    archivo = folder_s + 'data_final_' + var + '.txt'
    big_frame.to_csv(archivo, sep=';', decimal=',', float_format='%.2f', date_format='%Y-%m-%d')
