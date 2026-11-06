# Usuarios y API keys de la API propia (N15, N17).
# Los usuarios se guardan en SQLite (data/usuarios.db). La API key se muestra
# una sola vez al registrarse y en la base queda solo su hash, asi que si alguien
# lee la base no puede usar las claves.

import hashlib
import re
import secrets
import sqlite3
import time
from collections import deque
from datetime import datetime

from monitoreo.app import config


class UsuarioExistente(Exception):
    pass


def _conectar(ruta=None):
    ruta = ruta or config.RUTA_DB_USUARIOS
    ruta.parent.mkdir(parents=True, exist_ok=True)

    conexion = sqlite3.connect(ruta)
    conexion.execute(
        'CREATE TABLE IF NOT EXISTS usuarios ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'nombre TEXT NOT NULL, '
        'email TEXT NOT NULL UNIQUE, '
        'clave_hash TEXT NOT NULL, '
        'creado TEXT NOT NULL)'
    )
    return conexion


def hashear(clave):
    return hashlib.sha256(clave.encode('utf-8')).hexdigest()


def email_valido(email):
    return re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) is not None


def registrar_usuario(nombre, email, ruta=None):
    """Crea el usuario y devuelve su API key (unica vez que se ve completa)."""
    nombre = nombre.strip()
    email = email.strip().lower()

    if len(nombre) < 2:
        raise ValueError('El nombre es muy corto')

    if not email_valido(email):
        raise ValueError('El email no es valido')

    clave = secrets.token_urlsafe(24)
    conexion = _conectar(ruta)

    try:
        conexion.execute(
            'INSERT INTO usuarios (nombre, email, clave_hash, creado) VALUES (?, ?, ?, ?)',
            (nombre, email, hashear(clave), datetime.now().isoformat(timespec='seconds')),
        )
        conexion.commit()
    except sqlite3.IntegrityError:
        raise UsuarioExistente(f'Ya hay un usuario registrado con {email}')
    finally:
        conexion.close()

    return clave


def validar_clave(clave, ruta=None):
    """Devuelve {'nombre', 'email'} si la API key existe, o None."""
    conexion = _conectar(ruta)

    try:
        fila = conexion.execute(
            'SELECT nombre, email FROM usuarios WHERE clave_hash = ?', (hashear(clave),)
        ).fetchone()
    finally:
        conexion.close()

    if fila is None:
        return None

    return {'nombre': fila[0], 'email': fila[1]}


class LimitadorPedidos:
    """Rate limiting: como mucho `maximo` pedidos por clave en una ventana de 60 segundos."""

    def __init__(self, maximo, ventana=60):
        self.maximo = maximo
        self.ventana = ventana
        self.pedidos = {}

    def permitir(self, clave, ahora=None):
        ahora = time.time() if ahora is None else ahora
        cola = self.pedidos.setdefault(clave, deque())

        while cola and ahora - cola[0] >= self.ventana:
            cola.popleft()

        if len(cola) >= self.maximo:
            return False

        cola.append(ahora)
        return True
