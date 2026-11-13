# Graficos con DataFrame.plot() (N23). Se guardan como PNG en data/processed/graficos.
#   - Evolucion semanal de reclamos (la pide la consigna): lo genera el ETL.
#   - Pronostico de los proximos dias contra los umbrales: va adjunto en el correo.

import matplotlib

matplotlib.use('Agg')   # solo guardamos imagenes, no abrimos ventanas
import matplotlib.pyplot as plt

from monitoreo.app import config


def guardar(figura, nombre):
    config.DIR_GRAFICOS.mkdir(parents=True, exist_ok=True)
    figura.tight_layout()

    ruta = config.DIR_GRAFICOS / nombre
    figura.savefig(ruta, dpi=120)
    plt.close(figura)

    return ruta


def grafico_evolucion_semanal(semanal):
    """Tendencia: reclamos por sumideros y arboles en cada semana de 2023."""
    ax = semanal[['reclamos', 'media_movil_4']].plot(
        figsize=(9, 4),
        title='Reclamos por sumideros y árboles en CABA, semana por semana (2023)',
    )
    ax.set_xlabel('Semana')
    ax.set_ylabel('Reclamos')
    ax.legend(['Reclamos de la semana', 'Promedio de las últimas 4 semanas'])

    return guardar(ax.get_figure(), 'evolucion_semanal.png')


def grafico_pronostico(pronostico):
    """Barras de lluvia y viento de los proximos dias, con una linea en cada umbral.
    pronostico es un DataFrame con las columnas dia, lluvia_mm y viento_kmh."""
    # nombres para que se lean bien en la leyenda del grafico
    pronostico = pronostico.rename(columns={'lluvia_mm': 'Lluvia prevista', 'viento_kmh': 'Viento previsto'})

    ejes = pronostico.plot.bar(
        x='dia',
        y=['Lluvia prevista', 'Viento previsto'],
        subplots=True,
        legend=False,
        figsize=(8, 6),
        rot=0,
        color=['tab:blue', 'tab:gray'],
        title=['Lluvia prevista (mm en el día)', 'Viento máximo previsto (km/h)'],
    )

    lineas = [
        (ejes[0], config.LLUVIA_ATENCION, config.LLUVIA_ALERTA, config.LLUVIA_EMERGENCIA, 'mm'),
        (ejes[1], config.VIENTO_ATENCION, config.VIENTO_ALERTA, config.VIENTO_EMERGENCIA, 'km/h'),
    ]

    for ax, atencion, alerta, emergencia, unidad in lineas:
        ax.axhline(atencion, color='gold', linestyle='--', label=f'Atención ({atencion} {unidad})')
        ax.axhline(alerta, color='orange', linestyle='--', label=f'Alerta ({alerta} {unidad})')
        ax.axhline(emergencia, color='red', linestyle='--', label=f'Emergencia ({emergencia} {unidad})')
        ax.set_xlabel('')
        ax.legend(loc='upper right', fontsize=8)

    return guardar(ejes[0].get_figure(), 'pronostico.png')
