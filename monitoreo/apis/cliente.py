# Cliente de la API propia, con requests (N15, N16).
# Usa POST (registro), GET con la API key en un header, timeout y manejo de
# status codes y errores de conexion. Es como consultaria la API una app del vecino.

import requests

from monitoreo.app import config

URL_BASE = f'http://{config.API_HOST}:{config.API_PUERTO}'


class ErrorApi(Exception):
    pass


def pedir(metodo, ruta, **opciones):
    try:
        respuesta = requests.request(metodo, URL_BASE + ruta, timeout=config.TIMEOUT, **opciones)
    except requests.exceptions.ConnectionError:
        raise ErrorApi(f'No se pudo conectar con {URL_BASE}. ¿Está levantado el servidor?')
    except requests.exceptions.Timeout:
        raise ErrorApi('El servidor tardó demasiado en responder')

    if respuesta.status_code in (200, 201):
        return respuesta.json()

    # Cuando hay un error, FastAPI manda {"detail": "..."}
    raise ErrorApi(f'{respuesta.status_code}: {respuesta.json().get("detail")}')


def revisar_salud():
    return pedir('GET', '/salud')


def registrar_usuario(nombre, email, barrio):
    """POST con cuerpo JSON. Devuelve los datos del usuario, con su API key."""
    return pedir('POST', '/usuarios', json={'nombre': nombre, 'email': email, 'barrio': barrio})


def consultar_mi_barrio(api_key):
    """GET con la API key en el header."""
    return pedir('GET', '/mi-barrio', headers={'X-API-Key': api_key})


def consultar_barrio(api_key, barrio):
    return pedir('GET', f'/riesgo/{barrio}', headers={'X-API-Key': api_key})
