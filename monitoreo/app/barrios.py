# N04 validacion y limpieza de datos, N05 y N06 listas y diccionarios de barrios,
# N07 normalizacion de nombres.

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

# Vulnerabilidad de cada barrio. La calcula el ETL a partir de los reclamos
# reales del SUACI 2023 y la guarda en data/processed/vulnerabilidad_barrios.csv
RUTA_VULNERABILIDAD = config.DIR_PROCESADOS / 'vulnerabilidad_barrios.csv'
VULNERABILIDAD_NEUTRA = {'reclamos': 0, 'percentil': 0.5, 'factor': 1.0}
_vulnerabilidad = {}


# normalizamos a minisculas, sin acentos y sin whitespace
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
    buscado = normalizar(nombre)

    if buscado in ALIAS_BARRIOS:
        return ALIAS_BARRIOS[buscado]

    for barrio in BARRIOS:
        if normalizar(barrio) == buscado:
            return barrio

    return None


def extraer_dominio(url):
    dominio = url.replace('https://', '').replace('http://', '')

    if '/' in dominio:
        dominio = dominio.split('/')[0]

    if dominio.startswith('www.'):
        dominio = dominio.replace('www.', '')

    return dominio


def armar_mensaje(barrio, evento, nivel, puntos, motivos):
    texto = f'[{nivel.upper()}] {barrio} - {evento}\n'
    texto = texto + f'Puntaje de riesgo: {puntos}\n'
    texto = texto + 'Motivos:\n'

    for motivo in motivos:
        texto = texto + f'  - {motivo}\n'

    return texto

def cargar_vulnerabilidad(ruta=RUTA_VULNERABILIDAD):
    """Lee el CSV que genero el ETL y arma un diccionario {barrio: datos}."""
    _vulnerabilidad.clear()

    if not ruta.exists():
        return _vulnerabilidad

    with open(ruta, encoding='utf-8', newline='') as archivo:
        for fila in csv.DictReader(archivo):
            _vulnerabilidad[fila['barrio']] = {
                'reclamos': int(fila['reclamos']),
                'percentil': float(fila['percentil']),
                'factor': float(fila['factor_vulnerabilidad']),
            }

    return _vulnerabilidad


def hay_datos_vulnerabilidad():
    if not _vulnerabilidad:
        cargar_vulnerabilidad()

    return len(_vulnerabilidad) > 0


def vulnerabilidad_de_barrio(barrio):
    """Si no hay datos del ETL se usa un factor neutro (1.0): ni suma ni resta."""
    if not _vulnerabilidad:
        cargar_vulnerabilidad()

    return _vulnerabilidad.get(barrio, VULNERABILIDAD_NEUTRA)
