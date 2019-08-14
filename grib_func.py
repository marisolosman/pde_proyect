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


def get_files_hr(date, dic):
    """
    Function to return the list of the files corresponding for
    date given.

    date: datetime variable
    var: Variable to extract
    folder: Base folder to retrieve the files

    <var>.<ensMem>.<yyyymmddhh t(i)>.<yyyymmddhh t(v)>.<yyyymmdd t(ic)>.grb
    """

    logfile = open(dic['lfile'], 'a')
    iv = dt.timedelta(days=1)
    d1 = (date - iv).replace(hour=18)
    d2 = date
    d3 = date.replace(hour=6)
    d4 = date.replace(hour=12)

    vr = ['pressfc', 'q2m', 'tmp2m']
    outf = {}
    for var in vr:
        for dx in [d1, d2, d3, d4]:
            wkfolder = dic['dfolder'] + var + '/' + str(dx.year) + '/'
            sd1 = dx.strftime('%Y%m%d%H')
            f1 = glob.glob(wkfolder + var + '_f.01.' + sd1 + '*.grb2')
            lfls = []
            if not f1:
                logfile.write('File for ' + sd1 + ' NOT FOUND \n')
            else:
                lfls.append(f1[0])
                logfile.write('File: ' + f1[0] + ' ADDED \n')
        # End loop of dates
        outf[var] = lfls
    # End of LOOP
    logfile.close()

    return outf


def get_files_o(date, dic):
    """
    Function to obtain files to extract
    wmd10m, dswsfc, tmax, tmin
    In this case for these particular variables
    the idea is to get a file with prognostic
    for the four hours of the date and to work
    with those four values
    """
    lfls = []
    logfile = open(dic['lfile'], 'a')
    if date == dt.datetime(1999,1,1):
        d1 = date.replace(hour=0)
        wkfolder = dic['dfolder'] + dic['var'] + '/' + str(d1.year) + '/'
        sd1 = d1.strftime('%Y%m%d%H')
        f1 = glob.glob(wkfolder + dic['var'] + '_f.01.' + sd1 + '*grb2')
        if not f1:
            n_file = wkfolder + dic['var'] + '_f.01' + sd1
            logfile.write('File ' + sd1 + ' NOT FOUND\n')
        else:
            lfls.append(f1[0])
            logfile.write('File: ' + f1[0] + ' ADDED \n')
    else:
        # Test all dates from previous day and all hours
        iv = dt.timedelta(days=1)
        d1 = (date - iv).replace(hour=18) # forecast from previous day at 18
        d2 = (date - iv).replace(hour=12)
        d3 = (date - iv).replace(hour=6)
        d4 = (date - iv).replace(hour=0)
        wkfolder = dic['dfolder'] + dic['var'] + '/' + str(d1.year) + '/'
        for dx in [d1, d2, d3, d4]:
            sd1 = dx.strftime('%Y%m%d%H')
            n_file = wkfolder + dic['var'] + '_f.01.' + sd1
            f1 = glob.glob(n_file + '*.grb2')
            if not f1:
                logfile.write('File ' + sd1 + ' NOT FOUND \n')
            else:
                lfls.append(f1[0])
                logfile.write('File: ' + f1[0] + ' ADDED \n')

    logfile.close()

    return lfls


def get_ffiles(date, dic):
    """
    """
    

def get_daily_value(files, fecha, dic):
    """
    From the list of files given, it extracts
    one value for the date given

    - files: List of files
    - fecha: Date to use as a value
    - dic: Dictionary containing data from var, folders, etc
    """
    logfile = open(dic['lfile'], 'a')
    if not files:
        # If files is empty
        sd = fecha.strftime('%Y-%m-%d')
        logfile.write('There are no files for date: ' + sd + ' \n')
        logfile.write('returning NaN for specified date \n')
        logfile.close()
        valores = {dic['var'] + '_00': np.nan, dic['var'] + '_06': np.nan,
                   dic['var'] + '_12': np.nan, dic['var'] + '_18': np.nan}
    else:
        valores = {}
        fecha_d = []
        for item in files:
            d_file = extract_data_files(item)
            vec_date, ymd = gen_date_range(d_file)
            grbs = xr.open_dataset(item, engine='pynio')
            nvar = list(grbs.data_vars.keys())[0]
            xe = np.array(dic['lon_e']) % 360  # Pasamos de [-180, 180] a [0, 360]
            ye = dic['lat_e']
            data = grbs[nvar].sel(lon_0=xe, lat_0=ye, method='nearest')
            datos = data.values
            aux = [dt.datetime(a.year, a.month, a.day) for a in vec_date]
            idate = [a == fecha for a in aux]
            if var == 'tmax':
                valores[ dic['var'] + '_' + d_file['ti'][8::] ] = np.max(np.array(datos[idate]))
            elif var == 'tmin':
                valores[ dic['var'] + '_' + d_file['ti'][8::] ] = np.min(np.array(datos[idate]))
            else:
                valores[ dic['var'] + '_' + d_file['ti'][8::] ] = np.nan
        # End of LOOP


    return valores

def create_summary_file(dic, fval):
    """
    Function to create a summary file to save the results
    """

    columnas = ['fecha'] 
    columnas.extend([dic['var'] + '_' + hr for hr in ['00', '06', '12', '18']]) 
    df = pd.DataFrame(columns=columnas)
    df['fecha'] = fval
    #namefile = dic['ofolder'] + 'Summary_data_' + dic['n_est'] + '.txt'
    #df.to_csv(namefile, sep=';', float_format='%.3f', decimal=',')

    return df


def get_daily_value_hr(dfl, fecha, dic):
    """
    """

def get_daily_value_wnd(dfl, fecha, dic):
    """
    """

def get_daily_value_pp(dfl, fecha, dic):
    """
    """

if __name__ == "__main__":

    import os
    # ############################################
    folder = '/datos2/CFSReana/'
    var    = 'tmax'  
    # Other options: tmax, tmin, dswsfc,
    #                hr, wnd10m
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
    f.write('Se extraen datos de variable: ' + var + '\n')
    f.write('Datos GRIB se encuentran en: ' + folder + '\n')
    f.write('Extraer datos para estacion: ' + n_est[it] + '\n')
    f.write('Salidas se encuentran en: ' + outfolder + '\n')
    f.write('----------------------------------------------\n')
    f.write('\n')
    f.close()
    # Diccionario con datos generales
    dic = {'lfile':outfolder + logfile, 'ofolder':outfolder,
            'dfolder':folder, 'var':var,
            'lat_e':lat_e[it], 'lon_e':lon_e[it],
            'n_est':n_est[it]}
    
    # -------------------------------------------------------
    # MAIN CODE 
    # -------------------------------------------------------
    #f = open(outfolder + logfile, 'a')
    #fecha = dt.datetime(1999,10,6)
    fval = pd.date_range(start='1999-01-02', end='2010-12-31', freq='D').to_pydatetime().tolist()
    os.makedirs(outfolder + n_est[it], exist_ok=True)
    n_file = outfolder + n_est[it] + '/data_' + var  + '.txt'
    if os.path.isfile(n_file):
        df = pd.read_csv(n_file, sep=';', decimal=',', index_col=0)
    else:
        df = create_summary_file(dic, fval)
    for fecha in fval:
    # --
        f = open(outfolder + logfile, 'a')
        f.write('Working at date: ' + fecha.strftime('%Y-%m-%d') + '\n')
        f.close()
    # --
        if var == 'hr':
            files = get_files_hr(fecha, dic)
        else:
            files = get_files_o(fecha, dic)
            values = get_daily_value(files, fecha, dic)
            for k in values.keys():
                df.loc[df['fecha'] == fecha, k] = values[k]


    # --
    df = df.apply(pd.to_numeric, errors='ignore')
    df.to_csv(n_file, sep=';', float_format='%.4f', decimal=',')
    f = open(outfolder + logfile, 'a')
    f.write('######### THE END ##########\n')
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
            



