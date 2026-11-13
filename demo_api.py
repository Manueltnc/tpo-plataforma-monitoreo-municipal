# Demostracion de la API propia (N15, N16, N17).
# Levanta el servidor en segundo plano y lo consulta con requests, como lo haria
# la app de un vecino: se registra con su barrio y pide su riesgo.
# Usa un archivo de usuarios temporal, asi se puede correr todas las veces que se quiera.

import json
import tempfile
import threading
import time
from pathlib import Path

import uvicorn

from monitoreo.app import config

config.RUTA_USUARIOS = Path(tempfile.mkdtemp()) / 'usuarios_demo.csv'

from monitoreo.apis import cliente, servidor


def paso(texto):
    print()
    print(texto)


def intentar(descripcion, funcion, *args):
    try:
        return funcion(*args)
    except cliente.ErrorApi as error:
        print(f'  Error esperado ({descripcion}): {error}')
        return None


def levantar_servidor():
    # si ya hay un servidor prendido, la demo hablaria con ese y no con el suyo
    try:
        cliente.revisar_salud()
        raise SystemExit('Ya hay un servidor prendido en el puerto 8000. Cerralo con Ctrl+C y volve a correr la demo.')
    except cliente.ErrorApi:
        pass

    opciones = uvicorn.Config(servidor.app, host=config.API_HOST, port=config.API_PUERTO, log_level='warning')
    uv = uvicorn.Server(opciones)
    hilo = threading.Thread(target=uv.run, daemon=True)
    hilo.start()

    # esperamos a que el servidor conteste
    for intento in range(50):
        try:
            cliente.revisar_salud()
            return uv, hilo
        except cliente.ErrorApi:
            time.sleep(0.2)

    raise SystemExit('El servidor no arrancó')


def main():
    uv, hilo = levantar_servidor()

    try:
        paso('1. GET /salud (no pide clave)')
        print(' ', cliente.revisar_salud())

        paso('2. POST /usuarios: una vecina de Palermo se registra')
        usuario = cliente.registrar_usuario('Ana Vecina', 'ana@ejemplo.com', 'Palermo')
        print(f'  Registrada: {usuario["nombre"]}, barrio {usuario["barrio"]}')
        print(f'  Su API key: {usuario["api_key"]}')
        clave = usuario['api_key']

        paso('3. GET /mi-barrio con su API key (respuesta completa en JSON)')
        datos = cliente.consultar_mi_barrio(clave)
        print(json.dumps(datos, indent=2, ensure_ascii=False))

        paso('4. GET /riesgo/{barrio}: consulta otro barrio')
        otro = cliente.consultar_barrio(clave, 'La Boca')
        print(f'  {otro["resumen"]}')

        paso('5. Errores que maneja la API')
        intentar('sin API key', cliente.consultar_mi_barrio, '')
        intentar('API key inventada', cliente.consultar_mi_barrio, 'clave-inventada')
        intentar('barrio que no existe', cliente.consultar_barrio, clave, 'Narnia')
        intentar('email ya registrado', cliente.registrar_usuario, 'Ana', 'ana@ejemplo.com', 'Palermo')
        intentar('barrio invalido al registrarse', cliente.registrar_usuario, 'Juan', 'juan@ejemplo.com', 'Narnia')
    finally:
        uv.should_exit = True
        hilo.join(5)

    print()
    print('Demo terminada.')


if __name__ == '__main__':
    main()
