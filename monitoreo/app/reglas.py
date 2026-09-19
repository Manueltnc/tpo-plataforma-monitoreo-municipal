# Las reglas de alertas

from monitoreo.app import barrios, config

# Funcionar para sumar los puntos para alertas
def sumar_reglas(resultados):
    puntos = 0
    motivos = []

    for puntos_regla, motivo in resultados:
        if puntos_regla > 0:
            puntos = puntos + puntos_regla
            motivos.append(motivo)

    return {'puntos': puntos, 'motivos': motivos}


# -- Reglas por clima --

def regla_lluvia(milimetros):
    if milimetros >= config.LLUVIA_EMERGENCIA:
        return config.PUNTOS_LLUVIA_EMERGENCIA, f'Lluvia muy alta: {milimetros:.0f} mm'
    elif milimetros >= config.LLUVIA_ALERTA:
        return config.PUNTOS_LLUVIA_ALERTA, f'Lluvia alta: {milimetros:.0f} mm'
    elif milimetros >= config.LLUVIA_ATENCION:
        return config.PUNTOS_LLUVIA_ATENCION, f'Lluvia moderada: {milimetros:.0f} mm'
    else:
        return 0, ''


def regla_viento(kmh):
    if kmh >= config.VIENTO_ALERTA:
        return config.PUNTOS_VIENTO_ALERTA, f'Viento fuerte: {kmh:.0f} km/h'
    elif kmh >= config.VIENTO_ATENCION:
        return config.PUNTOS_VIENTO_ATENCION, f'Viento moderado: {kmh:.0f} km/h'
    else:
        return 0, ''

def regla_temperatura(dia):
    if dia['temp_max'] >= config.TEMPERATURA_ALTA:
        return config.PUNTOS_TEMPERATURA_ALTA, f'Calor extremo: {dia["temp_max"]:.0f} grados'
    else:
        return 0, ''

def regla_criticidad(barrio, milimetros):
    criticidad = barrios.criticidad_de_barrio(barrio)

    if criticidad >= 4 and milimetros >= config.LLUVIA_ATENCION:
        return config.PUNTOS_CRITICIDAD_ALTA, f'Cuenca critica (nivel {criticidad}) con lluvia'
    else:
        return 0, ''

def regla_reclamos(barrio):
    cantidad = barrios.reclamos_de_barrio(barrio)

    if cantidad >= config.RECLAMOS_MUCHOS:
        return config.PUNTOS_MUCHOS_RECLAMOS, f'{cantidad} reclamos en el ultimo mes'
    else:
        return 0, ''

def evaluar_riesgo(barrio, dia):
    return sumar_reglas([
        regla_lluvia(dia['lluvia_mm']),
        regla_viento(dia['viento_kmh']),
        regla_temperatura(dia),
        regla_criticidad(barrio, dia['lluvia_mm']),
        regla_reclamos(barrio),
    ])


# Mensaje de clasificacion
def clasificar(puntos):
    if puntos >= config.CORTE_EMERGENCIA:
        return 'emergencia'
    elif puntos >= config.CORTE_ALERTA:
        return 'alerta'
    elif puntos >= config.CORTE_ATENCION:
        return 'atencion'
    else:
        return 'normal'

# Mensaje de soporte
def que_hacer(nivel):
    acciones = {
        'normal': 'Todo normal',
        'atencion': 'Tener precaución',
        'alerta': 'Estén alerta y evite salir',
        'emergencia': 'Eviten salir, es un evento de emergencia',
    }

    return acciones[nivel]
