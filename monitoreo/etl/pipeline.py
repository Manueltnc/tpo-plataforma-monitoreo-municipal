# Proceso ETL completo (N19 a N23).
#   Extraer:     SUACI 2023 (CSV o ZIP)
#   Transformar: limpieza, tipos, nulos, fechas, agrupaciones, merge, join y concat
#   Cargar:      CSV, Excel y JSON en data/processed, mas el grafico de evolucion semanal
#
# Se corre una sola vez (python ejecutar_etl.py). Lo que deja es lo que usa el
# programa diario para saber que barrios tuvieron mas reclamos.

from monitoreo.app import barrios
from monitoreo.etl import cargar, extraer, transformar
from monitoreo.reportes import graficos


def ejecutar_etl(rutas):
    """Procesa el SUACI y deja los resultados en data/processed."""
    print('ETL - EXTRAER')
    crudo = extraer.leer_suaci(rutas)
    print(f'  Filas leidas: {len(crudo):,}')

    print('ETL - TRANSFORMAR')
    limpio, info = transformar.limpiar_suaci(crudo)
    print(f'  Sin barrio (descartadas): {info["sin_barrio"]:,}')
    print(f'  Barrio desconocido: {info["barrio_desconocido"]:,} | fecha invalida: {info["fecha_invalida"]:,}')
    print(f'  Filas limpias: {info["filas_limpias"]:,}')

    marcado = transformar.marcar_reclamos_clima(limpio)
    por_barrio = transformar.ordenar_por_reclamos(transformar.contar_por_barrio(marcado))
    semanal = transformar.serie_semanal(marcado)
    semestres = transformar.comparar_semestres(marcado)

    total_clima = int(marcado['es_clima'].sum())
    print(f'  Reclamos relacionados con el clima: {total_clima:,}')

    print('ETL - CARGAR')
    archivos = [
        cargar.guardar_csv(por_barrio, 'reclamos_por_barrio.csv'),
        cargar.guardar_json(por_barrio, 'reclamos_por_barrio.json'),
        cargar.guardar_csv(semanal.reset_index(), 'reclamos_clima_semanal.csv'),
        cargar.guardar_csv(semestres, 'comparacion_semestres.csv'),
        cargar.guardar_excel(
            {
                'reclamos por barrio': por_barrio,
                'por semana': semanal.reset_index(),
                'semestres': semestres,
            },
            'resumen_etl.xlsx',
        ),
    ]
    for ruta in archivos:
        print(f'  Guardado: {ruta.name}')

    # Comprobacion: el mismo resultado se puede leer desde CSV, JSON y Excel
    for nombre in ('reclamos_por_barrio.csv', 'reclamos_por_barrio.json', 'resumen_etl.xlsx'):
        leido = cargar.leer_resultado(cargar.ruta_de(nombre))
        print(f'  Lectura de control {nombre}: {leido.shape[0]} filas')

    ruta = graficos.grafico_evolucion_semanal(semanal)
    print(f'  Grafico: {ruta.name}')

    # El programa diario lee estos datos
    barrios.cargar_reclamos()

    return {'info': info, 'por_barrio': por_barrio, 'semanal': semanal, 'semestres': semestres}
