# Plataforma de monitoreo municipal de CABA
# Trae el clima, scrapea los avisos oficiales, calcula el riesgo por barrio
# y arma un reporte que junta todo y se manda por correo.
# Se corre desde la carpeta del proyecto con: python main.py

import requests

from monitoreo.app import barrios, config, reglas, servicio
from monitoreo.email import alertas as correo
from monitoreo.etl import pipeline
from monitoreo.reportes import reporte
from monitoreo.scraping import avisos


def main():
    print('PLATAFORMA DE MONITOREO MUNICIPAL - CABA')
    print()

    if not barrios.hay_datos_vulnerabilidad():
        print('Falta el resultado del ETL: lo genero ahora (tarda unos segundos).')
        pipeline.ejecutar_etl()
        print()

    # 1. Avisos del sitio oficial
    print('AVISOS OFICIALES')
    todos, importantes = [], []
    scraping_usado = False

    if config.SCRAPING_ACTIVO:
        try:
            html = avisos.bajar_html(config.URLS_OFICIALES[0])
            todos, importantes = avisos.obtener_avisos(html)
            scraping_usado = True
        except requests.exceptions.RequestException as error:
            print(f'  No se pudo bajar el sitio: {error}')
            html = ''

        if scraping_usado:
            print(f'  Noticias encontradas: {len(todos)}')
            print(f'  Importantes para el sistema: {len(importantes)}')

            for aviso in importantes:
                print(f'  - {aviso["fecha"]}: {aviso["titulo"]}')
            print()

            print('BUSQUEDAS CON find_all')
            avisos.mostrar_busquedas(html)
    else:
        print('  Scraping desactivado por configuracion.')
    print()

    # 2. Pronostico del clima
    print('PRONOSTICO')
    riesgo = servicio.riesgo_actual(usar_cache=False)

    for dia in riesgo['dias']:
        print(f'  {dia["fecha"]}: {dia["lluvia_mm"]:.1f} mm, '
              f'viento {dia["viento_kmh"]:.0f} km/h, '
              f'de {dia["temp_min"]:.1f} a {dia["temp_max"]:.1f} grados')
    print()

    # 3. Riesgo por barrio
    print(f'RIESGO POR BARRIO (dia evaluado: {riesgo["dia"]["fecha"]})')

    for nivel in ['emergencia', 'alerta', 'atencion', 'normal']:
        print(f'  {nivel}: {riesgo["conteo"][nivel]} barrios')
    print()

    # 4. Alertas de los barrios que no estan en normal
    print('ALERTAS')
    hay_alertas = False

    for fila in riesgo['resultados']:
        if fila['nivel'] != 'normal':
            print(barrios.armar_mensaje(
                fila['barrio'],
                'riesgo urbano',
                fila['nivel'],
                fila['puntos'],
                fila['motivos'],
            ))
            print(f'  {reglas.que_hacer(fila["nivel"])}')
            print()
            hay_alertas = True

    if not hay_alertas:
        print('  Ningun barrio supera el umbral de atencion.')
    print()

    # 5. Reporte integrado: indicador + API + scraping + historial del ETL
    pipeline.cargar_api_y_web(riesgo['dias'], todos)
    texto = reporte.armar_reporte(riesgo, todos, importantes, scraping_usado)
    ruta = reporte.guardar_reporte(texto)
    print(f'REPORTE INTEGRADO guardado en: {ruta}')

    # 6. Correo: reporte con adjuntos y, si hay barrios en alerta, aviso de alerta
    if config.ENVIAR_CORREOS:
        print()
        print('CORREOS')

        for nombre, resultado in correo.notificar(riesgo, ruta):
            print(f'  {nombre}: {resultado["estado"]} - {resultado["detalle"]}')


if __name__ == '__main__':
    main()
