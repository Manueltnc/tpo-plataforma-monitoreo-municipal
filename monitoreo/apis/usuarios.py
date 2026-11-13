# Vecinos registrados en la API propia (N15, N17).
# Se guardan en un CSV (data/usuarios.csv) que se lee y se escribe con pandas.
# Cada vecino tiene nombre, email, el barrio donde vive y su API key.
# El CSV esta en .gitignore porque tiene las claves.

import re
import secrets
import time
from datetime import datetime

import pandas as pd

from monitoreo.app import barrios, config

COLUMNAS = ['nombre', 'email', 'barrio', 'api_key', 'fecha_alta']


class UsuarioExistente(Exception):
    pass


def leer_usuarios(ruta=None):
    """Devuelve un DataFrame con los usuarios (vacio si todavia no hay ninguno)."""
    ruta = ruta or config.RUTA_USUARIOS

    if not ruta.exists():
        return pd.DataFrame(columns=COLUMNAS)

    # dtype=str: todo se lee como texto, asi la clave no se transforma en numero
    return pd.read_csv(ruta, dtype=str)


def email_valido(email):
    return re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) is not None


def registrar_usuario(nombre, email, barrio, ruta=None):
    """Agrega un vecino al CSV y devuelve su API key."""
    ruta = ruta or config.RUTA_USUARIOS
    nombre = nombre.strip()
    email = email.strip().lower()
    barrio_oficial = barrios.validar_barrio(barrio)

    if len(nombre) < 2:
        raise ValueError('El nombre es muy corto')

    if not email_valido(email):
        raise ValueError('El email no es válido')

    if barrio_oficial is None:
        raise ValueError(f'No existe el barrio "{barrio}"')

    usuarios = leer_usuarios(ruta)

    if email in usuarios['email'].values:
        raise UsuarioExistente(f'Ya hay un usuario registrado con {email}')

    clave = secrets.token_hex(16)     # 32 caracteres al azar

    nuevo = pd.DataFrame([{
        'nombre': nombre,
        'email': email,
        'barrio': barrio_oficial,
        'api_key': clave,
        'fecha_alta': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }])
    usuarios = pd.concat([usuarios, nuevo], ignore_index=True)

    ruta.parent.mkdir(parents=True, exist_ok=True)
    usuarios.to_csv(ruta, index=False)

    return clave


def buscar_por_clave(clave, ruta=None):
    """Devuelve el usuario (diccionario) dueño de esa API key, o None."""
    usuarios = leer_usuarios(ruta)
    encontrados = usuarios[usuarios['api_key'] == clave]

    if len(encontrados) == 0:
        return None

    return encontrados.iloc[0].to_dict()


def lista_de_usuarios(ruta=None):
    """Todos los usuarios como lista de diccionarios (para mandarles los correos)."""
    return leer_usuarios(ruta).to_dict('records')


class LimitadorPedidos:
    """Rate limiting: como mucho `maximo` pedidos por clave en una ventana de 60 segundos."""

    def __init__(self, maximo, ventana=60):
        self.maximo = maximo
        self.ventana = ventana
        self.pedidos = {}           # {clave: [momentos de los ultimos pedidos]}

    def permitir(self, clave, ahora=None):
        if ahora is None:
            ahora = time.time()

        # nos quedamos solo con los pedidos que estan dentro de la ventana
        anteriores = self.pedidos.get(clave, [])
        recientes = []
        for momento in anteriores:
            if ahora - momento < self.ventana:
                recientes.append(momento)

        if len(recientes) >= self.maximo:
            self.pedidos[clave] = recientes
            return False

        recientes.append(ahora)
        self.pedidos[clave] = recientes
        return True
