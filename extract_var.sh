#!/bin/sh

eval "$(conda shell.bash hook)"
conda activate py37
python --version


for var in 'tmax' 'tmin' 'dswsfc' 'wnd10m' 'prate' 'hrmean' 
do
    yy=2002
    while [ "$yy" -lt 2011 ] 
    do
	python /home/felix.carrasco/pde_proyect/read_var.py $yy $var &
	pid=$!
	echo 'waiting for: '$pid
	wait $pid
	echo '--- Se termino de trabajar en: '$yy' ---'
	yy=$((yy + 1))
    done
done
