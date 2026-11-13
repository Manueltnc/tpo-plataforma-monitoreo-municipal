# Correos con smtplib y EmailMessage (N24).
#   - Al vecino: cuando su barrio llega al nivel NIVEL_MINIMO_AVISO (atencion o mas).
#     Un correo por vecino, en palabras simples, con el grafico del pronostico adjunto.
#   - A la guardia municipal (EMAIL_GUARDIA en el .env): el reporte diario adjunto.
#
# Si no hay credenciales (EMAIL_USER y EMAIL_PASSWORD en el .env), si el destinatario
# es de ejemplo (@ejemplo.com) o si el envio falla, el correo NO se pierde: se guarda
# como archivo .eml en data/processed/correos y se puede abrir con Outlook o Thunderbird.

import html
import smtplib
import ssl
from datetime import date, datetime
from email.message import EmailMessage
from pathlib import Path

from monitoreo.apis import usuarios
from monitoreo.app import config, reglas, servicio


def hay_credenciales():
    return config.get_email_user() != '' and config.get_email_password() != ''


def es_destinatario_real(correo):
    return not correo.strip().lower().endswith(config.DOMINIO_DE_EJEMPLO)


def remitente():
    correo = config.get_email_user() or 'monitoreo@ejemplo.com'
    return f'Monitoreo municipal CABA <{correo}>'


def adjuntar_imagen(msg, ruta):
    ruta = Path(ruta)
    msg.add_attachment(ruta.read_bytes(), maintype='image', subtype='png', filename=ruta.name)


# -- Correo para el vecino --

def correo_vecino(usuario, fila, scraping, ruta_grafico=None):
    """fila es el riesgo del barrio del vecino (servicio.riesgo_de_barrio)."""
    barrio = fila['barrio']
    nombre_nivel = reglas.NOMBRES_NIVEL[fila['nivel']]
    peor_dia = fila['proximos_dias'][0]
    for dia in fila['proximos_dias']:
        if dia['fecha'] == fila['fecha']:
            peor_dia = dia

    msg = EmailMessage()
    msg['Subject'] = f'{nombre_nivel.upper()} en {barrio}: {peor_dia["causa"]} el {peor_dia["dia"]}'
    msg['From'] = remitente()
    msg['To'] = usuario['email']

    # Version en texto
    texto = f'Hola {usuario["nombre"]}:\n\n'
    texto += f'Para tu barrio, {barrio}, el {peor_dia["dia"]} el nivel de riesgo por clima es {nombre_nivel.upper()}.\n\n'

    texto += 'Por qué:\n'
    for motivo in fila['motivos']:
        texto += f'  - {motivo}\n'

    texto += f'\nQué te recomendamos:\n  {fila["que_hacer"]}\n\n'

    texto += f'Los próximos días en {barrio}:\n'
    for dia in fila['proximos_dias']:
        texto += f'  - {texto_de_dia(dia)}\n'

    texto += '\nAvisos oficiales sobre el clima:\n'
    if scraping['avisos']:
        for aviso in scraping['avisos']:
            texto += f'  - {aviso["titulo"]} ({aviso["fecha"]}): {aviso["enlace"]}\n'
    else:
        texto += '  Hoy no encontramos noticias oficiales sobre el clima.\n'

    if ruta_grafico:
        texto += '\nTe adjuntamos un gráfico con la lluvia y el viento previstos.\n'

    texto += '\n--\nPlataforma de monitoreo municipal de CABA.\n'
    texto += f'Recibís este correo porque te registraste para el barrio {barrio}.\n'

    msg.set_content(texto)
    msg.add_alternative(html_vecino(usuario, fila, peor_dia, scraping), subtype='html')

    if ruta_grafico:
        adjuntar_imagen(msg, ruta_grafico)

    return msg


def texto_de_dia(dia):
    """'viernes 14/11: Alerta. Lluvia 45 mm, viento hasta 30 km/h, entre 14 y 22 grados.'"""
    return (
        f'{dia["dia"]}: {reglas.NOMBRES_NIVEL[dia["nivel"]]}. '
        f'Lluvia {dia["lluvia_mm"]:.0f} mm, viento hasta {dia["viento_kmh"]} km/h, '
        f'entre {dia["temp_min"]} y {dia["temp_max"]} grados.'
    )


def html_vecino(usuario, fila, peor_dia, scraping):
    """El mismo contenido que el texto, con formato HTML.
    html.escape evita que un titulo raro de la web rompa el correo."""
    colores = {'normal': '#2e7d32', 'atencion': '#f9a825', 'alerta': '#ef6c00', 'emergencia': '#c62828'}
    color = colores[fila['nivel']]
    nombre_nivel = reglas.NOMBRES_NIVEL[fila['nivel']]

    motivos = ''
    for motivo in fila['motivos']:
        motivos += f'<li>{html.escape(motivo)}</li>'

    dias = ''
    for dia in fila['proximos_dias']:
        dias += f'<li>{html.escape(texto_de_dia(dia))}</li>'

    avisos = ''
    for aviso in scraping['avisos']:
        avisos += f'<li><a href="{html.escape(aviso["enlace"])}">{html.escape(aviso["titulo"])}</a> ({aviso["fecha"]})</li>'
    if avisos == '':
        avisos = '<li>Hoy no encontramos noticias oficiales sobre el clima.</li>'

    return (
        '<html><body style="font-family: Arial, sans-serif; max-width: 600px">'
        f'<p>Hola {html.escape(usuario["nombre"])}:</p>'
        f'<p>Para tu barrio, <b>{fila["barrio"]}</b>, el {peor_dia["dia"]} el nivel de riesgo por clima es:</p>'
        f'<p style="background:{color}; color:white; padding:10px; font-size:20px; text-align:center">'
        f'<b>{nombre_nivel.upper()}</b></p>'
        f'<h3>Por qué</h3><ul>{motivos}</ul>'
        f'<h3>Qué te recomendamos</h3><p>{html.escape(fila["que_hacer"])}</p>'
        f'<h3>Los próximos días en {fila["barrio"]}</h3><ul>{dias}</ul>'
        f'<h3>Avisos oficiales sobre el clima</h3><ul>{avisos}</ul>'
        '<p style="color:gray; font-size:12px">Plataforma de monitoreo municipal de CABA. '
        f'Recibís este correo porque te registraste para el barrio {fila["barrio"]}.</p>'
        '</body></html>'
    )


# -- Correo para la guardia municipal --

def correo_guardia(riesgo, ruta_reporte, ruta_grafico=None):
    grupos = servicio.barrios_por_nivel(riesgo)

    msg = EmailMessage()
    msg['Subject'] = f'Reporte diario de riesgo por clima - {date.today().strftime("%d/%m/%Y")}'
    msg['From'] = remitente()
    msg['To'] = ', '.join(config.get_correos_guardia())

    texto = 'Reporte diario de riesgo por clima en CABA.\n\n'
    for nivel in ['emergencia', 'alerta', 'atencion', 'normal']:
        nombre = reglas.NOMBRES_NIVEL[nivel]
        cantidad = len(grupos[nivel])
        texto += f'{nombre}: {cantidad} barrios\n'

    texto += f'\nAvisos oficiales sobre el clima encontrados hoy: {len(riesgo["scraping"]["avisos"])}\n'
    texto += 'El reporte completo, barrio por barrio, va en el archivo adjunto.\n'

    msg.set_content(texto)

    ruta_reporte = Path(ruta_reporte)
    msg.add_attachment(ruta_reporte.read_bytes(), maintype='text', subtype='markdown', filename=ruta_reporte.name)

    if ruta_grafico:
        adjuntar_imagen(msg, ruta_grafico)

    return msg


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


def conectar_y_enviar(msg):
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
    destinatarios = msg['To'].split(',')

    reales = []
    for correo in destinatarios:
        if es_destinatario_real(correo):
            reales.append(correo)

    if len(reales) == 0:
        ruta = guardar_borrador(msg)
        return {'estado': 'borrador', 'detalle': f'destinatario de ejemplo, guardado en {ruta.name}'}

    if not hay_credenciales():
        ruta = guardar_borrador(msg)
        return {'estado': 'borrador', 'detalle': f'faltan EMAIL_USER y EMAIL_PASSWORD en el .env, guardado en {ruta.name}'}

    try:
        conectar_y_enviar(msg)
    except smtplib.SMTPAuthenticationError as error:
        ruta = guardar_borrador(msg)
        return {'estado': 'error', 'detalle': f'el servidor rechazó la clave ({error.smtp_code}), guardado en {ruta.name}'}
    except (smtplib.SMTPException, OSError) as error:
        ruta = guardar_borrador(msg)
        return {'estado': 'error', 'detalle': f'no se pudo enviar ({error}), guardado en {ruta.name}'}

    return {'estado': 'enviado', 'detalle': 'para ' + msg['To']}


def notificar(riesgo, ruta_reporte, ruta_grafico=None):
    """Manda el reporte a la guardia y avisa a cada vecino cuyo barrio esta en riesgo.
    Devuelve una lista de (a quien, resultado del envio)."""
    resultados = []

    if config.get_correos_guardia():
        msg = correo_guardia(riesgo, ruta_reporte, ruta_grafico)
        resultados.append(('reporte para la guardia', enviar(msg)))

    corte = reglas.NIVELES.index(config.NIVEL_MINIMO_AVISO)

    for usuario in usuarios.lista_de_usuarios():
        fila = servicio.buscar_barrio(riesgo, usuario['barrio'])

        if reglas.NIVELES.index(fila['nivel']) >= corte:
            msg = correo_vecino(usuario, fila, riesgo['scraping'], ruta_grafico)
            resultados.append((f'aviso a {usuario["email"]} ({usuario["barrio"]})', enviar(msg)))

    return resultados
