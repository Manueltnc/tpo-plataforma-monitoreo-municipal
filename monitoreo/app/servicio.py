# Junta las tres partes: el pronostico (API), los avisos oficiales (scraping) y los
# criterios de riesgo (reglas). Lo usan main.py, la API propia y los correos, asi
# el calculo vive en un solo lugar.

import time
from datetime import datetime

from monitoreo.apis import clima
from monitoreo.app import barrios, config, reglas
from monitoreo.scraping import avisos

DIAS_SEMANA = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']

_cache = {'momento': 0, 'valor': None}


def fecha_legible(fecha):
    """2026-11-14 -> 'viernes 14/11'"""
    return f'{DIAS_SEMANA[fecha.weekday()]} {fecha.day:02d}/{fecha.month:02d}'


def riesgo_de_barrio(barrio, dias):
    """Evalua al barrio en cada dia del pronostico y se queda con el peor dia."""
    proximos_dias = []

    for dia in dias:
        resultado = reglas.evaluar_barrio(barrio, dia)

        proximos_dias.append({
            'fecha': dia['fecha'],
            'dia': fecha_legible(dia['fecha']),
            'nivel': resultado['nivel'],
            'causa': resultado['causa'],
            'motivos': resultado['motivos'],
            'lluvia_mm': round(dia['lluvia_mm'], 1),
            'viento_kmh': round(dia['viento_kmh']),
            'temp_min': round(dia['temp_min']),
            'temp_max': round(dia['temp_max']),
        })

    # el peor dia: el de nivel mas alto (si empatan, el primero)
    peor = proximos_dias[0]
    for dia in proximos_dias:
        if reglas.NIVELES.index(dia['nivel']) > reglas.NIVELES.index(peor['nivel']):
            peor = dia

    return {
        'barrio': barrio,
        'nivel': peor['nivel'],
        'resumen': armar_resumen(barrio, peor),
        'fecha': peor['fecha'],
        'que_hacer': reglas.RECOMENDACIONES[peor['nivel']],
        'motivos': peor['motivos'],
        'proximos_dias': proximos_dias,
    }


def armar_resumen(barrio, dia):
    """Una frase para una persona: 'Palermo: alerta por lluvia el viernes 14/11'"""
    if dia['nivel'] == 'normal':
        return f'{barrio}: sin riesgo por clima en los próximos días'

    nombre = reglas.NOMBRES_NIVEL[dia['nivel']].lower()
    return f'{barrio}: {nombre} por {dia["causa"]} el {dia["dia"]}'


def riesgo_actual(usar_cache=True):
    """Pide el pronostico, lee los avisos oficiales y evalua los 48 barrios.
    La API lo pide muchas veces, por eso se guarda unos minutos (cache)."""
    ahora = time.time()
    vigente = ahora - _cache['momento'] < config.SEGUNDOS_CACHE_RIESGO

    if usar_cache and _cache['valor'] is not None and vigente:
        return _cache['valor']

    dias = clima.obtener_pronostico()
    scraping = avisos.buscar_avisos()

    por_barrio = []
    for barrio in barrios.BARRIOS:
        por_barrio.append(riesgo_de_barrio(barrio, dias))

    valor = {
        'actualizado': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'dias': dias,
        'scraping': scraping,
        'barrios': por_barrio,
    }
    _cache['momento'] = ahora
    _cache['valor'] = valor

    return valor


def buscar_barrio(riesgo, barrio):
    """Del resultado de riesgo_actual(), devuelve el del barrio pedido (o None)."""
    for fila in riesgo['barrios']:
        if fila['barrio'] == barrio:
            return fila

    return None


def barrios_por_nivel(riesgo):
    """{'emergencia': [...], 'alerta': [...], 'atencion': [...], 'normal': [...]}"""
    grupos = {'emergencia': [], 'alerta': [], 'atencion': [], 'normal': []}

    for fila in riesgo['barrios']:
        grupos[fila['nivel']].append(fila['barrio'])

    return grupos
