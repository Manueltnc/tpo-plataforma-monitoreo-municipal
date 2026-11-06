# Envio de correos con smtplib y EmailMessage (N24).
#   - Reporte diario con adjuntos (reporte, graficos y Excel del ETL)
#   - Correo de alerta cuando algun barrio llega al nivel configurado
#
# Si no hay credenciales (EMAIL_USER y EMAIL_PASSWORD en el .env), o no hay destinatarios
# reales, o el envio falla, el mensaje NO se pierde: se guarda como borrador .eml en
# data/processed/correos y se avisa por pantalla.

import html
import mimetypes
import smtplib
import ssl
from datetime import date, datetime
from email.message import EmailMessage
from pathlib import Path

from monitoreo.app import barrios, config, reglas, servicio

DOMINIO_DE_EJEMPLO = '@ejemplo.com'


# -- Configuracion --

def destinatarios_configurados():
    """Destinatarios reales: EMAIL_RECEIVER del .env o, si no hay, la lista de config.py.
    Se descartan los de ejemplo (@ejemplo.com)."""
    texto = config.get_email_receiver()

    if texto:
        lista = [d.strip() for d in texto.split(',') if d.strip()]
    else:
        lista = list(config.CORREOS)

    return [d for d in lista if not d.lower().endswith(DOMINIO_DE_EJEMPLO)]


def hay_credenciales():
    return bool(config.get_email_user() and config.get_email_password())


# -- Armado de los mensajes --

def _filas_ordenadas(riesgo):
    return sorted(riesgo['resultados'], key=lambda fila: fila['puntos'], reverse=True)


def filas_en_alerta(riesgo):
    """Barrios cuyo nivel llega al minimo configurado para mandar alerta."""
    corte = servicio.ORDEN_NIVELES.index(config.NIVEL_MINIMO_ALERTA)

    return [f for f in _filas_ordenadas(riesgo) if servicio.ORDEN_NIVELES.index(f['nivel']) >= corte]


def texto_reporte(riesgo):
    dia = riesgo['dia']
    conteo = riesgo['conteo']

    lineas = [
        'Reporte de riesgo urbano - CABA',
        f'Dia evaluado: {dia["fecha"]} (lluvia {dia["lluvia_mm"]:.1f} mm, viento {dia["viento_kmh"]:.0f} km/h)',
        '',
        f'Emergencia: {conteo["emergencia"]} | Alerta: {conteo["alerta"]} | '
        f'Atencion: {conteo["atencion"]} | Normal: {conteo["normal"]}',
        '',
        'Barrios con mayor indice:',
    ]

    for fila in _filas_ordenadas(riesgo)[:10]:
        lineas.append(f'  - {fila["barrio"]}: {fila["nivel"]} (indice {fila["puntos"]})')

    lineas += ['', 'El detalle completo (reporte, graficos y tablas) viene en los adjuntos.']

    return '\n'.join(lineas)


def html_reporte(riesgo):
    dia = riesgo['dia']
    conteo = riesgo['conteo']

    filas = ''
    for fila in _filas_ordenadas(riesgo)[:10]:
        filas += (
            f'<tr><td>{html.escape(fila["barrio"])}</td><td>{html.escape(fila["nivel"])}</td>'
            f'<td>{fila["puntos"]}</td></tr>'
        )

    return (
        '<html><body>'
        '<h2>Reporte de riesgo urbano - CABA</h2>'
        f'<p>Dia evaluado: <b>{dia["fecha"]}</b> (lluvia {dia["lluvia_mm"]:.1f} mm, '
        f'viento {dia["viento_kmh"]:.0f} km/h)</p>'
        f'<p>Emergencia: <b>{conteo["emergencia"]}</b> | Alerta: <b>{conteo["alerta"]}</b> | '
        f'Atencion: <b>{conteo["atencion"]}</b> | Normal: <b>{conteo["normal"]}</b></p>'
        '<table border="1" cellpadding="4" cellspacing="0">'
        '<tr><th>Barrio</th><th>Nivel</th><th>Indice</th></tr>'
        f'{filas}</table>'
        '<p>El detalle completo viene en los adjuntos.</p>'
        '</body></html>'
    )


def _adjuntar(msg, ruta):
    ruta = Path(ruta)
    tipo, _ = mimetypes.guess_type(ruta.name)
    principal, secundario = (tipo or 'application/octet-stream').split('/', 1)

    msg.add_attachment(ruta.read_bytes(), maintype=principal, subtype=secundario, filename=ruta.name)


def _encabezados(msg, asunto):
    remitente = config.get_email_user() or 'monitoreo@ejemplo.com'
    para = destinatarios_configurados() or list(config.CORREOS)

    msg['Subject'] = asunto
    msg['From'] = f'Monitoreo municipal CABA <{remitente}>'
    msg['To'] = ', '.join(para)


def armar_correo_reporte(riesgo, adjuntos=()):
    """Correo del reporte diario: cuerpo en texto y en HTML, y los archivos adjuntos."""
    msg = EmailMessage()
    _encabezados(msg, f'Reporte de riesgo urbano CABA - {date.today()}')

    msg.set_content(texto_reporte(riesgo))
    msg.add_alternative(html_reporte(riesgo), subtype='html')

    for ruta in adjuntos:
        _adjuntar(msg, ruta)

    return msg


def armar_correo_alerta(filas, riesgo):
    """Correo de alerta con un bloque por cada barrio que llego al nivel minimo."""
    msg = EmailMessage()
    _encabezados(msg, f'[ALERTA] {len(filas)} barrios en {config.NIVEL_MINIMO_ALERTA} o mas - {riesgo["dia"]["fecha"]}')

    texto = f'Dia evaluado: {riesgo["dia"]["fecha"]}\n\n'
    for fila in filas:
        texto += barrios.armar_mensaje(
            fila['barrio'], 'riesgo urbano', fila['nivel'], fila['puntos'], fila['motivos'],
        )
        texto += f'{reglas.que_hacer(fila["nivel"])}\n\n'

    msg.set_content(texto)

    return msg


def adjuntos_del_reporte(ruta_reporte=None):
    """El reporte, los graficos y el Excel del ETL (los que existan)."""
    adjuntos = []

    if ruta_reporte and Path(ruta_reporte).exists():
        adjuntos.append(Path(ruta_reporte))

    carpeta_graficos = config.DIR_PROCESADOS / 'graficos'
    if carpeta_graficos.exists():
        adjuntos += sorted(carpeta_graficos.glob('*.png'))

    excel = config.DIR_PROCESADOS / 'resumen_etl.xlsx'
    if excel.exists():
        adjuntos.append(excel)

    return adjuntos


# -- Envio --

def guardar_borrador(msg):
    config.DIR_CORREOS.mkdir(parents=True, exist_ok=True)

    marca = datetime.now().strftime('%Y%m%d_%H%M%S')
    contador = 1
    ruta = config.DIR_CORREOS / f'correo_{marca}_{contador}.eml'
    while ruta.exists():
        contador += 1
        ruta = config.DIR_CORREOS / f'correo_{marca}_{contador}.eml'

    ruta.write_bytes(bytes(msg))

    return ruta


def _conectar_y_enviar(msg):
    servidor = config.get_smtp_server()
    puerto = config.get_smtp_port()
    contexto = ssl.create_default_context()
    usuario = config.get_email_user()
    clave = config.get_email_password()

    if puerto == 465:
        # conexion cifrada desde el principio (SSL)
        with smtplib.SMTP_SSL(host=servidor, port=puerto, context=contexto, timeout=config.TIMEOUT) as conexion:
            conexion.login(user=usuario, password=clave)
            conexion.send_message(msg)
    else:
        # conexion normal que se cifra con starttls (puerto 587)
        with smtplib.SMTP(host=servidor, port=puerto, timeout=config.TIMEOUT) as conexion:
            conexion.ehlo()
            conexion.starttls(context=contexto)
            conexion.ehlo()
            conexion.login(user=usuario, password=clave)
            conexion.send_message(msg)


def enviar(msg):
    """Envia el mensaje. Devuelve {'estado': 'enviado' | 'borrador' | 'error', 'detalle': texto}."""
    if not destinatarios_configurados():
        ruta = guardar_borrador(msg)
        return {'estado': 'borrador', 'detalle': f'no hay destinatarios reales (EMAIL_RECEIVER); guardado en {ruta.name}'}

    if not hay_credenciales():
        ruta = guardar_borrador(msg)
        return {'estado': 'borrador', 'detalle': f'faltan EMAIL_USER y EMAIL_PASSWORD en el .env; guardado en {ruta.name}'}

    try:
        _conectar_y_enviar(msg)
    except smtplib.SMTPAuthenticationError as error:
        ruta = guardar_borrador(msg)
        return {'estado': 'error', 'detalle': f'autenticacion rechazada ({error.smtp_code}); guardado en {ruta.name}'}
    except (smtplib.SMTPException, OSError) as error:
        ruta = guardar_borrador(msg)
        return {'estado': 'error', 'detalle': f'no se pudo enviar ({error}); guardado en {ruta.name}'}

    return {'estado': 'enviado', 'detalle': 'para ' + msg['To']}


def notificar(riesgo, ruta_reporte=None):
    """Manda el reporte diario y, si hay barrios en alerta, el correo de alerta."""
    resultados = []

    reporte = armar_correo_reporte(riesgo, adjuntos_del_reporte(ruta_reporte))
    resultados.append(('reporte diario', enviar(reporte)))

    graves = filas_en_alerta(riesgo)
    if graves:
        resultados.append(('alerta', enviar(armar_correo_alerta(graves, riesgo))))

    return resultados
