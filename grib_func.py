"""
09/04/2019 Creado por Felix Carrasco

This script contains functions to read, extract data from
grib2 files, contained in Pikachu database.

The datafiles correspond to 1999-2009 period of CFS data
with 45 days of forecast.

The functions programmed in this grib_func.py 
allows to read for specific lat lon meteorological
station.
"""

if __name__ == "__main__":

    import glob
    import xarray as xr
    import numpy as np
    import pandas as pd
