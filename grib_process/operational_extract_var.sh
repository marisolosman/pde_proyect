#!/bin/sh

# eval "$(conda shell.bash hook)"
# conda activate py37
# python --version

fecha='2021-09-27'
#for dia in 02
#do
for var in 'tmax' 'tmin' 'dswsfc' 'wnd10m' 'prate' 'hrmean'
    do
        python /home/osman/proyectos/pde_proyect/grib_process/operational_read_var_par.py $var $fecha$dia &
        pid=$!
        echo 'waiting for: '$pid
        wait $pid
#        echo '--- Se termino de trabajar en: '$yy' ---'
#        yy=$((yy + 1))
done
#done
