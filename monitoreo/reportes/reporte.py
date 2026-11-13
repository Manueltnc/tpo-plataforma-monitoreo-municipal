# Reporte diario (Markdown) para la guardia municipal.
# Junta en un solo archivo lo que dio la API del clima, lo que encontro el scraping
# y el nivel de cada barrio. Se guarda en data/processed/reportes/reporte_FECHA.md

from datetime import date

from monitoreo.app import config, reglas, servicio


def tabla(encabezados, filas):
    """Arma una tabla en formato Markdown."""
    texto = '| ' + ' | '.join(encabezados) + ' |\n'
    texto += '|' + '---|' * len(encabezados) + '\n'

    for fila in filas:
        texto += '| ' + ' | '.join(str(valor) for valor in fila) + ' |\n'

    return texto


def armar_reporte(riesgo):
    """riesgo es lo que devuelve servicio.riesgo_actual()."""
    grupos = servicio.barrios_por_nivel(riesgo)
    scraping = riesgo['scraping']

    texto = '# Reporte diario de riesgo por clima - CABA\n\n'
    texto += f'Generado el {riesgo["actualizado"]}.\n\n'

    # 1. Barrios por nivel
    texto += '## 1. Cómo están los barrios\n\n'
    for nivel in ['emergencia', 'alerta', 'atencion', 'normal']:
        nombre = reglas.NOMBRES_NIVEL[nivel]
        lista = grupos[nivel]

        if lista:
            texto += f'- **{nombre}** ({len(lista)} barrios): {", ".join(lista)}\n'
        else:
            texto += f'- **{nombre}**: ningún barrio\n'

    # 2. Pronostico de la ciudad (API)
    texto += '\n## 2. Pronóstico para la ciudad (OpenWeather)\n\n'
    filas = []
    for dia in riesgo['dias']:
        clima = reglas.nivel_del_clima(dia)
        filas.append([
            servicio.fecha_legible(dia['fecha']),
            f'{dia["lluvia_mm"]:.0f} mm',
            f'{dia["viento_kmh"]:.0f} km/h',
            f'{dia["temp_min"]:.0f} a {dia["temp_max"]:.0f} grados',
            reglas.NOMBRES_NIVEL[clima['nivel']],
        ])
    texto += tabla(['Día', 'Lluvia', 'Viento máximo', 'Temperatura', 'Nivel por el clima'], filas)

    # 3. Avisos oficiales (scraping)
    texto += '\n## 3. Avisos oficiales sobre el clima\n\n'
    texto += scraping['detalle'] + '\n\n'
    if scraping['avisos']:
        filas = []
        for aviso in scraping['avisos']:
            filas.append([aviso['fecha'], f'[{aviso["titulo"]}]({aviso["enlace"]})'])
        texto += tabla(['Fecha', 'Noticia'], filas)
    elif scraping['usado']:
        texto += 'Ninguna noticia habla del clima.\n'

    # 4. Que hacer en cada nivel
    texto += '\n## 4. Qué se le recomienda al vecino\n\n'
    filas = []
    for nivel in reglas.NIVELES:
        filas.append([reglas.NOMBRES_NIVEL[nivel], reglas.RECOMENDACIONES[nivel]])
    texto += tabla(['Nivel', 'Recomendación'], filas)

    # 5. Como se decide el nivel
    texto += '\n## 5. Cómo se decide el nivel\n\n'
    texto += (
        f'1. **El clima define el nivel.** Lluvia: atención desde {config.LLUVIA_ATENCION} mm, '
        f'alerta desde {config.LLUVIA_ALERTA} mm, emergencia desde {config.LLUVIA_EMERGENCIA} mm. '
        f'Viento: atención desde {config.VIENTO_ATENCION} km/h, alerta desde {config.VIENTO_ALERTA} km/h, '
        f'emergencia desde {config.VIENTO_EMERGENCIA} km/h. Se toma el peor de los dos.\n'
        f'2. **El barrio puede subir un nivel.** Si está entre los '
        f'{config.CANTIDAD_BARRIOS_CON_MAS_RECLAMOS} barrios con más reclamos por sumideros y árboles '
        f'en 2023 (SUACI), sube un nivel.\n'
    )

    return texto


def guardar_reporte(texto):
    config.DIR_REPORTES.mkdir(parents=True, exist_ok=True)
    ruta = config.DIR_REPORTES / f'reporte_{date.today()}.md'

    with open(ruta, 'w', encoding='utf-8') as archivo:
        archivo.write(texto)

    return ruta
