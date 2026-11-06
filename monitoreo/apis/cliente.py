# Cliente de la API propia, con requests (N15, N16).
# Usa POST (registro), GET con parametros, headers de autenticacion, timeout y
# manejo de status codes y errores de conexion.

import requests

from monitoreo.app import config

URL_BASE = f'http://{config.API_HOST}:{config.API_PUERTO}'


class ErrorApi(Exception):
    def __init__(self, mensaje, codigo=None):
        super().__init__(mensaje)
        self.codigo = codigo


def _pedir(metodo, ruta, **opciones):
    try:
        respuesta = requests.request(metodo, URL_BASE + ruta, timeout=config.TIMEOUT, **opciones)
    except requests.exceptions.ConnectionError:
        raise ErrorApi(f'No se pudo conectar con {URL_BASE}. Esta levantado el servidor?')
    except requests.exceptions.Timeout:
        raise ErrorApi('El servidor tardo demasiado en responder')

    if respuesta.status_code in (200, 201):
        return respuesta.json()

    # En error FastAPI manda {"detail": "..."}
    try:
        detalle = respuesta.json().get('detail', respuesta.text)
    except ValueError:
        detalle = respuesta.text

    raise ErrorApi(f'{respuesta.status_code}: {detalle}', respuesta.status_code)


def revisar_salud():
    return _pedir('GET', '/salud')


def registrar_usuario(nombre, email):
    """POST con cuerpo JSON. Devuelve los datos del usuario, con su API key."""
    return _pedir('POST', '/usuarios', json={'nombre': nombre, 'email': email})


def consultar_riesgo(api_key, nivel_minimo=None):
    """GET con la API key en el header y, si se pide, un parametro de filtro."""
    encabezados = {'X-API-Key': api_key, 'Accept': 'application/json'}
    parametros = {}

    if nivel_minimo:
        parametros['nivel_minimo'] = nivel_minimo

    return _pedir('GET', '/riesgo', headers=encabezados, params=parametros)


def consultar_barrio(api_key, barrio):
    encabezados = {'X-API-Key': api_key, 'Accept': 'application/json'}
    return _pedir('GET', f'/riesgo/{barrio}', headers=encabezados)
