# T de ETL: limpieza, tipos, nulos, agregaciones, fechas y combinaciones
# (N20, N22).

import numpy as np
import pandas as pd

from monitoreo.app import barrios, config


def limpiar_suaci(df):
    """Limpia el SUACI y devuelve (DataFrame limpio, resumen de lo descartado)."""
    df = df.copy()
    info = {'filas_originales': len(df)}

    # Nulos: sin barrio no se puede asignar el reclamo a ningun lado
    info['sin_barrio'] = int(df['barrio'].isna().sum())
    df = df.dropna(subset=['barrio'])

    # Nombres de barrio: se normaliza sobre los valores unicos (son 48, no 800 mil)
    mapa = {nombre: barrios.validar_barrio(nombre) for nombre in df['barrio'].unique()}
    df['barrio'] = df['barrio'].map(mapa)
    info['barrio_desconocido'] = int(df['barrio'].isna().sum())
    df = df.dropna(subset=['barrio'])

    # Fechas: texto a datetime. Lo que no se puede convertir queda NaT y se descarta
    df['fecha'] = pd.to_datetime(df['fecha_ingreso'], errors='coerce')
    info['fecha_invalida'] = int(df['fecha'].isna().sum())
    df = df.dropna(subset=['fecha'])

    # Faltantes y tipos
    df['canal'] = df['canal'].fillna('Sin dato')
    df['comuna'] = df['comuna'].fillna(0).astype(int)
    for columna in ('categoria', 'canal', 'estado_general'):
        df[columna] = df[columna].astype('category')

    # Texto de la prestacion normalizado, para buscar palabras sin problemas de tildes
    mapa_prestacion = {p: barrios.normalizar(p) for p in df['prestacion'].dropna().unique()}
    df['prestacion_norm'] = df['prestacion'].map(mapa_prestacion).fillna('')

    df = df.drop(columns=['fecha_ingreso'])
    info['filas_limpias'] = len(df)

    return df.reset_index(drop=True), info


def marcar_reclamos_clima(df):
    """Agrega la columna es_clima: True si el reclamo esta relacionado con lluvia o viento."""
    patron = '|'.join(config.PATRONES_RECLAMOS_CLIMA)
    df = df.copy()
    df['es_clima'] = df['prestacion_norm'].str.contains(patron, regex=True)

    return df


def contar_por_barrio(df):
    """Reclamos relacionados con el clima por barrio. Salen siempre los 48 barrios."""
    clima = df.query('es_clima')
    conteo = clima.groupby('barrio').size().rename('reclamos').reset_index()

    # merge con la lista oficial: un barrio sin reclamos aparece con 0 en vez de faltar
    maestra = pd.DataFrame({'barrio': barrios.BARRIOS})
    tabla = maestra.merge(conteo, on='barrio', how='left')
    tabla['reclamos'] = tabla['reclamos'].fillna(0).astype(int)

    # transform: cada barrio como porcentaje del total de la ciudad
    tabla['participacion_pct'] = tabla['reclamos'].transform(lambda s: s / s.sum() * 100).round(2)

    return tabla


def calcular_vulnerabilidad(tabla):
    """Percentil (0 a 1) y factor de vulnerabilidad (FACTOR_MIN a FACTOR_MAX) por barrio."""
    tabla = tabla.copy()
    cantidad = len(tabla)

    orden = tabla['reclamos'].rank(method='average')          # 1 = menos reclamos
    tabla['percentil'] = ((orden - 1) / (cantidad - 1)).round(3)

    rango = config.FACTOR_MAX - config.FACTOR_MIN
    tabla['factor_vulnerabilidad'] = (config.FACTOR_MIN + rango * tabla['percentil']).round(3)

    return tabla.sort_values('reclamos', ascending=False).reset_index(drop=True)


def serie_semanal(df):
    """Reclamos de clima por semana, con media movil y variacion contra la semana anterior."""
    clima = df.query('es_clima')

    semana = clima['fecha'].dt.to_period('W').dt.start_time
    serie = clima.groupby(semana).size()

    # semanas sin reclamos tambien cuentan (0)
    todas = pd.date_range(serie.index.min(), serie.index.max(), freq='W-MON')
    serie = serie.reindex(todas, fill_value=0)

    # Se descartan las semanas incompletas de los extremos (la del 1 de enero
    # arranca un domingo): con pocos dias distorsionan la comparacion.
    inicio = df['fecha'].min().normalize()
    fin = df['fecha'].max().normalize()
    completas = (serie.index >= inicio) & (serie.index + pd.Timedelta(days=6) <= fin)
    serie = serie[completas]

    tabla = serie.rename('reclamos').to_frame()
    tabla.index.name = 'semana'
    tabla['media_movil_4'] = tabla['reclamos'].rolling(4).mean().round(1)

    anterior = tabla['reclamos'].shift(1)
    tabla['variacion_pct'] = ((tabla['reclamos'] - anterior) / anterior * 100)
    tabla['variacion_pct'] = tabla['variacion_pct'].replace([np.inf, -np.inf], np.nan).round(1)

    return tabla


def comparar_semestres(df):
    """Comparacion temporal: reclamos de clima de enero-junio contra julio-diciembre."""
    clima = df.query('es_clima')
    mes = clima['fecha'].dt.month

    semestre_1 = clima[mes <= 6].groupby('barrio').size().rename('semestre_1')
    semestre_2 = clima[mes > 6].groupby('barrio').size().rename('semestre_2')

    # join por el indice (barrio)
    comparacion = semestre_1.to_frame().join(semestre_2, how='outer').fillna(0).astype(int)
    comparacion['diferencia'] = comparacion['semestre_2'] - comparacion['semestre_1']

    base = comparacion['semestre_1'].replace(0, np.nan)
    comparacion['variacion_pct'] = (comparacion['diferencia'] / base * 100).round(1)

    return comparacion.sort_values('diferencia', ascending=False).reset_index()


def reclamos_barrio_mes(df):
    """Tabla dinamica: barrios en las filas, meses en las columnas."""
    clima = df.query('es_clima').assign(mes=lambda d: d['fecha'].dt.month)

    tabla = clima.pivot_table(
        index='barrio', columns='mes', values='nro_solicitud',
        aggfunc='count', fill_value=0,
    )
    tabla.columns = [f'mes_{mes:02d}' for mes in tabla.columns]

    return tabla.reset_index()


def resumen_categorias(df):
    """Cuantos reclamos hay por categoria y cuantos siguen abiertos (agg con nombres)."""
    resumen = df.groupby('categoria', observed=True).agg(
        reclamos=('nro_solicitud', 'count'),
        abiertos=('estado_general', lambda s: int((s == 'Abierto').sum())),
    )

    return resumen.nlargest(10, 'reclamos').reset_index()
