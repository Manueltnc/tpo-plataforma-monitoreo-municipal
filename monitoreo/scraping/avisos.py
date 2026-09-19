# Scraping del sitio oficial de noticias del gobierno
#   URL: https://www.argentina.gob.ar/noticias
#   Dominio: argentina.gob.ar
#   IP: 104.26.4.183
#   Navegador: Chrome en Windows 11
#
# Etiquetas que tiene la pagina : html, head, title, body, a, div,
# time, h3, span, img

import requests
from bs4 import BeautifulSoup

from monitoreo.app import barrios, config


def bajar_html(url):
    respuesta = requests.get(url, timeout=config.TIMEOUT)
    respuesta.encoding = 'utf-8'

    return respuesta.text


def limpiar_avisos(html):
    sopa = BeautifulSoup(html, 'html.parser')

    avisos = []

    # cada noticia es un <a class="panel panel-default">
    for caja in sopa.find_all('a', class_='panel'):
        fecha = caja.find('time')

        avisos.append({
            'titulo': caja.find('h3').get_text(strip=True),
            'enlace': caja.get('href'),
            'fecha': fecha.get_text(strip=True),
            'fecha_iso': fecha.get('datetime'),
            'clases': caja.get('class'),
        })

    return avisos


# busca si el titulo tiene alguna de nuestras palabras clave
def es_importante(aviso):
    titulo = barrios.normalizar(aviso['titulo'])

    for palabra in config.PALABRAS_CLAVE:
        if palabra in titulo:
            return True

    return False


def obtener_avisos(html):
    if not config.SCRAPING_ACTIVO:
        print('  Scraping desactivado por configuracion.')
        return [], []

    todos = limpiar_avisos(html)

    importantes = []
    for aviso in todos:
        if es_importante(aviso):
            importantes.append(aviso)

    return todos, importantes


# -- Las seis busquedas que pide N12 --

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
