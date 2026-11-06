# Pruebas simples, sin librerias extra.
# Correr desde la carpeta del proyecto:  python -m tests.test_entrega2

import json
import os
import smtplib
import tempfile
from pathlib import Path

from monitoreo.apis import clima, usuarios
from monitoreo.app import barrios, config, reglas
from monitoreo.email import alertas
from monitoreo.etl import extraer, transformar


def test_puntaje_amenaza():
    lluvia = (config.LLUVIA_ATENCION, config.LLUVIA_ALERTA, config.LLUVIA_EMERGENCIA)

    assert reglas.puntaje_amenaza(0, *lluvia) == 0
    assert reglas.puntaje_amenaza(config.LLUVIA_ATENCION, *lluvia) == config.CORTE_ATENCION
    assert reglas.puntaje_amenaza(config.LLUVIA_ALERTA, *lluvia) == config.CORTE_ALERTA
    assert reglas.puntaje_amenaza(config.LLUVIA_EMERGENCIA, *lluvia) == config.CORTE_EMERGENCIA
    assert reglas.puntaje_amenaza(1000, *lluvia) == 100

    # a mas lluvia, nunca menos puntos
    anterior = 0
    for mm in range(0, 200, 5):
        puntos = reglas.puntaje_amenaza(mm, *lluvia)
        assert puntos >= anterior
        anterior = puntos


def test_indice_y_vulnerabilidad():
    barrios._vulnerabilidad.clear()
    barrios._vulnerabilidad.update({
        'Palermo': {'reclamos': 2000, 'percentil': 1.0, 'factor': 1.25},
        'Retiro': {'reclamos': 100, 'percentil': 0.0, 'factor': 0.75},
    })

    quieto = {'lluvia_mm': 0, 'viento_kmh': 0}
    assert reglas.evaluar_riesgo('Palermo', quieto)['puntos'] == 0     # sin peligro no hay riesgo

    brisa = {'lluvia_mm': 0, 'viento_kmh': 10}
    assert reglas.clasificar(reglas.evaluar_riesgo('Palermo', brisa)['puntos']) == 'normal'

    tormenta = {'lluvia_mm': 45, 'viento_kmh': 20}
    alto = reglas.evaluar_riesgo('Palermo', tormenta)['puntos']
    bajo = reglas.evaluar_riesgo('Retiro', tormenta)['puntos']
    assert alto > bajo                                                  # misma lluvia, distinto barrio

    con_viento = {'lluvia_mm': 45, 'viento_kmh': 45}
    assert reglas.peligro_meteorologico(con_viento)['peligro'] > reglas.peligro_meteorologico(tormenta)['peligro']

    assert reglas.clasificar(10) == 'normal'
    assert reglas.clasificar(20) == 'atencion'
    assert reglas.clasificar(45) == 'alerta'
    assert reglas.clasificar(70) == 'emergencia'

    barrios._vulnerabilidad.clear()


def test_alias_de_barrios():
    assert barrios.validar_barrio('Boca') == 'La Boca'
    assert barrios.validar_barrio('Paternal') == 'La Paternal'
    assert barrios.validar_barrio('Villa Gral. Mitre') == 'Villa General Mitre'
    assert barrios.validar_barrio('Agronomía') == 'Agronomia'
    assert barrios.validar_barrio('Narnia') is None


def test_etl_con_la_muestra():
    crudo = extraer.leer_suaci(config.RUTA_FIXTURE_SUACI)       # lee el ZIP
    limpio, info = transformar.limpiar_suaci(crudo)
    assert info['filas_limpias'] <= info['filas_originales']
    assert info['barrio_desconocido'] == 0

    marcado = transformar.marcar_reclamos_clima(limpio)
    tabla = transformar.calcular_vulnerabilidad(transformar.contar_por_barrio(marcado))

    assert len(tabla) == 48
    assert tabla['factor_vulnerabilidad'].min() >= config.FACTOR_MIN
    assert tabla['factor_vulnerabilidad'].max() <= config.FACTOR_MAX
    assert tabla['reclamos'].sum() == int(marcado['es_clima'].sum())

    semanal = transformar.serie_semanal(marcado)
    assert (semanal['reclamos'] >= 0).all()
    assert len(transformar.comparar_semestres(marcado)) > 0


def test_usuarios_y_claves():
    ruta = Path(tempfile.mkdtemp()) / 'prueba.db'

    clave = usuarios.registrar_usuario('Ana', 'Ana@Ejemplo.com', ruta)
    assert usuarios.validar_clave(clave, ruta)['email'] == 'ana@ejemplo.com'
    assert usuarios.validar_clave('otra-clave', ruta) is None

    try:
        usuarios.registrar_usuario('Ana', 'ana@ejemplo.com', ruta)
        assert False, 'tendria que fallar por email repetido'
    except usuarios.UsuarioExistente:
        pass

    for email in ('sin-arroba', 'a@b', 'a b@c.com'):
        try:
            usuarios.registrar_usuario('Ana', email, ruta)
            assert False, f'{email} no es valido'
        except ValueError:
            pass


def test_limitador():
    limitador = usuarios.LimitadorPedidos(maximo=3, ventana=60)

    assert limitador.permitir('k', ahora=0)
    assert limitador.permitir('k', ahora=1)
    assert limitador.permitir('k', ahora=2)
    assert not limitador.permitir('k', ahora=3)       # cuarto pedido dentro del minuto
    assert limitador.permitir('k', ahora=61)          # ya paso la ventana


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


# -- Correo (N24) --

RIESGO_FALSO = {
    'dia': {'fecha': '2026-09-14', 'lluvia_mm': 40.0, 'viento_kmh': 45.0},
    'conteo': {'emergencia': 0, 'alerta': 1, 'atencion': 1, 'normal': 1},
    'resultados': [
        {'barrio': 'Palermo', 'puntos': 66.4, 'peligro': 53.1, 'factor': 1.25, 'motivos': ['Lluvia prevista: 40 mm'], 'nivel': 'alerta'},
        {'barrio': 'Retiro', 'puntos': 30.0, 'peligro': 40.0, 'factor': 0.75, 'motivos': [], 'nivel': 'atencion'},
        {'barrio': 'Boedo', 'puntos': 5.0, 'peligro': 5.0, 'factor': 1.0, 'motivos': [], 'nivel': 'normal'},
    ],
}

VARIABLES_CORREO = ('EMAIL_USER', 'EMAIL_PASSWORD', 'EMAIL_RECEIVER', 'SMTP_SERVER', 'SMTP_PORT')


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


def test_armado_del_correo():
    carpeta = Path(tempfile.mkdtemp())
    reporte = carpeta / 'reporte.md'
    reporte.write_text('# reporte', encoding='utf-8')
    grafico = carpeta / 'grafico.png'
    grafico.write_bytes(b'\x89PNG fake')

    msg = alertas.armar_correo_reporte(RIESGO_FALSO, [reporte, grafico])

    assert 'Reporte de riesgo urbano' in msg['Subject']
    assert msg.get_body(('plain',)) is not None and msg.get_body(('html',)) is not None
    nombres = [parte.get_filename() for parte in msg.iter_attachments()]
    assert nombres == ['reporte.md', 'grafico.png']

    graves = alertas.filas_en_alerta(RIESGO_FALSO)
    assert [f['barrio'] for f in graves] == ['Palermo']          # solo el que llega a "alerta"
    alerta = alertas.armar_correo_alerta(graves, RIESGO_FALSO)
    assert '[ALERTA]' in alerta['Subject'] and 'Palermo' in alerta.get_content()


def test_correo_sin_credenciales_queda_como_borrador():
    restaurar = _con_entorno({})
    anterior = config.DIR_CORREOS
    config.DIR_CORREOS = Path(tempfile.mkdtemp())
    try:
        resultado = alertas.enviar(alertas.armar_correo_reporte(RIESGO_FALSO))
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

    restaurar = _con_entorno({
        'EMAIL_USER': 'yo@gmail.com', 'EMAIL_PASSWORD': 'abcd efgh ijkl mnop',
        'EMAIL_RECEIVER': 'a@dominio.com, b@dominio.com',
    })
    original = smtplib.SMTP_SSL
    smtplib.SMTP_SSL = SmtpFalso
    try:
        resultado = alertas.enviar(alertas.armar_correo_reporte(RIESGO_FALSO))
    finally:
        smtplib.SMTP_SSL = original
        restaurar()

    assert resultado['estado'] == 'enviado'
    assert llamadas['servidor'] == ('smtp.gmail.com', 465)
    assert llamadas['login'] == ('yo@gmail.com', 'abcdefghijklmnop')     # sin los espacios
    assert llamadas['para'] == 'a@dominio.com, b@dominio.com'


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

    restaurar = _con_entorno({'EMAIL_USER': 'yo@gmail.com', 'EMAIL_PASSWORD': 'mala', 'EMAIL_RECEIVER': 'a@dominio.com'})
    original, anterior = smtplib.SMTP_SSL, config.DIR_CORREOS
    smtplib.SMTP_SSL = SmtpRechaza
    config.DIR_CORREOS = Path(tempfile.mkdtemp())
    try:
        resultado = alertas.enviar(alertas.armar_correo_reporte(RIESGO_FALSO))
        assert resultado['estado'] == 'error' and 'autenticacion' in resultado['detalle']
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
