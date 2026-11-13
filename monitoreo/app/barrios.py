# N04 validacion y limpieza de datos, N05 y N06 listas y diccionarios de barrios,
# N07 normalizacion de nombres y extraccion de dominios.

import csv

from monitoreo.app import config

# 48 barrios de CABA
BARRIOS = [
    'Agronomia', 'Almagro', 'Balvanera', 'Barracas', 'Belgrano', 'Boedo',
    'Caballito', 'Chacarita', 'Coghlan', 'Colegiales', 'Constitucion',
    'Flores', 'Floresta', 'La Boca', 'La Paternal', 'Liniers', 'Mataderos',
    'Monte Castro', 'Monserrat', 'Nueva Pompeya', 'Nunez', 'Palermo',
    'Parque Avellaneda', 'Parque Chacabuco', 'Parque Chas',
    'Parque Patricios', 'Puerto Madero', 'Recoleta', 'Retiro', 'Saavedra',
    'San Cristobal', 'San Nicolas', 'San Telmo', 'Velez Sarsfield',
    'Versalles', 'Villa Crespo', 'Villa del Parque', 'Villa Devoto',
    'Villa General Mitre', 'Villa Lugano', 'Villa Luro', 'Villa Ortuzar',
    'Villa Pueyrredon', 'Villa Real', 'Villa Riachuelo', 'Villa Santa Rita',
    'Villa Soldati', 'Villa Urquiza',
]

# El SUACI escribe algunos barrios distinto que nuestra lista oficial.
# Las claves ya estan normalizadas (minusculas, sin tildes).
ALIAS_BARRIOS = {
    'boca': 'La Boca',
    'paternal': 'La Paternal',
    'villa gral. mitre': 'Villa General Mitre',
}

# Reclamos de cada barrio. Los calcula el ETL a partir de los reclamos reales del
# SUACI 2023 y los guarda en data/processed/reclamos_por_barrio.csv
RUTA_RECLAMOS = config.DIR_PROCESADOS / 'reclamos_por_barrio.csv'
SIN_DATOS = {'reclamos': 0, 'puesto': 0, 'con_mas_reclamos': False}
_reclamos = {}


# normalizamos a minusculas, sin acentos y sin espacios de mas
def normalizar(texto):
    texto = texto.strip().lower()
    texto = texto.replace('á', 'a')
    texto = texto.replace('é', 'e')
    texto = texto.replace('í', 'i')
    texto = texto.replace('ó', 'o')
    texto = texto.replace('ú', 'u')
    texto = texto.replace('ñ', 'n')

    return ' '.join(texto.split())


def validar_barrio(nombre):
    """Devuelve el nombre oficial del barrio, o None si no existe."""
    buscado = normalizar(nombre)

    if buscado in ALIAS_BARRIOS:
        return ALIAS_BARRIOS[buscado]

    for barrio in BARRIOS:
        if normalizar(barrio) == buscado:
            return barrio

    return None


def extraer_dominio(url):
    """https://www.argentina.gob.ar/noticias -> argentina.gob.ar"""
    dominio = url.replace('https://', '').replace('http://', '')

    if '/' in dominio:
        dominio = dominio.split('/')[0]

    if dominio.startswith('www.'):
        dominio = dominio.replace('www.', '')

    return dominio


def cargar_reclamos(ruta=RUTA_RECLAMOS):
    """Lee el CSV que genero el ETL y arma un diccionario {barrio: datos}."""
    _reclamos.clear()

    if not ruta.exists():
        return _reclamos

    with open(ruta, encoding='utf-8', newline='') as archivo:
        for fila in csv.DictReader(archivo):
            _reclamos[fila['barrio']] = {
                'reclamos': int(fila['reclamos']),
                'puesto': int(fila['puesto']),
                'con_mas_reclamos': fila['con_mas_reclamos'] == 'True',
            }

    return _reclamos


def hay_datos_de_reclamos():
    if not _reclamos:
        cargar_reclamos()

    return len(_reclamos) > 0


def reclamos_de_barrio(barrio):
    """Si no hay datos del ETL, el barrio no sube de nivel."""
    if not _reclamos:
        cargar_reclamos()

    return _reclamos.get(barrio, SIN_DATOS)
