# Graficos con DataFrame.plot() (N23). Se guardan como PNG en data/processed/graficos.

import matplotlib

matplotlib.use('Agg')   # solo guardamos imagenes, no abrimos ventanas
import matplotlib.pyplot as plt

from monitoreo.app import config

DIR_GRAFICOS = config.DIR_PROCESADOS / 'graficos'


def _guardar(ax, nombre):
    DIR_GRAFICOS.mkdir(parents=True, exist_ok=True)
    figura = ax.get_figure()
    figura.tight_layout()

    ruta = DIR_GRAFICOS / nombre
    figura.savefig(ruta, dpi=120)
    plt.close(figura)

    return ruta


def grafico_evolucion_semanal(semanal):
    ax = semanal[['reclamos', 'media_movil_4']].plot(
        figsize=(9, 4),
        title='Reclamos por sumideros y arbolado por semana (CABA 2023)',
    )
    ax.set_xlabel('Semana')
    ax.set_ylabel('Reclamos')

    return _guardar(ax, 'evolucion_semanal.png')


def grafico_ranking_barrios(por_barrio):
    top = por_barrio.nlargest(10, 'reclamos').sort_values('reclamos')
    ax = top.plot.barh(
        x='barrio', y='reclamos', legend=False, figsize=(8, 5),
        title='10 barrios con mas reclamos por sumideros y arbolado',
    )
    ax.set_xlabel('Reclamos en 2023')
    ax.set_ylabel('')

    return _guardar(ax, 'ranking_barrios.png')


def grafico_histograma(por_barrio):
    ax = por_barrio['reclamos'].plot.hist(
        bins=10, figsize=(7, 4),
        title='Distribucion de reclamos por barrio',
    )
    ax.set_xlabel('Reclamos en el barrio')
    ax.set_ylabel('Cantidad de barrios')

    return _guardar(ax, 'histograma_reclamos.png')


def grafico_semestres(comparacion):
    top = comparacion.assign(total=comparacion['semestre_1'] + comparacion['semestre_2'])
    top = top.nlargest(10, 'total')
    ax = top.plot.bar(
        x='barrio', y=['semestre_1', 'semestre_2'], figsize=(9, 5),
        title='Primer contra segundo semestre (10 barrios con mas reclamos)',
    )
    ax.set_xlabel('')
    ax.set_ylabel('Reclamos')

    return _guardar(ax, 'comparacion_semestres.png')
