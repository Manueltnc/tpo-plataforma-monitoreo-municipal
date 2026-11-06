# E de ETL: traer los datos a DataFrames (N19, N21).
# Tres fuentes: archivo comprimido/CSV (SUACI), API (pronostico) y web (avisos).

from pathlib import Path

import pandas as pd

from monitoreo.app import config

# Solo leemos las columnas que usamos: el archivo completo pesa ~190 MB
COLUMNAS_SUACI = [
    'nro_solicitud', 'categoria', 'prestacion', 'fecha_ingreso',
    'barrio', 'comuna', 'canal', 'estado_general',
]


def buscar_archivos_suaci():
    """Busca CSV o ZIP en data/raw. Si no hay nada, usa la muestra de data/fixtures."""
    if config.DIR_RAW.exists():
        for patron in ('*.csv', '*.zip'):
            archivos = sorted(config.DIR_RAW.glob(patron))
            if archivos:
                return archivos

    print('  [etl] No hay archivos en data/raw: uso la muestra de data/fixtures.')
    return [config.RUTA_FIXTURE_SUACI]


def leer_suaci(rutas):
    """Lee uno o varios archivos del SUACI (.csv o .zip) y los junta en un DataFrame."""
    if isinstance(rutas, (str, Path)):
        rutas = [rutas]

    partes = []
    for ruta in rutas:
        print(f'  [etl] Leyendo {Path(ruta).name} ...')
        # compression='infer' (por defecto) descomprime solo si la extension es .zip
        parte = pd.read_csv(ruta, sep=';', usecols=COLUMNAS_SUACI, low_memory=False)
        partes.append(parte)

    return pd.concat(partes, ignore_index=True)


def pronostico_a_dataframe(dias):
    """Los dias que arma clima.resumir_por_dia pasan a DataFrame."""
    df = pd.DataFrame(dias)
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df


def avisos_a_dataframe(avisos):
    """Los avisos que arma avisos.limpiar_avisos pasan a DataFrame."""
    df = pd.DataFrame(avisos, columns=['titulo', 'enlace', 'fecha', 'fecha_iso', 'clases'])

    # 'clases' es una lista; la pasamos a texto para poder guardarla en CSV
    df['clases'] = df['clases'].apply(lambda c: ' '.join(c) if isinstance(c, list) else c)

    return df
