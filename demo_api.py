# Demostracion de la API propia (N15, N16, N17).
# Levanta el servidor en segundo plano y lo consulta con requests:
# registro con POST, consultas con API key, y los errores 401, 404 y 409.
# Usa una base de usuarios temporal, asi se puede correr todas las veces que se quiera.

import tempfile
import threading
import time
from pathlib import Path

import uvicorn

from monitoreo.app import config

config.RUTA_DB_USUARIOS = Path(tempfile.mkdtemp()) / 'usuarios_demo.db'

from monitoreo.apis import cliente, servidor


def paso(texto):
    print()
    print('-' * 60)
    print(texto)


def intentar(descripcion, funcion, *args):
    try:
        resultado = funcion(*args)
        print(f'  OK: {descripcion}')
        return resultado
    except cliente.ErrorApi as error:
        print(f'  Error esperado en "{descripcion}": {error}')
        return None


def levantar_servidor():
    opciones = uvicorn.Config(servidor.app, host=config.API_HOST, port=config.API_PUERTO, log_level='warning')
    uv = uvicorn.Server(opciones)
    hilo = threading.Thread(target=uv.run, daemon=True)
    hilo.start()

    for _ in range(50):
        try:
            cliente.revisar_salud()
            return uv, hilo
        except cliente.ErrorApi:
            time.sleep(0.2)

    raise SystemExit('El servidor no arranco')


def main():
    uv, hilo = levantar_servidor()

    try:
        paso('1. GET /salud (publica, no pide clave)')
        print(' ', cliente.revisar_salud())

        paso('2. GET /riesgo sin API key')
        intentar('consulta sin clave', cliente.consultar_riesgo, '')

        paso('3. POST /usuarios (registro)')
        usuario = cliente.registrar_usuario('Alumno Demo', 'alumno@ejemplo.com')
        print(f'  Usuario: {usuario["nombre"]} | API key: {usuario["api_key"][:8]}... ({usuario["aviso"]})')
        clave = usuario['api_key']

        paso('4. POST /usuarios repetido (mismo email)')
        intentar('registro duplicado', cliente.registrar_usuario, 'Alumno Demo', 'alumno@ejemplo.com')

        paso('5. GET /riesgo con API key y filtro nivel_minimo=atencion')
        datos = intentar('consulta con clave', cliente.consultar_riesgo, clave, 'atencion')
        if datos:
            print(f'  Dia evaluado: {datos["dia_evaluado"]} | barrios en atencion o mas: {datos["cantidad"]}')
            for fila in datos['barrios'][:5]:
                print(f'  - {fila["barrio"]}: {fila["nivel"]} (indice {fila["indice"]})')

        paso('6. GET /riesgo/{barrio}')
        fila = intentar('barrio Palermo', cliente.consultar_barrio, clave, 'Palermo')
        if fila:
            print(f'  Palermo: {fila["nivel"]}, indice {fila["indice"]}, factor {fila["factor_vulnerabilidad"]}')
        intentar('barrio que no existe', cliente.consultar_barrio, clave, 'Narnia')

        paso('7. GET /riesgo con una clave inventada')
        intentar('clave invalida', cliente.consultar_riesgo, 'clave-inventada')
    finally:
        uv.should_exit = True
        hilo.join(5)

    print()
    print('Demo terminada.')


if __name__ == '__main__':
    main()
