# API propia del proyecto, hecha con FastAPI (N15, N17).
# Esta pensada para el vecino: se registra con su barrio y consulta su riesgo.
#
#   GET  /salud            publica, para ver que el servidor esta vivo
#   POST /usuarios         registro: nombre, email y barrio. Devuelve la API key
#   GET  /mi-barrio        riesgo del barrio con el que se registro (necesita API key)
#   GET  /riesgo/{barrio}  riesgo de cualquier barrio (necesita API key)
#
# La API key se manda en el header X-API-Key.
# Para levantarla:  python -m uvicorn monitoreo.apis.servidor:app

from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from monitoreo.apis import usuarios
from monitoreo.app import barrios, config, reglas, servicio

app = FastAPI(title='Monitoreo de riesgo por clima - CABA', version='3.0')

limitador = usuarios.LimitadorPedidos(config.LIMITE_PEDIDOS_POR_MINUTO)


class UsuarioEntrada(BaseModel):
    nombre: str
    email: str
    barrio: str


def exigir_clave(x_api_key: Optional[str] = Header(default=None)):
    """Corta el pedido si la API key falta, no existe o se paso del limite."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail='Falta el header X-API-Key')

    usuario = usuarios.buscar_por_clave(x_api_key)
    if usuario is None:
        raise HTTPException(status_code=401, detail='La API key no es válida')

    if not limitador.permitir(x_api_key):
        raise HTTPException(status_code=429, detail='Demasiados pedidos, esperá un minuto')

    return usuario


def respuesta_de_barrio(barrio):
    """Arma el JSON que devuelve la API para un barrio."""
    riesgo = servicio.riesgo_actual()
    fila = servicio.buscar_barrio(riesgo, barrio)

    dias = []
    for dia in fila['proximos_dias']:
        dias.append({
            'fecha': str(dia['fecha']),
            'dia': dia['dia'],
            'nivel': dia['nivel'],
            'lluvia_mm': dia['lluvia_mm'],
            'viento_max_kmh': dia['viento_kmh'],
            'temp_min': dia['temp_min'],
            'temp_max': dia['temp_max'],
        })

    return {
        'barrio': fila['barrio'],
        'resumen': fila['resumen'],
        'nivel': fila['nivel'],
        # 0 normal, 1 atencion, 2 alerta, 3 emergencia: sirve para ordenar o comparar
        'nivel_numero': reglas.NIVELES.index(fila['nivel']),
        'fecha': str(fila['fecha']),
        'que_hacer': fila['que_hacer'],
        'motivos': fila['motivos'],
        'proximos_dias': dias,
        'avisos_oficiales': riesgo['scraping']['avisos'],
        'actualizado': riesgo['actualizado'],
    }


@app.get('/salud')
def salud():
    return {'estado': 'ok'}


@app.post('/usuarios', status_code=201)
def crear_usuario(entrada: UsuarioEntrada):
    try:
        clave = usuarios.registrar_usuario(entrada.nombre, entrada.email, entrada.barrio)
    except usuarios.UsuarioExistente as error:
        raise HTTPException(status_code=409, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    return {
        'nombre': entrada.nombre.strip(),
        'email': entrada.email.strip().lower(),
        'barrio': barrios.validar_barrio(entrada.barrio),
        'api_key': clave,
        'aviso': 'Guardá esta clave: la vas a necesitar para consultar la API.',
    }


@app.get('/mi-barrio')
def mi_barrio(usuario: dict = Depends(exigir_clave)):
    return respuesta_de_barrio(usuario['barrio'])


@app.get('/riesgo/{barrio}')
def riesgo_de_barrio(barrio: str, usuario: dict = Depends(exigir_clave)):
    nombre = barrios.validar_barrio(barrio)
    if nombre is None:
        raise HTTPException(status_code=404, detail=f'No existe el barrio "{barrio}"')

    return respuesta_de_barrio(nombre)
