# Corre el proceso ETL sobre el SUACI 2023 y deja los resultados en data/processed.
# Poner el archivo (CSV o ZIP) en data/raw/. Si no esta, usa una muestra chica.

from monitoreo.etl import pipeline

if __name__ == '__main__':
    pipeline.ejecutar_etl()
