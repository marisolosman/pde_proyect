"""
09/04/2019 Creado por Felix Carrasco

This script contains functions to read, extract data from
grib2 files, contained in Pikachu database.

The datafiles correspond to 1999-2009 period of CFS data
with 120 days of forecast between 6 hours.

The project considers a forecast to 30 days.

The functions programmed in this grib_func.py 
allows to read for specific lat lon meteorological
station.
"""
import xarray as xr
import numpy as np
import pandas as pd
import datetime as dt
import glob

def extract_data_files(fname):
    """
    Extract the data from the filename. According to README in NOMADS
    the filename contains the following structure:

    <var>.<ensMem>.<yyyymmddhh t(i)>.<yyyymmddhh t(v)>.<yyyymmdd t(ic)>.grb2

    which means:

    var    : The output weather element
    t(i)   : Initialization or cycle run time.
    t(v)   : Final verification time of the series
    t(ic)  : Date/time of initial condition data used for forecast sequence.
    ensMem : Always/only 01 for this high-priority distribution.

    Each 00:00 UTC cycle contains a sequence of forecast records extended
    to approximately 2920 hours (or 4 months)
    Alternately for 06:00 / 12:00 / 18:00 UTC cycles:
    Each file contains a sequence of forecast records extending out
    to 1080 hours (45 days)
    Some fields, such as ocean, the t(ic) will differ from the t(i) by six
    hours.  in most cases, they are the same.

    """

    aux = fname.split('/')[5]  # Position of the filename
    filen = aux.split('.')
    dic = {'var':filen[0], 'ensMem':filen[1], 'ti':filen[2], 'tv':filen[3],\
           'tic':filen[4]}


    return dic
    

def gen_date_range(dfile):
    """
    Function to generate datetime index
    based on the data provided by the 
    name of the file.
    """
    yri = dfile['ti'][0:4]
    moi = dfile['ti'][4:6]
    dai = dfile['ti'][6:8]
    hri = dfile['ti'][8::]
    yrf = dfile['tv'][0:4]
    mof = dfile['tv'][4:6]
    daf = dfile['tv'][6:8]
    hrf = dfile['tv'][8::]
    strt = dt.datetime(int(yri), int(moi),
                       int(dai), int(hri),
                       0, 0)
    endt = dt.datetime(int(yrf), int(mof),
                       int(daf), int(hrf),
                       0, 0)

    f1 = pd.date_range(start=strt, end=endt, freq='6H')
    fecha = f1[1::]

    ymd = np.array(fecha.year*1e4 + fecha.month*1e2 +\
                   fecha.day, dtype=int)

    return fecha, ymd
    

def get_files(date, dic):
    """
    Function to return the list of the files corresponding for
    date given.

    date: datetime variable
    var: Variable to extract
    folder: Base folder to retrieve the files

    <var>.<ensMem>.<yyyymmddhh t(i)>.<yyyymmddhh t(v)>.<yyyymmdd t(ic)>.grb2
    """
    iv = dt.timedelta(days=1)
    d1 = (date - iv).replace(hour=18)
    d2 = date
    d3 = date.replace(hour=6)
    d4 = date.replace(hour=12)

    if np.logical_and(date.month == 1, date.day == 1):
        wkfolder = dic['dfolder'] + dic['var'] + '/' + str(date.year - 1) + '/'
        sd1 = d1.strftime('%Y%m%d%H')
        f1 = glob.glob(wkfolder + dic['var'] + '_f.01.' + sd1 + '*.grb2')
    else:
        wkfolder = dic['dfolder'] + dic['var'] + '/' + str(date.year - 1) + '/'
        sd1 = d1.strftime('%Y%m%d%H')
        f1 = glob.glob(wkfolder + dic['var'] + '_f.01.' + sd1 + '*.grb2')

    wkfolder = dic['dfolder'] + dic['var'] + '/' + str(date.year) + '/'
    sd2 = d2.strftime('%Y%m%d%H')
    f2 = glob.glob(wkfolder + dic['var'] + '_f.01.' + sd2 + '*.grb2')
    sd3 = d3.strftime('%Y%m%d%H')
    f3 = glob.glob(wkfolder + dic['var'] + '_f.01.' + sd3 + '*.grb2')
    sd4 = d4.strftime('%Y%m%d%H')
    f4 = glob.glob(wkfolder + dic['var'] + '_f.01.' + sd4 + '*.grb2')

    # Check if Glob get the file
    f = []
    if not f1:
        logfile = open(dic['lfile'], 'a')
        logfile.write('File for ' + sd1 + ' NOT FOUND \n')
        logfile.close()
    else:
        f.append(f1[0])
    if not f2:
        logfile = open(dic['lfile'], 'a')
        logfile.write('File for ' + sd2 + ' NOT FOUND \n')
        logfile.close()
    else:
        f.append(f2[0])
    if not f3:
        logfile = open(dic['lfile'], 'a')
        logfile.write('File for ' + sd3 + ' NOT FOUND \n')
        logfile.close()
    else:
        f.append(f3[0])
    if not f4:
        logfile = open(dic['lfile'], 'a')
        logfile.write('File for ' + sd4 + ' NOT FOUND \n')
        logfile.close()
    else:
        f.append(f4[0])
    
    return f


def get_daily_value(files, fecha, dic):
    """
    From the list of files given, it extracts
    one value for the date given

    - files: List of files
    - fecha: Date to use as a value
    - dic: Dictionary containing data from var, folders, etc
    """
    if not files:
        # If files is empty
        sd = fecha.strftime('%Y-%m-%d')
        logfile = open(dic['lfile'], 'a')
        logfile.write('There are no files for date: ' + sd + ' \n')
        logfile.write('returning NaN for specified date \n')
        logfile.close()
        valor = np.nan
    else:
        valores = []
        for item in files:
            d_file = extract_data_files(item)
            fecha, ymd = gen_date_range(d_file)
            grbs = xr.open_dataset(item, engine='pynio')
            print(grbs.data_vars)
            xe = np.array(dic['lon_e']) % 360  # Pasamos de [-180, 180] a [0, 360]
            ye = dic['lat_e']
            if var == 'tmax':
                data = grbs['TMAX_P0_L103_GGA0'].sel(lon_0=xe, lat_0=ye,
                                                     method='nearest')
                datos = data.values
                print(datos[0:10])



        valor = 381.7

    return valor


if __name__ == "__main__":

    import os
    # ############################################
    folder = '/datos2/CFSReana/'
    var    = 'tmax'  
    # Other options: tmax, tmin, dswsfc, pressfc
    #                tmp2m, wnd10m
    # Datos de fechas, estaciones y lugar para salidas
    yri = 1999
    yrf = 2010  # Entire period cover by database

    lat_e = [-27.45]  # Test con estacion Resistencia (Chaco, SMN)
    lon_e = [-59.05]
    n_est = ['resistencia']

    outfolder = '../pde_salidas/'
    os.makedirs(outfolder, exist_ok=True)
    # LogFile
    it = 0
    logfile = 'log_extract_variable_' + var + '_' + n_est[it] + '.log'
    f = open(outfolder + logfile, 'w')
    f.write('----------------------------------------------\n')
    f.write('\n')
    f.write('Archivo log para extraer datos desde GRIB \n')
    f.write('Este archivo extraer datos de variable: ' + var + '\n')
    f.write('Datos GRIB se encuentran en: ' + folder + '\n')
    f.write('Extraer datos para estacion: ' + n_est[it] + '\n')
    f.write('Salidas se encuentran en: ' + outfolder + '\n')
    f.write('----------------------------------------------\n')
    f.write('\n')
    f.close()
    # Diccionario con datos generales
    dic = {'lfile':outfolder+logfile, 'ofolder':outfolder,
            'dfolder':folder, 'var':var,
            'lat_e':lat_e[it], 'lon_e':lon_e[it],
            'n_est':n_est[it]}
    
    # -------------------------------------------------------
    # MAIN CODE 
    # -------------------------------------------------------
    f = open(outfolder + logfile, 'a')
    fecha = dt.datetime(1999,1,1)
    # --
    f.write('Working at date: ' + fecha.strftime('%Y-%m-%d') + '\n')
    f.close()
    # --
    files = get_files(fecha, dic)
    value = get_daily_value(files, fecha, dic)
    print(value)
    # --
    f = open(outfolder + logfile, 'a')
    f.write('############################\n')
    f.close()
    # --
    #for yr in np.arange(yri,yri+1):
    #    wrkfol = folder + var + '/' + str(yr) + '/'
    #    files = glob.glob(wrkfol + var + '*.grb2')
    #    files.sort(key = lambda x: x.split('.')[2])
    #    print('Trabajando en la carpeta: ' + wrkfol)
    #    for item in files[0:5]:
    #        print(item.split('/')[5])
    #        d_file = extract_data_files(item)
    #        fecha, ymd = gen_date_range(d_file)
    #        grbs = xr.open_dataset(item, engine='pynio')
    #        lon_e1 = np.array(lon_e) % 360  # Pasamos de [-180, 180] a [0, 360]
    #        data = grbs['TMAX_P0_L103_GGA0'].sel(lon_0=lon_e1[0],
    #                                             lat_0=lat_e[0],
    #                                             method='nearest')
    #        aux = data.dims[0]
    #        datos = data.values
    #        df = pd.DataFrame(index=np.arange(0, len(datos)))
    #        df = df.assign(fecha=fecha)
    #        df = df.assign(ymd=ymd)
    #        df = df.assign(var=datos)
    #        #dmax = df.groupby(by='ymd').max()
    #        print(fecha[0:5])
    #        print(datos[0:10])
    #        #print(dmax.head(5))
    #        print('------------------------------')
    #        #print((data[0:5].values))
    #        #it1, it2 = get_time_index(data)
            



