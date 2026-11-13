# L de ETL: guardar los resultados en CSV, Excel y JSON, y volver a leerlos (N19, N21).

import pandas as pd

from monitoreo.app import config


def ruta_de(nombre):
    config.DIR_PROCESADOS.mkdir(parents=True, exist_ok=True)
    return config.DIR_PROCESADOS / nombre


def guardar_csv(df, nombre):
    ruta = ruta_de(nombre)
    df.to_csv(ruta, index=False, encoding='utf-8')
    return ruta


def guardar_excel(hojas, nombre):
    """hojas es un diccionario {nombre de hoja: DataFrame}."""
    ruta = ruta_de(nombre)

    with pd.ExcelWriter(ruta, engine='openpyxl') as escritor:
        for hoja, df in hojas.items():
            df.to_excel(escritor, sheet_name=hoja[:31], index=False)

    return ruta


def guardar_json(df, nombre):
    ruta = ruta_de(nombre)
    df.to_json(ruta, orient='records', force_ascii=False, indent=2, date_format='iso')
    return ruta


def leer_resultado(ruta):
    """Lee un resultado ya guardado, sea CSV, Excel o JSON."""
    ruta = str(ruta)

    if ruta.endswith('.csv'):
        return pd.read_csv(ruta)
    elif ruta.endswith('.xlsx'):
        return pd.read_excel(ruta)
    elif ruta.endswith('.json'):
        return pd.read_json(ruta)

    raise ValueError(f'Formato no soportado: {ruta}')
