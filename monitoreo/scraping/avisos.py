# Scraping de noticias oficiales (N08 a N12)
#   URL: https://www.argentina.gob.ar/noticias
#   Dominio: argentina.gob.ar
#   IP: 104.26.4.183
#   Navegador: Chrome en Windows 11
#
# Etiquetas que tiene la pagina: html, head, title, body, a, div, time, h3, span, img
#
# Que hacemos: leemos los titulos de las ultimas noticias del gobierno y nos quedamos
# con las que hablan del clima (alerta, tormenta, lluvia, etc.). Esas se le muestran
# al vecino como "avisos oficiales", con su link. No cambian el nivel de riesgo.

from urllib import robotparser

import requests
from bs4 import BeautifulSoup

from monitoreo.app import barrios, config


def permitido_por_robots(url):
    """Lee el robots.txt del sitio y responde si se puede leer esa url (N10)."""
    try:
        # se baja con requests: el sitio rechaza el lector que trae Python (da 403)
        respuesta = requests.get(config.URL_ROBOTS, timeout=config.TIMEOUT)
        respuesta.raise_for_status()
    except requests.RequestException:
        # si no se puede leer el robots.txt, por las dudas no scrapeamos
        return False

    lector = robotparser.RobotFileParser()
    lector.parse(respuesta.text.splitlines())

    return lector.can_fetch('*', url)


def bajar_html(url):
    respuesta = requests.get(url, timeout=config.TIMEOUT)
    respuesta.raise_for_status()
    respuesta.encoding = 'utf-8'

    return respuesta.text


def limpiar_avisos(html, url_sitio):
    """Arma una lista de diccionarios con cada noticia de la pagina (N11)."""
    sopa = BeautifulSoup(html, 'html.parser')
    dominio = barrios.extraer_dominio(url_sitio)

    avisos = []

    # cada noticia es un <a class="panel panel-default">
    for caja in sopa.find_all('a', class_='panel'):
        fecha = caja.find('time')

        avisos.append({
            'titulo': caja.find('h3').get_text(strip=True),
            'fecha': fecha.get_text(strip=True),
            'fecha_iso': fecha.get('datetime'),
            # el href viene sin dominio (/noticias/...), le agregamos el sitio
            'enlace': 'https://www.' + dominio + caja.get('href'),
            'fuente': dominio,
        })

    return avisos


def es_del_clima(aviso):
    """True si el titulo tiene alguna de las palabras clave del clima."""
    titulo = barrios.normalizar(aviso['titulo'])

    for palabra in config.PALABRAS_CLAVE:
        if palabra in titulo:
            return True

    return False


def buscar_avisos():
    """Hace todo el scraping y devuelve un resumen:
    {'usado': True/False, 'detalle': texto, 'leidas': cantidad, 'avisos': [...]}"""
    url = config.URLS_OFICIALES[0]

    if not config.SCRAPING_ACTIVO:
        return {'usado': False, 'detalle': 'El scraping está desactivado en config.py.', 'leidas': 0, 'avisos': []}

    if not permitido_por_robots(url):
        return {'usado': False, 'detalle': 'El robots.txt del sitio no permite leer la página.', 'leidas': 0, 'avisos': []}

    try:
        html = bajar_html(url)
    except requests.RequestException as error:
        return {'usado': False, 'detalle': f'No se pudo leer el sitio ({error}).', 'leidas': 0, 'avisos': []}

    todas = limpiar_avisos(html, url)

    del_clima = []
    for aviso in todas:
        if es_del_clima(aviso):
            del_clima.append(aviso)

    return {
        'usado': True,
        'detalle': f'Se leyeron {len(todas)} noticias de {barrios.extraer_dominio(url)}.',
        'leidas': len(todas),
        'avisos': del_clima,
    }


# -- Las seis busquedas que pide N12 (se prueban en tests/) --

def mostrar_busquedas(html):
    sopa = BeautifulSoup(html, 'html.parser')

    print(f'  1. etiqueta "a": {len(sopa.find_all("a"))} enlaces')
    print(f'  2. clase "panel": {len(sopa.find_all("a", class_="panel"))} noticias')
    print(f'  3. id "main-content": <{sopa.find(id="main-content").name}>')
    print(f'  4. atributo datetime: {len(sopa.find_all("time", attrs={"datetime": True}))} fechas')
    print(f'  5. texto exacto: {len(sopa.find_all(string="Pasar al contenido principal"))} coincidencia')

    noticias = sopa.find_all(
        lambda tag: tag.name == 'a' and tag.get('href', '').startswith('/noticias/')
    )
    print(f'  6. lambda sobre href: {len(noticias)} noticias')
