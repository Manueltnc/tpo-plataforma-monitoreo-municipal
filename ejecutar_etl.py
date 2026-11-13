# Corre el proceso ETL sobre el SUACI 2023 completo y deja los resultados en data/processed.
# Se corre una sola vez. El archivo (CSV o ZIP, ~190 MB) va en data/raw/.

from monitoreo.etl import extraer, pipeline

if __name__ == '__main__':
    archivos = extraer.buscar_archivos_suaci()

    if not archivos:
        print('No hay archivos del SUACI en data/raw.')
        print('Los resultados de data/processed ya estan hechos con el SUACI 2023 completo.')
        print('Para volver a generarlos, bajar el CSV (ver README) y ponerlo en data/raw.')
    else:
        pipeline.ejecutar_etl(archivos)
