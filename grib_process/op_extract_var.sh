#!/bin/sh

eval "$(conda shell.bash hook)"
conda activate py37
python --version

fecha='2003-05-'
for dia in 05 12 19 26
do
    for var in 'tmax' 'tmin' 'dswsfc' 'wnd10m' 'prate' 'hrmean'
    do
        python /home/felix.carrasco/pde_proyect/op_read_var.py $var $fecha$dia &
        pid=$!
        echo 'waiting for: '$pid
        wait $pid
        echo '--- Se termino de trabajar en: '$yy' ---'
        yy=$((yy + 1))
    done
done
