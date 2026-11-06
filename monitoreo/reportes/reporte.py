# Reporte integrado: junta en un solo documento el indicador de riesgo, la consulta
# a la API del clima y el resultado del scraping, mas el contexto historico del ETL.

from datetime import date

from monitoreo.app import barrios, config
from monitoreo.etl import cargar

DIR_REPORTES = config.DIR_PROCESADOS / 'reportes'


def _tabla(encabezados, filas):
    texto = '| ' + ' | '.join(encabezados) + ' |\n'
    texto += '|' + '|'.join(['---'] * len(encabezados)) + '|\n'

    for fila in filas:
        texto += '| ' + ' | '.join(str(valor) for valor in fila) + ' |\n'

    return texto


def armar_reporte(riesgo, avisos_todos, avisos_importantes, scraping_usado):
    """Devuelve el texto (Markdown) del reporte. riesgo es lo que devuelve servicio.riesgo_actual()."""
    dia = riesgo['dia']
    conteo = riesgo['conteo']
    resultados = riesgo['resultados']

    texto = f'# Reporte de riesgo urbano - CABA - {date.today()}\n\n'

    # 1. Resumen
    texto += '## 1. Resumen\n\n'
    texto += f'Dia evaluado: **{dia["fecha"]}** (el de mayor lluvia prevista).\n\n'
    texto += _tabla(
        ['Emergencia', 'Alerta', 'Atencion', 'Normal'],
        [[conteo['emergencia'], conteo['alerta'], conteo['atencion'], conteo['normal']]],
    )

    # 2. API del clima
    texto += '\n## 2. Pronostico (API OpenWeather)\n\n'
    filas = []
    for d in riesgo['dias']:
        filas.append([
            d['fecha'], f'{d["lluvia_mm"]:.1f}', f'{d["viento_kmh"]:.0f}',
            f'{d["temp_min"]:.1f} a {d["temp_max"]:.1f}',
        ])
    texto += _tabla(['Fecha', 'Lluvia (mm)', 'Viento max (km/h)', 'Temperatura (C)'], filas)

    # 3. Scraping
    texto += '\n## 3. Avisos oficiales (scraping)\n\n'
    if not scraping_usado:
        texto += 'El scraping esta desactivado o no se pudo realizar en esta corrida.\n'
    else:
        texto += f'Noticias leidas: {len(avisos_todos)}. Importantes para el sistema: {len(avisos_importantes)}.\n\n'
        if avisos_importantes:
            filas = [[a['fecha'], a['titulo']] for a in avisos_importantes]
            texto += _tabla(['Fecha', 'Titulo'], filas)
        else:
            texto += 'Ninguna noticia contiene palabras clave de emergencia.\n'

    # 4. Indicador
    texto += '\n## 4. Indice de riesgo por barrio (los 10 mas altos)\n\n'
    ordenados = sorted(resultados, key=lambda fila: fila['puntos'], reverse=True)[:10]
    filas = []
    for fila in ordenados:
        filas.append([
            fila['barrio'], fila['nivel'], fila['puntos'], fila['peligro'],
            f'{fila["factor"]:.2f}', '; '.join(fila['motivos']) or '-',
        ])
    texto += _tabla(['Barrio', 'Nivel', 'Indice', 'Peligro', 'Factor', 'Motivos'], filas)

    # 5. Contexto historico (ETL)
    texto += '\n## 5. Contexto historico (SUACI 2023, ETL con Pandas)\n\n'
    ruta = config.DIR_PROCESADOS / 'vulnerabilidad_barrios.csv'
    if ruta.exists():
        historial = cargar.leer_resultado(ruta).head(5)
        filas = [[f['barrio'], f['reclamos'], f'{f["participacion_pct"]}%', f['factor_vulnerabilidad']]
                 for _, f in historial.iterrows()]
        texto += 'Barrios con mas reclamos por sumideros, calles anegadas y arbolado:\n\n'
        texto += _tabla(['Barrio', 'Reclamos 2023', 'Del total', 'Factor'], filas)
        texto += '\n![Evolucion semanal](../graficos/evolucion_semanal.png)\n\n'
        texto += '![Ranking de barrios](../graficos/ranking_barrios.png)\n'
    else:
        texto += 'Todavia no se corrio el ETL (ejecutar_etl.py), asi que el factor de vulnerabilidad es neutro.\n'

    # 6. Metodologia
    texto += '\n## 6. Como se calcula\n\n'
    texto += ('Indice = peligro meteorologico (lluvia y viento previstos, 0 a 100) x factor de '
              'vulnerabilidad del barrio (0.75 a 1.25, segun sus reclamos historicos). '
              f'Cortes: atencion {config.CORTE_ATENCION}, alerta {config.CORTE_ALERTA}, '
              f'emergencia {config.CORTE_EMERGENCIA}. Detalle en el README.\n')

    return texto


def guardar_reporte(texto):
    DIR_REPORTES.mkdir(parents=True, exist_ok=True)
    ruta = DIR_REPORTES / f'reporte_{date.today()}.md'

    with open(ruta, 'w', encoding='utf-8') as archivo:
        archivo.write(texto)

    return ruta
