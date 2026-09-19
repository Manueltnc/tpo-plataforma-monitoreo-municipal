# Intentamos cubrir N04 con validacion y limpieza de datos, N05 y N06 con las listas de barrios y sus criterios y valores fijos de reclamos, N07 normalizacion de nombres. 

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

# Criticidad barrios por cercania a factores como rios y cuencas (sacado de en-linea)
CRITICIDAD = {
    'Agronomia': 5, 'Almagro': 3, 'Balvanera': 3, 'Barracas': 4,
    'Belgrano': 4, 'Boedo': 3, 'Caballito': 5, 'Chacarita': 5,
    'Coghlan': 4, 'Colegiales': 4, 'Constitucion': 3, 'Flores': 4,
    'Floresta': 5, 'La Boca': 4, 'La Paternal': 5, 'Liniers': 4,
    'Mataderos': 4, 'Monte Castro': 5, 'Monserrat': 2, 'Nueva Pompeya': 4,
    'Nunez': 4, 'Palermo': 5, 'Parque Avellaneda': 4,
    'Parque Chacabuco': 3, 'Parque Chas': 5, 'Parque Patricios': 4,
    'Puerto Madero': 2, 'Recoleta': 2, 'Retiro': 2, 'Saavedra': 4,
    'San Cristobal': 3, 'San Nicolas': 2, 'San Telmo': 2,
    'Velez Sarsfield': 5, 'Versalles': 5, 'Villa Crespo': 5,
    'Villa del Parque': 5, 'Villa Devoto': 5, 'Villa General Mitre': 5,
    'Villa Lugano': 4, 'Villa Luro': 5, 'Villa Ortuzar': 5,
    'Villa Pueyrredon': 4, 'Villa Real': 5, 'Villa Riachuelo': 4,
    'Villa Santa Rita': 5, 'Villa Soldati': 4, 'Villa Urquiza': 4,
}

# Cantidad de reclamos estaticos para primera entrega, datos de 2023
RECLAMOS = {
    'Villa Crespo': 87, 'Palermo': 64, 'Chacarita': 55, 'Caballito': 71,
    'Flores': 48, 'Villa Lugano': 62, 'Villa Soldati': 58,
    'La Boca': 44, 'Barracas': 39, 'Belgrano': 22, 'Recoleta': 8,
}


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

def criticidad_de_barrio(barrio):
    return CRITICIDAD[barrio]


def reclamos_de_barrio(barrio):
    return RECLAMOS.get(barrio, 0)

