# API publica de Openweather: https://openweathermap.org/api
# Es publica porque tiene documentacion abierta y clave gratis para cualquiera.

from datetime import datetime, timedelta, timezone

import requests

from monitoreo.app import config

# Conversion timezone
HUSO_CABA = timezone(timedelta(hours=config.HORAS_UTC_CABA))


def pedir_a_la_api():
    api_key = config.get_api_key()

    if api_key == '':
        raise SystemExit('Falta OPENWEATHER_API_KEY en el archivo .env')

    parametros = {
        'lat': config.LATITUD,
        'lon': config.LONGITUD,
        'appid': api_key,
        'units': 'metric',
        'lang': 'es',
    }

    try:
        respuesta = requests.get(config.URL_CLIMA, params=parametros, timeout=config.TIMEOUT)
        respuesta.raise_for_status()
    except requests.exceptions.RequestException as error:
        raise SystemExit(f'No se pudo consultar el clima: {error}')

    return respuesta.json()


# -- Transformacion de la respuesta (N04) --

def limpiar_bloques(datos):
    bloques = []

    for item in datos['list']:
        # dt viene en UTC, lo pasamos a hora de CABA
        fecha = datetime.fromtimestamp(item['dt'], HUSO_CABA)

        # El key rain no aparece cuando no llueve
        lluvia = item.get('rain', {}).get('3h', 0.0)

        bloques.append({
            'fecha': fecha,
            'temperatura': item['main']['temp'],
            # el viento viene en m/s y nuestros umbrales estan en km/h
            'viento_kmh': item['wind']['speed'] * config.MS_A_KMH,
            'lluvia_mm': lluvia,
            'descripcion': item['weather'][0]['description'],
        })

    return bloques


def resumir_por_dia(bloques):
    dias = {}

    for bloque in bloques:
        fecha = bloque['fecha'].date()

        if fecha not in dias:
            dias[fecha] = {
                'fecha': fecha,
                'lluvia_mm': 0.0,
                'viento_kmh': 0.0,
                'temp_max': bloque['temperatura'],
                'temp_min': bloque['temperatura'],
            }

        dia = dias[fecha]
        dia['lluvia_mm'] = dia['lluvia_mm'] + bloque['lluvia_mm']

        if bloque['viento_kmh'] > dia['viento_kmh']:
            dia['viento_kmh'] = bloque['viento_kmh']

        if bloque['temperatura'] > dia['temp_max']:
            dia['temp_max'] = bloque['temperatura']

        if bloque['temperatura'] < dia['temp_min']:
            dia['temp_min'] = bloque['temperatura']

    resumen = []
    for fecha in sorted(dias):
        resumen.append(dias[fecha])

    return resumen


def obtener_pronostico():
    datos = pedir_a_la_api()
    bloques = limpiar_bloques(datos)

    return resumir_por_dia(bloques)
