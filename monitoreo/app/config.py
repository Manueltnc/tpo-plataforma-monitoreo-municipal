# Configuración de la plataforma: urls, umbrales de las alertas, puntajes
# y demas datos ajustables.

import os

from dotenv import load_dotenv

# Lee el archivo .env y carga sus valores como variables de entorno.
# El .env esta en .gitignore, asi que la clave nunca viaja en el repo (N17).
load_dotenv()

# API de openweather
URL_CLIMA = 'https://api.openweathermap.org/data/2.5/forecast'
TIMEOUT = 10

# OpenWeather manda el viento en metros por segundo y el SMN publica en km/h
MS_A_KMH = 3.6

# Unificar la zona horario contra la api de openweather
HORAS_UTC_CABA = -3

# coordenadas de centro caba
LATITUD = -34.61
LONGITUD = -58.44

# -- Umbrales --

# Lluvia
LLUVIA_ATENCION = 20
LLUVIA_ALERTA = 40
LLUVIA_EMERGENCIA = 70

# Viento
VIENTO_ATENCION = 40
VIENTO_ALERTA = 59

# Temperatura (para segunda entrega)
TEMPERATURA_ALTA = 32.3

# Reclamos
RECLAMOS_MUCHOS = 50

# -- Fin Umbrales --

# Puntajes de alertas
PUNTOS_LLUVIA_ATENCION = 15
PUNTOS_LLUVIA_ALERTA = 30
PUNTOS_LLUVIA_EMERGENCIA = 50

PUNTOS_VIENTO_ATENCION = 10
PUNTOS_VIENTO_ALERTA = 20

PUNTOS_CRITICIDAD_ALTA = 20
PUNTOS_MUCHOS_RECLAMOS = 15

PUNTOS_TEMPERATURA_ALTA = 25

# Umbral de puntos
CORTE_ATENCION = 20
CORTE_ALERTA = 45
CORTE_EMERGENCIA = 70

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

# Destinatarios correos
CORREOS = [
    'mtanco@uade.edu.ar',
]

def get_api_key():
    return os.environ.get('OPENWEATHER_API_KEY', '')
