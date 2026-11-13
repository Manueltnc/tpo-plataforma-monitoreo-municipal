# Configuracion de la plataforma: urls, umbrales de las alertas, rutas
# y demas datos ajustables. Si hay que cambiar un criterio, se cambia aca.

import os
from pathlib import Path

from dotenv import load_dotenv

# Lee el archivo .env y carga sus valores como variables de entorno.
# El .env esta en .gitignore, asi que las claves nunca viajan en el repo (N17).
load_dotenv()

# config.py esta en monitoreo/app/, la raiz del proyecto es dos carpetas arriba
BASE_DIR = Path(__file__).resolve().parents[2]

# -- Rutas de datos --
DIR_RAW = BASE_DIR / 'data' / 'raw'                # datos crudos (no van al repo)
DIR_FIXTURES = BASE_DIR / 'data' / 'fixtures'      # muestras chicas (si van al repo)
DIR_PROCESADOS = BASE_DIR / 'data' / 'processed'   # resultados del ETL
DIR_REPORTES = DIR_PROCESADOS / 'reportes'         # un reporte por dia
DIR_GRAFICOS = DIR_PROCESADOS / 'graficos'
DIR_CORREOS = DIR_PROCESADOS / 'correos'           # correos que no se pudieron enviar
RUTA_FIXTURE_SUACI = DIR_FIXTURES / 'suaci_2023_muestra.zip'
RUTA_USUARIOS = BASE_DIR / 'data' / 'usuarios.csv'  # vecinos registrados en la API

# -- API de OpenWeather (publica) --
URL_CLIMA = 'https://api.openweathermap.org/data/2.5/forecast'
TIMEOUT = 10

# Si no hay API key se usa un pronostico guardado (fixture), avisando por pantalla.
# Sirve para probar el programa sin cuenta en OpenWeather.
USAR_FIXTURE_SI_FALTA_CLAVE = True
PRONOSTICO_FIXTURE = os.environ.get('PRONOSTICO_FIXTURE', 'forecast_caba.json')

# OpenWeather manda el viento en metros por segundo y el SMN publica en km/h
MS_A_KMH = 3.6

# Diferencia horaria de CABA con UTC (OpenWeather manda las horas en UTC)
HORAS_UTC_CABA = -3

# Coordenadas del centro de CABA. Hay un solo pronostico para toda la ciudad.
LATITUD = -34.61
LONGITUD = -58.44

# -- Criterios de riesgo (N02, N03) --
# Paso 1: el clima define el nivel. Lluvia en mm por dia, viento en km/h.
# Valores tomados de los rangos de los avisos del SMN (ver README).
LLUVIA_ATENCION = 20
LLUVIA_ALERTA = 40
LLUVIA_EMERGENCIA = 70

VIENTO_ATENCION = 40
VIENTO_ALERTA = 59
VIENTO_EMERGENCIA = 80

# Paso 2: el barrio puede subir un nivel.
# Son "barrios con mas reclamos" los 16 primeros (un tercio de los 48) en reclamos
# del SUACI 2023 por sumideros, calles anegadas y arboles.
CANTIDAD_BARRIOS_CON_MAS_RECLAMOS = 16

# Que reclamos del SUACI se consideran "relacionados con el clima".
# Se buscan (como expresion regular) en el nombre de la prestacion ya normalizado
# (minusculas y sin tildes).
#   - sumideros / pluviales / calle anegada: el drenaje falla cuando llueve mucho
#   - poda y extraccion de arbol: los arboles ceden con viento y tormenta
PATRONES_RECLAMOS_CLIMA = [
    'sumidero',
    'alcantarilla',
    'pluvial',
    'anegada',
    'inundada',
    '^poda de arbol',
    '^extraccion de arbol',
]

# -- Scraping (N10) --
# La consigna pide que se pueda apagar por configuracion.
SCRAPING_ACTIVO = True

# Sitio oficial que se lee. Viene armado desde el servidor, asi que BeautifulSoup
# lo puede leer. El de smn.gob.ar/alertas devuelve 403 porque exige JavaScript.
URLS_OFICIALES = [
    'https://www.argentina.gob.ar/noticias',
]
URL_ROBOTS = 'https://www.argentina.gob.ar/robots.txt'

# Palabras que hacen que una noticia tenga que ver con el clima.
# Se comparan contra el titulo normalizado (minusculas y sin tildes).
PALABRAS_CLAVE = [
    'alerta',
    'tormenta',
    'lluvia',
    'temporal',
    'inundacion',
    'anegamiento',
    'viento',
    'granizo',
    'meteorolog',
    'ola de calor',
]

# -- Correo (N24, N25) --
# Se le avisa a un vecino cuando su barrio llega a este nivel o a uno mas alto
NIVEL_MINIMO_AVISO = 'atencion'

# Si esta en False, main.py no manda ni guarda ningun correo
ENVIAR_CORREOS = True

# Direcciones que tienen un dominio de ejemplo nunca se envian (quedan como borrador)
DOMINIO_DE_EJEMPLO = '@ejemplo.com'

# -- API propia del proyecto (N15, N16, N17) --
API_HOST = '127.0.0.1'
API_PUERTO = 8000
LIMITE_PEDIDOS_POR_MINUTO = 30     # rate limiting por API key
SEGUNDOS_CACHE_RIESGO = 600        # no se vuelve a pedir el clima antes de 10 minutos


def _valor_real(nombre, por_defecto=''):
    """Lee una variable de entorno. Si falta o es un relleno de .env.example
    (empieza con "tu_"), devuelve el valor por defecto."""
    valor = os.environ.get(nombre, '').strip()

    if valor == '' or valor.startswith('tu_'):
        return por_defecto

    return valor


def get_api_key():
    return _valor_real('OPENWEATHER_API_KEY')


# Las claves del correo nunca se escriben en el codigo: se leen del .env.

def get_smtp_server():
    return _valor_real('SMTP_SERVER', 'smtp.gmail.com')


def get_smtp_port():
    return int(_valor_real('SMTP_PORT', '465'))


def get_email_user():
    return _valor_real('EMAIL_USER')


def get_email_password():
    return _valor_real('EMAIL_PASSWORD').replace(' ', '')   # Gmail la muestra con espacios


def get_correos_guardia():
    """Lista de correos de la guardia municipal (N05). Reciben el reporte diario.
    En el .env van separados por coma: EMAIL_GUARDIA=uno@x.com,otro@x.com"""
    texto = _valor_real('EMAIL_GUARDIA')
    correos = []

    for correo in texto.split(','):
        if correo.strip() != '':
            correos.append(correo.strip())

    return correos
