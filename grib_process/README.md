This folder contains programs to process reforecast and real time CFS V2 data

- The code *select station.py* takes reforecast data from CFS v2 fot eh 1999-201o period and the coords and name of the station and generates the txt files needed to calibrate forecast

- the code *operational_read_var_par.py* takes selected date and station from 2011-present and generate the txt files of the operational forecasts that are later calibrated. It has been paralellized and now each station and date take ~ min to be processed. Use this one instead of *operationa_read_var.py*

- The code *arrange_forecast_data.py* preprocess the forecasts for the period 2011-2021

