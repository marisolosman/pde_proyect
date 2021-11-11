import os
import glob
import datetime as dt
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
from matplotlib.dates import MO, TU, WE, TH, FR, SA, SU
from matplotlib.ticker import MultipleLocator

mpl.rcParams['font.family'] = 'Arial'
mpl.rcParams['xtick.labelsize'] = 12
mpl.rcParams['ytick.labelsize'] = 12


def campaign_plot(bh):
    csfont = {'fontname':'Arial'}
    # Datos del grafico
    fecha = dt.datetime.strptime(bh.fecha, '%Y%m%d')
    estacion = bh.data_estacion['nombre']
    provincia = bh.data_estacion['prov']
    tipo_est = bh.data_estacion['tipoe']
    ini = bh.fecha_inicio_plot
    fin = bh.fecha_fin_plot
    ini_e = bh.fecha_inicio_excesos
    fin_e = bh.fecha_fin_excesos
    ini_d = bh.fecha_inicio_deficit
    fin_d = bh.fecha_fin_deficit
    CC = bh.clt_data['CC']
    PMP = bh.clt_data['PMP']
    alm_min, fecha_min = bh.calc_min_hist()

    #################################################################
    # COMENZAMOS LA FIGURA ##########
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 6))
    ax.axhline(CC, color='blue')  # Capacidad de campo
    ax.axhline(PMP, color='brown')  # Punto Marchitez Permanente
    # minimo historico: linea punteada gris
    #ax[0].plot(clim_times, min_historico.values, color='black', linestyle=(0, (5, 10)),
    #           alpha=0.3)
    # intervalor normal
    #ax[0].plot(clim_times, int_norm_inf, color='black', alpha=0.3)
    #ax[0].plot(clim_times, int_norm_sup, color='black', alpha=0.3)

    # período critico exceso: linea celeste. periodo crifico deficit: linea amarilla
    xe = [ini_e, ini_e, fin_e, fin_e]
    xd = [ini_d, ini_d, fin_d, fin_d]
    ye = [0, CC*1.1, CC*1.1, 0]
    color_e = [0.,204./255.,1., 0.6]
    color_d = [255./255.,204./255.,0, 0.6]
    ax.fill_between(xe, ye, facecolor=color_e, alpha=0.3, hatch='/',
                    label=u'Período crítico exceso hídrico', color=color_e, zorder=0)
    ax.fill_between(xd, ye, facecolor=color_d, alpha=0.3, hatch='/',
                    label=u'Período crítico déficit hídrico', color=color_d, zorder=0)
    # observado
    ax.plot(bh.fecha_obs, bh.almr_obs,'k',linewidth=2, zorder=1, label='Almacenaje estimado')
    ax.plot(fecha_min,alm_min, '--', linewidth=1.5, zorder=1, label='Mínimo histórico')
    # Eje Y
    ax.set_ylim(0, CC*1.2)
    ax.set_ylabel(u'Milímetros', fontsize=10, **csfont)
    #ax.yaxis.grid(True, linestyle='--', color='gray', alpha=0.3)
    # Eje X
    ax.set_xlim(ini, fin)
    loc = mdates.WeekdayLocator(byweekday=(MO))
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(DateFormatter("%d %b"))
    ax.tick_params(axis='x', which='major', labelsize=7, rotation=45)
    ax.set_xlabel('Fecha', fontsize=10, **csfont)
    ax.xaxis.grid(True, linestyle='--', color='gray', alpha=0.3)
    # Posicion del Eje
    pos = ax.get_position()
    pos.x0=0.1; pos.x1=0.95;pos.y0=0.105;pos.y1=0.72
    ax.set_position(pos) # set a new position
    # Detalles del Eje
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    # Texto del Eje
    titulo = 'Perspectiva de la reserva de agua en el suelo'
    subtitulo = 'Estación: ' + estacion + ', ' + provincia +\
                ' (' + tipo_est + ')' +  '\nInicio Pron: ' + fecha.strftime('%Y-%m-%d')
    fig.text(0.1, 0.95, titulo, fontsize=14, fontweight='bold', fontname='Arial')
    fig.text(0.1, 0.85, subtitulo, fontsize=14, fontname='Arial')


    return fig, ax
