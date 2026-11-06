# Junta el clima y las reglas para obtener el riesgo de todos los barrios.
# Lo usan main.py y la API propia, asi el calculo vive en un solo lugar.

import time

from monitoreo.apis import clima
from monitoreo.app import barrios, config, reglas

ORDEN_NIVELES = ['normal', 'atencion', 'alerta', 'emergencia']

_cache = {'momento': 0, 'valor': None}


# de todos los dias del pronostico nos quedamos con el que mas llueve
def peor_dia(dias):
    peor = dias[0]

    for dia in dias:
        if dia['lluvia_mm'] > peor['lluvia_mm']:
            peor = dia

    return peor


def evaluar_barrios(dia):
    resultados = []

    for barrio in barrios.BARRIOS:
        riesgo = reglas.evaluar_riesgo(barrio, dia)

        resultados.append({
            'barrio': barrio,
            'puntos': riesgo['puntos'],
            'peligro': riesgo['peligro'],
            'factor': riesgo['factor'],
            'motivos': riesgo['motivos'],
            'nivel': reglas.clasificar(riesgo['puntos']),
        })

    return resultados


def contar_niveles(resultados):
    conteo = {'emergencia': 0, 'alerta': 0, 'atencion': 0, 'normal': 0}

    for fila in resultados:
        conteo[fila['nivel']] = conteo[fila['nivel']] + 1

    return conteo


def riesgo_actual(usar_cache=True):
    """Pide el pronostico, evalua los 48 barrios y devuelve todo junto."""
    ahora = time.time()
    vigente = ahora - _cache['momento'] < config.SEGUNDOS_CACHE_RIESGO

    if usar_cache and _cache['valor'] is not None and vigente:
        return _cache['valor']

    dias = clima.obtener_pronostico()
    dia = peor_dia(dias)
    resultados = evaluar_barrios(dia)

    valor = {
        'dias': dias,
        'dia': dia,
        'resultados': resultados,
        'conteo': contar_niveles(resultados),
    }
    _cache['momento'] = ahora
    _cache['valor'] = valor

    return valor
