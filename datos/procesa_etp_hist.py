
import pandas as pd
import sys
sys.path.append('../lib/')
from class_historico import class_historico
sys.path.append('../mdb_process/')
from etp_func import CalcularETPconDatos

estacion = 'resistencia'
id = '107'
df = class_historico(estacion)
dic = df.datos_mod
dic['Fecha'] = df.dtimes
ds = pd.DataFrame(data=dic)
ds1 = CalcularETPconDatos(ds, id)
print(ds1.head())
