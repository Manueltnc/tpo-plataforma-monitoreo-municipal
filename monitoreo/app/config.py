# Configuracion de la plataforma: urls, umbrales de las alertas, rutas
# y demas datos ajustables.

import os
from pathlib import Path

from dotenv import load_dotenv

# Lee el archivo .env y carga sus valores como variables de entorno.
# El .env esta en .gitignore, asi que la clave nunca viaja en el repo (N17).
load_dotenv()

# config.py esta en monitoreo/app/, la raiz del proyecto es dos carpetas arriba
BASE_DIR = Path(__file__).resolve().parents[2]

# -- Rutas de datos --
DIR_RAW = BASE_DIR / 'data' / 'raw'                # datos crudos (no van al repo)
DIR_FIXTURES = BASE_DIR / 'data' / 'fixtures'      # muestras chicas (si van al repo)
DIR_PROCESADOS = BASE_DIR / 'data' / 'processed'   # resultados del ETL
RUTA_FIXTURE_SUACI = DIR_FIXTURES / 'suaci_2023_muestra.zip'
RUTA_DB_USUARIOS = BASE_DIR / 'data' / 'usuarios.db'

# API de openweather
URL_CLIMA = 'https://api.openweathermap.org/data/2.5/forecast'
TIMEOUT = 10

# Si no hay API key se usa un pronostico guardado (fixture), avisando por pantalla.
# Poner en False para que el programa se detenga cuando falte la clave.
USAR_FIXTURE_SI_FALTA_CLAVE = True
PRONOSTICO_FIXTURE = os.environ.get('PRONOSTICO_FIXTURE', 'forecast_caba.json')

# OpenWeather manda el viento en metros por segundo y el SMN publica en km/h
MS_A_KMH = 3.6

# Unificar la zona horario contra la api de openweather
HORAS_UTC_CABA = -3

# coordenadas de centro caba
LATITUD = -34.61
LONGITUD = -58.44

# -- Indicador de riesgo (N02, N03) --
# Umbrales de peligro meteorologico, en mm por dia y km/h.
# APROXIMADOS: tomados de los rangos de los avisos del SMN (amarillo 20 a 70 mm,
# naranja 60 a 100 mm). Falta contrastarlos con la tabla oficial de CABA
# (Nota Tecnica SMN 2021-109 / "Umbrales para los alertas al publico").
# El SMN mide el viento en rafagas; OpenWeather da velocidad media, por eso los
# umbrales de viento son mas bajos.

# Lluvia
LLUVIA_ATENCION = 20
LLUVIA_ALERTA = 40
LLUVIA_EMERGENCIA = 70

# Viento
VIENTO_ATENCION = 40
VIENTO_ALERTA = 59
VIENTO_EMERGENCIA = 80

# Si llueve y ademas hay viento, el riesgo de arboles caidos sube
PUNTOS_COMPUESTO = 10

# Factor de vulnerabilidad del barrio: va de FACTOR_MIN (barrio con menos
# reclamos historicos de sumideros y arbolado) a FACTOR_MAX (el que mas tiene).
FACTOR_MIN = 0.75
FACTOR_MAX = 1.25

# Puntos de corte del indice (0 a 100)
CORTE_ATENCION = 20
CORTE_ALERTA = 45
CORTE_EMERGENCIA = 70

# Que reclamos del SUACI se consideran "relacionados con el clima".
# Se buscan (como expresion regular) en el nombre de la prestacion ya normalizado
# (minusculas y sin tildes).
#   - sumideros / pluviales / calle anegada: el drenaje falla cuando llueve mucho
#   - poda y extraccion de arbol: los arboles ceden con viento y tormenta
# No entran "retiro de restos de poda" ni "plantacion", que no dependen del clima.
PATRONES_RECLAMOS_CLIMA = [
    'sumidero',
    'alcantarilla',
    'pluvial',
    'anegada',
    'inundada',
    '^poda de arbol',
    '^extraccion de arbol',
]

# La consigna pide que el scraping se pueda apagar por configuracion.
SCRAPING_ACTIVO = True

# Sitio oficial que se scrapea. Viene armado desde el servidor, asi que
# BeautifulSoup lo puede leer. El de smn.gob.ar/alertas devuelve 403 porque
# exige JavaScript.
URLS_OFICIALES = [
    'https://www.argentina.gob.ar/noticias',
]

# Palabras que hacen que un aviso sea importante para el sistema.
PALABRAS_CLAVE = [
    'alerta',
    'anegamiento',
    'inundacion',
    'tormenta',
    'temporal',
    'ola de calor',
    'evacuacion',
    'emergencia',
    'corte',
]

# Destinatarios por defecto si no hay EMAIL_RECEIVER en el .env (cambiar por los del grupo)
CORREOS = [
    'destinatario@ejemplo.com',
]

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


# -- Correo (N24, N25) --
# Las claves nunca se escriben en el codigo: se leen del .env.
# Los nombres de las variables son los mismos de los ejemplos de la clase 12.

# Se manda correo de alerta desde este nivel (alerta o emergencia)
NIVEL_MINIMO_ALERTA = 'alerta'

# Si esta en False, main.py no manda ni guarda ningun correo
ENVIAR_CORREOS = True

# Cuando falta la clave del correo (o el envio falla) el mensaje se guarda aca como .eml
DIR_CORREOS = DIR_PROCESADOS / 'correos'


def get_smtp_server():
    return _valor_real('SMTP_SERVER', 'smtp.gmail.com')


def get_smtp_port():
    return int(_valor_real('SMTP_PORT', '465'))


def get_email_user():
    return _valor_real('EMAIL_USER')


def get_email_password():
    return _valor_real('EMAIL_PASSWORD').replace(' ', '')   # Gmail la muestra con espacios


def get_email_receiver():
    return _valor_real('EMAIL_RECEIVER')    # varios destinatarios separados por coma
