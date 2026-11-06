# Proceso ETL completo (N19 a N23).
#   Extraer:    SUACI 2023 (CSV o ZIP), pronostico (API) y avisos (web)
#   Transformar: limpieza, tipos, nulos, fechas, agrupaciones, merge/join/concat
#   Cargar:     CSV, Excel y JSON en data/processed + graficos

import pandas as pd

from monitoreo.app import barrios
from monitoreo.etl import cargar, extraer, transformar
from monitoreo.reportes import graficos


def ejecutar_etl(rutas=None, con_graficos=True):
    """Procesa el SUACI y deja todos los resultados en data/processed."""
    print('ETL - EXTRAER')
    rutas = rutas or extraer.buscar_archivos_suaci()
    crudo = extraer.leer_suaci(rutas)
    print(f'  Filas leidas: {len(crudo):,}')

    print('ETL - TRANSFORMAR')
    limpio, info = transformar.limpiar_suaci(crudo)
    print(f'  Sin barrio (descartadas): {info["sin_barrio"]:,}')
    print(f'  Barrio desconocido: {info["barrio_desconocido"]:,} | fecha invalida: {info["fecha_invalida"]:,}')
    print(f'  Filas limpias: {info["filas_limpias"]:,}')

    marcado = transformar.marcar_reclamos_clima(limpio)
    por_barrio = transformar.calcular_vulnerabilidad(transformar.contar_por_barrio(marcado))
    semanal = transformar.serie_semanal(marcado)
    comparacion = transformar.comparar_semestres(marcado)
    barrio_mes = transformar.reclamos_barrio_mes(marcado)
    categorias = transformar.resumen_categorias(limpio)

    total_clima = int(marcado['es_clima'].sum())
    print(f'  Reclamos relacionados con el clima: {total_clima:,}')

    print('ETL - CARGAR')
    archivos = [
        cargar.guardar_csv(por_barrio, 'vulnerabilidad_barrios.csv'),
        cargar.guardar_csv(semanal.reset_index(), 'reclamos_clima_semanal.csv'),
        cargar.guardar_csv(comparacion, 'comparacion_semestres.csv'),
        cargar.guardar_csv(barrio_mes, 'reclamos_clima_barrio_mes.csv'),
        cargar.guardar_json(por_barrio, 'vulnerabilidad_barrios.json'),
        cargar.guardar_excel(
            {
                'vulnerabilidad': por_barrio,
                'semanal': semanal.reset_index(),
                'semestres': comparacion,
                'barrio_mes': barrio_mes,
                'categorias': categorias,
            },
            'resumen_etl.xlsx',
        ),
    ]
    for ruta in archivos:
        print(f'  Guardado: {ruta.name}')

    # Comprobacion: el mismo resultado se puede leer desde CSV, JSON y Excel
    for nombre in ('vulnerabilidad_barrios.csv', 'vulnerabilidad_barrios.json', 'resumen_etl.xlsx'):
        leido = cargar.leer_resultado(cargar._ruta(nombre))
        print(f'  Lectura de control {nombre}: {leido.shape[0]} filas')

    if con_graficos:
        for ruta in (
            graficos.grafico_evolucion_semanal(semanal),
            graficos.grafico_ranking_barrios(por_barrio),
            graficos.grafico_histograma(por_barrio),
            graficos.grafico_semestres(comparacion),
        ):
            print(f'  Grafico: {ruta.name}')

    # El indicador de riesgo lee estos factores
    barrios.cargar_vulnerabilidad()

    return {
        'info': info,
        'por_barrio': por_barrio,
        'semanal': semanal,
        'comparacion': comparacion,
        'barrio_mes': barrio_mes,
        'categorias': categorias,
    }


def cargar_api_y_web(dias, avisos):
    """Guarda el pronostico (API) y los avisos (web) como tablas, junto a lo del SUACI."""
    pronostico = extraer.pronostico_a_dataframe(dias)
    tabla_avisos = extraer.avisos_a_dataframe(avisos)

    cargar.guardar_csv(pronostico, 'pronostico_actual.csv')
    cargar.guardar_csv(tabla_avisos, 'avisos_actuales.csv')

    return pronostico, tabla_avisos


def combinar_riesgo_con_historial(resultados):
    """merge: une el riesgo de hoy con los reclamos historicos de cada barrio."""
    riesgo = pd.DataFrame(resultados)[['barrio', 'puntos', 'nivel']]
    historial = cargar.leer_resultado(cargar._ruta('vulnerabilidad_barrios.csv'))

    return riesgo.merge(historial, on='barrio', how='left')
