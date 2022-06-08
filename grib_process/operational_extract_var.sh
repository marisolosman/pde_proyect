#!/bin/bash

fecha=$(date '+%Y-%m-%d')
for var in 'tmax' 'tmin' 'dswsfc' 'wnd10m' 'prate' 'hrmean'; do 
	/datos/osman/anaconda3/envs/pysol/bin/python /home/osman/proyectos/pde_proyect/grib_process/operational_read_var_par.py $var $fecha 
done

