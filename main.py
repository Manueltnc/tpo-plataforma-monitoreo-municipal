# Plataforma de monitoreo municipal de CABA
# Se corre una vez por dia: trae el pronostico, busca avisos oficiales, decide el
# nivel de riesgo de cada barrio, guarda el reporte y avisa por correo.
# Se corre desde la carpeta del proyecto con: python main.py

from monitoreo.app import barrios, config, reglas, servicio
from monitoreo.email import alertas
from monitoreo.etl import extraer
from monitoreo.reportes import graficos, reporte


def main():
    print('PLATAFORMA DE MONITOREO MUNICIPAL - CABA')
    print()

    if not barrios.hay_datos_de_reclamos():
        print('Aviso: falta data/processed/reclamos_por_barrio.csv (lo genera ejecutar_etl.py).')
        print('Sin ese archivo ningun barrio sube de nivel por sus reclamos.')
        print()

    # 1. Pronostico (API) + avisos oficiales (scraping) + nivel de cada barrio
    riesgo = servicio.riesgo_actual(usar_cache=False)

    print('PRONOSTICO PARA LA CIUDAD')
    for dia in riesgo['dias']:
        clima = reglas.nivel_del_clima(dia)
        print(f'  {servicio.fecha_legible(dia["fecha"])}: '
              f'lluvia {dia["lluvia_mm"]:.0f} mm, viento hasta {dia["viento_kmh"]:.0f} km/h, '
              f'de {dia["temp_min"]:.0f} a {dia["temp_max"]:.0f} grados '
              f'-> {reglas.NOMBRES_NIVEL[clima["nivel"]]}')
    print()

    print('AVISOS OFICIALES')
    scraping = riesgo['scraping']
    print(f'  {scraping["detalle"]}')
    print(f'  Noticias sobre el clima: {len(scraping["avisos"])}')
    for aviso in scraping['avisos']:
        print(f'  - {aviso["fecha"]}: {aviso["titulo"]}')
    print()

    print('BARRIOS')
    grupos = servicio.barrios_por_nivel(riesgo)
    for nivel in ['emergencia', 'alerta', 'atencion', 'normal']:
        lista = grupos[nivel]
        print(f'  {reglas.NOMBRES_NIVEL[nivel]} ({len(lista)}): {", ".join(lista) or "-"}')
    print()

    # 2. Reporte del dia y grafico del pronostico
    ruta_reporte = reporte.guardar_reporte(reporte.armar_reporte(riesgo))
    print(f'Reporte guardado en: {ruta_reporte}')

    pronostico = extraer.pronostico_a_dataframe(riesgo['dias'])
    pronostico['dia'] = [servicio.fecha_legible(fecha) for fecha in pronostico['fecha']]
    ruta_grafico = graficos.grafico_pronostico(pronostico)
    print(f'Grafico guardado en: {ruta_grafico}')

    # 3. Correos: reporte para la guardia y aviso a los vecinos de barrios en riesgo
    if config.ENVIAR_CORREOS:
        print()
        print('CORREOS')
        resultados = alertas.notificar(riesgo, ruta_reporte, ruta_grafico)

        if not resultados:
            print('  No hay correos para mandar (ningun vecino registrado en un barrio con riesgo).')

        for destino, resultado in resultados:
            print(f'  {destino}: {resultado["estado"]} - {resultado["detalle"]}')


if __name__ == '__main__':
    main()
