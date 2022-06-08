#!/bin/bash

fecha=$(date -d "$date -1 day" '+%Y%m%d')
fecha="20220605"
cd /home/osman/proyectos/pde_proyect/bh_process/

/datos/osman/anaconda3/envs/pysol/bin/python /home/osman/proyectos/pde_proyect/bh_process/bh_operational_felix.py $fecha --correccion --method 'EG'

/datos/osman/anaconda3/envs/pysol/bin/python /home/osman/proyectos/pde_proyect/bh_process/bh_operational_felix.py $fecha

scp /datos/osman/datos_pde_project/FIGURAS/*${fecha}*.jpg osman@fiona:/datos2/prono_bh/


