# Pruebas simples, sin librerias extra y sin internet.
# Correr desde la carpeta del proyecto:  python -m tests.test_plataforma

import json
import os
import smtplib
import tempfile
from datetime import date
from pathlib import Path

from monitoreo.apis import clima, usuarios
from monitoreo.app import barrios, config, reglas, servicio
from monitoreo.email import alertas
from monitoreo.etl import extraer, transformar
from monitoreo.scraping import avisos


# -- Criterios de riesgo (N02, N03) --

def test_nivel_por_umbrales():
    assert reglas.nivel_por_umbrales(0, 20, 40, 70) == 'normal'
    assert reglas.nivel_por_umbrales(19.9, 20, 40, 70) == 'normal'
    assert reglas.nivel_por_umbrales(20, 20, 40, 70) == 'atencion'
    assert reglas.nivel_por_umbrales(40, 20, 40, 70) == 'alerta'
    assert reglas.nivel_por_umbrales(100, 20, 40, 70) == 'emergencia'


def test_nivel_del_clima_toma_el_peor():
    assert reglas.nivel_del_clima({'lluvia_mm': 0, 'viento_kmh': 10})['nivel'] == 'normal'
    assert reglas.nivel_del_clima({'lluvia_mm': 45, 'viento_kmh': 10})['nivel'] == 'alerta'
    assert reglas.nivel_del_clima({'lluvia_mm': 25, 'viento_kmh': 85})['nivel'] == 'emergencia'

    ambos = reglas.nivel_del_clima({'lluvia_mm': 25, 'viento_kmh': 45})
    assert ambos['causa'] == 'lluvia y viento' and len(ambos['motivos']) == 2


def test_el_barrio_sube_un_nivel():
    barrios._reclamos.clear()
    barrios._reclamos.update({
        'Palermo': {'reclamos': 2419, 'puesto': 1, 'con_mas_reclamos': True},
        'Retiro': {'reclamos': 158, 'puesto': 46, 'con_mas_reclamos': False},
    })

    lluvia = {'lluvia_mm': 25, 'viento_kmh': 10}                  # atencion por el clima
    assert reglas.evaluar_barrio('Palermo', lluvia)['nivel'] == 'alerta'     # sube uno
    assert reglas.evaluar_barrio('Retiro', lluvia)['nivel'] == 'atencion'    # se queda

    calma = {'lluvia_mm': 0, 'viento_kmh': 10}
    assert reglas.evaluar_barrio('Palermo', calma)['nivel'] == 'normal'      # sin clima no sube

    temporal = {'lluvia_mm': 90, 'viento_kmh': 10}
    assert reglas.evaluar_barrio('Palermo', temporal)['nivel'] == 'emergencia'   # no hay mas arriba

    barrios._reclamos.clear()


def test_riesgo_de_barrio_elige_el_peor_dia():
    dias = [
        {'fecha': date(2026, 9, 12), 'lluvia_mm': 0, 'viento_kmh': 10, 'temp_min': 10, 'temp_max': 15},
        {'fecha': date(2026, 9, 13), 'lluvia_mm': 45, 'viento_kmh': 10, 'temp_min': 8, 'temp_max': 12},
    ]
    fila = servicio.riesgo_de_barrio('Retiro', dias)

    assert fila['nivel'] == 'alerta' and fila['fecha'] == date(2026, 9, 13)
    assert fila['resumen'] == 'Retiro: alerta por lluvia el domingo 13/09'
    assert len(fila['proximos_dias']) == 2


# -- Barrios y textos (N04, N07) --

def test_validar_barrio():
    assert barrios.validar_barrio('Boca') == 'La Boca'
    assert barrios.validar_barrio('  PALERMO ') == 'Palermo'
    assert barrios.validar_barrio('Agronomía') == 'Agronomia'
    assert barrios.validar_barrio('Narnia') is None


def test_extraer_dominio():
    assert barrios.extraer_dominio('https://www.argentina.gob.ar/noticias') == 'argentina.gob.ar'


# -- Scraping (N10 a N12), con la pagina guardada en data/fixtures --

def test_scraping_con_la_pagina_guardada():
    html = (config.DIR_FIXTURES / 'noticias_argentina.html').read_text(encoding='utf-8')
    noticias = avisos.limpiar_avisos(html, 'https://www.argentina.gob.ar/noticias')

    assert len(noticias) > 0
    assert noticias[0]['enlace'].startswith('https://www.argentina.gob.ar/noticias/')
    assert noticias[0]['fuente'] == 'argentina.gob.ar'

    assert avisos.es_del_clima({'titulo': 'Alerta amarilla por tormentas en el AMBA'})
    assert not avisos.es_del_clima({'titulo': 'Nueva ruta para el turismo en Salta'})

    avisos.mostrar_busquedas(html)      # las seis busquedas con find_all (N12)


# -- API de clima (N14, N16) --

def test_respuesta_del_clima():
    with open(config.DIR_FIXTURES / 'forecast_caba.json', encoding='utf-8') as archivo:
        datos = json.load(archivo)

    clima.validar_respuesta(datos)
    dias = clima.resumir_por_dia(clima.limpiar_bloques(datos))
    assert len(dias) >= 5 and dias[0]['lluvia_mm'] >= 0

    try:
        clima.validar_respuesta({'list': []})
        assert False
    except ValueError:
        pass


def test_valores_de_relleno_del_env():
    anterior = os.environ.get('OPENWEATHER_API_KEY')
    os.environ['OPENWEATHER_API_KEY'] = 'tu_clave_aca'
    try:
        assert config.get_api_key() == ''          # el relleno no cuenta como clave
        os.environ['OPENWEATHER_API_KEY'] = 'abc123'
        assert config.get_api_key() == 'abc123'
    finally:
        os.environ.pop('OPENWEATHER_API_KEY', None)
        if anterior is not None:
            os.environ['OPENWEATHER_API_KEY'] = anterior


# -- ETL con la muestra del SUACI (N19 a N22) --

def test_etl_con_la_muestra():
    crudo = extraer.leer_suaci(config.RUTA_FIXTURE_SUACI)       # lee el ZIP
    limpio, info = transformar.limpiar_suaci(crudo)
    assert info['filas_limpias'] <= info['filas_originales']
    assert info['barrio_desconocido'] == 0

    marcado = transformar.marcar_reclamos_clima(limpio)
    tabla = transformar.ordenar_por_reclamos(transformar.contar_por_barrio(marcado))

    assert len(tabla) == 48
    assert list(tabla['puesto']) == list(range(1, 49))
    assert tabla['con_mas_reclamos'].sum() == config.CANTIDAD_BARRIOS_CON_MAS_RECLAMOS
    assert tabla['reclamos'].sum() == int(marcado['es_clima'].sum())

    semanal = transformar.serie_semanal(marcado)
    assert (semanal['reclamos'] >= 0).all()
    assert len(transformar.comparar_semestres(marcado)) > 0


# -- Usuarios en CSV con pandas y API key (N17) --

def test_usuarios_en_csv():
    ruta = Path(tempfile.mkdtemp()) / 'usuarios.csv'

    clave = usuarios.registrar_usuario('Ana', 'Ana@Ejemplo.com', 'palermo', ruta)
    usuario = usuarios.buscar_por_clave(clave, ruta)
    assert usuario['email'] == 'ana@ejemplo.com' and usuario['barrio'] == 'Palermo'
    assert usuarios.buscar_por_clave('otra-clave', ruta) is None

    try:
        usuarios.registrar_usuario('Ana', 'ana@ejemplo.com', 'Palermo', ruta)
        assert False, 'tendria que fallar por email repetido'
    except usuarios.UsuarioExistente:
        pass

    for email, barrio in (('sin-arroba', 'Palermo'), ('a b@c.com', 'Palermo'), ('juan@ejemplo.com', 'Narnia')):
        try:
            usuarios.registrar_usuario('Juan', email, barrio, ruta)
            assert False, f'{email} / {barrio} no es valido'
        except ValueError:
            pass

    assert len(usuarios.lista_de_usuarios(ruta)) == 1


def test_limitador():
    limitador = usuarios.LimitadorPedidos(maximo=3, ventana=60)

    assert limitador.permitir('k', ahora=0)
    assert limitador.permitir('k', ahora=1)
    assert limitador.permitir('k', ahora=2)
    assert not limitador.permitir('k', ahora=3)       # cuarto pedido dentro del minuto
    assert limitador.permitir('k', ahora=61)          # ya paso la ventana


# -- Correo (N24) --

DIAS = [
    {'fecha': date(2026, 9, 13), 'lluvia_mm': 45, 'viento_kmh': 20, 'temp_min': 8, 'temp_max': 12},
]
SCRAPING = {'usado': True, 'detalle': 'prueba', 'leidas': 1, 'avisos': [
    {'titulo': 'Alerta por tormentas', 'fecha': '13 de septiembre', 'enlace': 'https://www.argentina.gob.ar/noticias/x', 'fuente': 'argentina.gob.ar'},
]}
VECINO = {'nombre': 'Ana', 'email': 'ana@dominio.com', 'barrio': 'Retiro'}
VARIABLES_CORREO = ('EMAIL_USER', 'EMAIL_PASSWORD', 'SMTP_SERVER', 'SMTP_PORT')


def _con_entorno(valores):
    """Deja las variables del correo con los valores dados y devuelve como estaban."""
    anteriores = {nombre: os.environ.get(nombre) for nombre in VARIABLES_CORREO}

    for nombre in VARIABLES_CORREO:
        os.environ.pop(nombre, None)
    os.environ.update(valores)

    def restaurar():
        for nombre, valor in anteriores.items():
            os.environ.pop(nombre, None)
            if valor is not None:
                os.environ[nombre] = valor

    return restaurar


def test_correo_del_vecino():
    fila = servicio.riesgo_de_barrio('Retiro', DIAS)
    msg = alertas.correo_vecino(VECINO, fila, SCRAPING)

    assert msg['Subject'] == 'ALERTA en Retiro: lluvia el domingo 13/09'
    texto = msg.get_body(('plain',)).get_content()
    assert 'Hola Ana' in texto and 'Se esperan 45 mm de lluvia' in texto
    assert 'Alerta por tormentas' in texto                       # el aviso del scraping
    assert msg.get_body(('html',)) is not None


def test_correo_sin_credenciales_queda_como_borrador():
    restaurar = _con_entorno({})
    anterior = config.DIR_CORREOS
    config.DIR_CORREOS = Path(tempfile.mkdtemp())
    try:
        fila = servicio.riesgo_de_barrio('Retiro', DIAS)
        resultado = alertas.enviar(alertas.correo_vecino(VECINO, fila, SCRAPING))
        assert resultado['estado'] == 'borrador'
        assert len(list(config.DIR_CORREOS.glob('*.eml'))) == 1
    finally:
        config.DIR_CORREOS = anterior
        restaurar()


def test_correo_se_envia_con_smtp():
    llamadas = {}

    class SmtpFalso:
        def __init__(self, host=None, port=None, context=None, timeout=None):
            llamadas['servidor'] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def login(self, user, password):
            llamadas['login'] = (user, password)

        def send_message(self, msg):
            llamadas['para'] = msg['To']

    restaurar = _con_entorno({'EMAIL_USER': 'yo@gmail.com', 'EMAIL_PASSWORD': 'abcd efgh ijkl mnop'})
    original = smtplib.SMTP_SSL
    smtplib.SMTP_SSL = SmtpFalso
    try:
        fila = servicio.riesgo_de_barrio('Retiro', DIAS)
        resultado = alertas.enviar(alertas.correo_vecino(VECINO, fila, SCRAPING))
    finally:
        smtplib.SMTP_SSL = original
        restaurar()

    assert resultado['estado'] == 'enviado'
    assert llamadas['servidor'] == ('smtp.gmail.com', 465)
    assert llamadas['login'] == ('yo@gmail.com', 'abcdefghijklmnop')     # sin los espacios
    assert llamadas['para'] == 'ana@dominio.com'


def test_correo_rechazado_no_se_pierde():
    class SmtpRechaza:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def login(self, user, password):
            raise smtplib.SMTPAuthenticationError(535, b'credenciales malas')

    restaurar = _con_entorno({'EMAIL_USER': 'yo@gmail.com', 'EMAIL_PASSWORD': 'mala'})
    original, anterior = smtplib.SMTP_SSL, config.DIR_CORREOS
    smtplib.SMTP_SSL = SmtpRechaza
    config.DIR_CORREOS = Path(tempfile.mkdtemp())
    try:
        fila = servicio.riesgo_de_barrio('Retiro', DIAS)
        resultado = alertas.enviar(alertas.correo_vecino(VECINO, fila, SCRAPING))
        assert resultado['estado'] == 'error' and 'rechazó la clave' in resultado['detalle']
        assert len(list(config.DIR_CORREOS.glob('*.eml'))) == 1
    finally:
        smtplib.SMTP_SSL, config.DIR_CORREOS = original, anterior
        restaurar()


if __name__ == '__main__':
    for nombre, funcion in list(globals().items()):
        if nombre.startswith('test_'):
            funcion()
            print(f'ok - {nombre}')

    print('Todas las pruebas pasaron.')
