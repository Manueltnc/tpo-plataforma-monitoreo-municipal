# API propia del proyecto, hecha con FastAPI (N15, N17).
#
#   GET  /salud            publica, para ver que el servidor esta vivo
#   POST /usuarios         registro de usuarios: devuelve su API key
#   GET  /riesgo           riesgo de los 48 barrios (necesita API key)
#   GET  /riesgo/{barrio}  riesgo de un barrio (necesita API key)
#
# La API key se manda en el header X-API-Key.
# Para levantarla sola:  python -m uvicorn monitoreo.apis.servidor:app

from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from monitoreo.apis import usuarios
from monitoreo.app import barrios, config, servicio

app = FastAPI(title='Monitoreo municipal CABA', version='2.0')

limitador = usuarios.LimitadorPedidos(config.LIMITE_PEDIDOS_POR_MINUTO)


class UsuarioEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=60)
    email: str = Field(min_length=5, max_length=120)


class UsuarioRespuesta(BaseModel):
    nombre: str
    email: str
    api_key: str
    aviso: str


def exigir_clave(x_api_key: Optional[str] = Header(default=None)):
    """Dependencia: corta el pedido si la API key falta, es invalida o se paso del limite."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail='Falta el header X-API-Key')

    usuario = usuarios.validar_clave(x_api_key)
    if usuario is None:
        raise HTTPException(status_code=401, detail='API key invalida')

    if not limitador.permitir(x_api_key):
        raise HTTPException(status_code=429, detail='Demasiados pedidos, espere un minuto')

    return usuario


def _barrio_a_dict(fila):
    return {
        'barrio': fila['barrio'],
        'nivel': fila['nivel'],
        'indice': fila['puntos'],
        'peligro': fila['peligro'],
        'factor_vulnerabilidad': fila['factor'],
        'motivos': fila['motivos'],
    }


@app.get('/salud')
def salud():
    return {'estado': 'ok'}


@app.post('/usuarios', status_code=201, response_model=UsuarioRespuesta)
def crear_usuario(entrada: UsuarioEntrada):
    try:
        clave = usuarios.registrar_usuario(entrada.nombre, entrada.email)
    except usuarios.UsuarioExistente as error:
        raise HTTPException(status_code=409, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    return UsuarioRespuesta(
        nombre=entrada.nombre.strip(),
        email=entrada.email.strip().lower(),
        api_key=clave,
        aviso='Guarde esta clave: no se vuelve a mostrar.',
    )


@app.get('/riesgo')
def riesgo(nivel_minimo: Optional[str] = None, usuario: dict = Depends(exigir_clave)):
    if nivel_minimo is not None and nivel_minimo not in servicio.ORDEN_NIVELES:
        raise HTTPException(
            status_code=422,
            detail=f'nivel_minimo debe ser uno de: {", ".join(servicio.ORDEN_NIVELES)}',
        )

    datos = servicio.riesgo_actual()
    filas = datos['resultados']

    if nivel_minimo is not None:
        corte = servicio.ORDEN_NIVELES.index(nivel_minimo)
        filas = [f for f in filas if servicio.ORDEN_NIVELES.index(f['nivel']) >= corte]

    filas = sorted(filas, key=lambda f: f['puntos'], reverse=True)

    return {
        'dia_evaluado': str(datos['dia']['fecha']),
        'lluvia_mm': round(datos['dia']['lluvia_mm'], 1),
        'viento_kmh': round(datos['dia']['viento_kmh'], 1),
        'cantidad': len(filas),
        'barrios': [_barrio_a_dict(f) for f in filas],
    }


@app.get('/riesgo/{barrio}')
def riesgo_de_barrio(barrio: str, usuario: dict = Depends(exigir_clave)):
    nombre = barrios.validar_barrio(barrio)
    if nombre is None:
        raise HTTPException(status_code=404, detail=f'No existe el barrio "{barrio}"')

    datos = servicio.riesgo_actual()
    fila = next(f for f in datos['resultados'] if f['barrio'] == nombre)

    respuesta = _barrio_a_dict(fila)
    respuesta['dia_evaluado'] = str(datos['dia']['fecha'])

    return respuesta
