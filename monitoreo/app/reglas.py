# Criterios de riesgo y clasificacion en niveles (N02, N03)
#
# El nivel de un barrio se decide en dos pasos:
#
#   Paso 1. El clima define el nivel.
#           La lluvia y el viento previstos se comparan contra tres umbrales cada uno
#           (atencion, alerta, emergencia). Se queda el peor de los dos.
#
#   Paso 2. El barrio puede subir un nivel.
#           Si el barrio esta entre los que mas reclamos tuvieron en 2023 por
#           sumideros, calles anegadas y arboles, se sube un nivel. Solo pasa si el
#           clima ya no es normal: sin lluvia ni viento fuerte no hay riesgo.

from monitoreo.app import barrios, config

# Los niveles, de menor a mayor. La posicion en la lista sirve para compararlos.
NIVELES = ['normal', 'atencion', 'alerta', 'emergencia']

# Como se muestra cada nivel a una persona
NOMBRES_NIVEL = {
    'normal': 'Normal',
    'atencion': 'Atención',
    'alerta': 'Alerta',
    'emergencia': 'Emergencia',
}

# Que se le recomienda al vecino en cada nivel
RECOMENDACIONES = {
    'normal': 'No hace falta hacer nada especial.',
    'atencion': 'Mantenete informado y tené cuidado al circular. Revisá que las rejillas '
                'y desagües de tu casa no estén tapados.',
    'alerta': 'Evitá salir si no es necesario. No dejes el auto en calles que se inundan '
              'y no te refugies debajo de árboles.',
    'emergencia': 'Quedate en un lugar seguro y seguí las indicaciones oficiales. '
                  'Ante una emergencia llamá al 103 (Defensa Civil de la Ciudad).',
}


def nivel_por_umbrales(valor, umbral_atencion, umbral_alerta, umbral_emergencia):
    """Compara un valor (mm o km/h) contra sus tres umbrales y devuelve el nivel."""
    if valor >= umbral_emergencia:
        return 'emergencia'
    elif valor >= umbral_alerta:
        return 'alerta'
    elif valor >= umbral_atencion:
        return 'atencion'
    else:
        return 'normal'


def el_peor(nivel_1, nivel_2):
    """Devuelve el mas grave de dos niveles."""
    if NIVELES.index(nivel_1) >= NIVELES.index(nivel_2):
        return nivel_1
    return nivel_2


def subir_un_nivel(nivel):
    """normal -> atencion -> alerta -> emergencia. Emergencia queda igual."""
    posicion = NIVELES.index(nivel)

    if posicion < len(NIVELES) - 1:
        return NIVELES[posicion + 1]
    return nivel


def nivel_del_clima(dia):
    """Paso 1: nivel de un dia segun la lluvia y el viento previstos."""
    nivel_lluvia = nivel_por_umbrales(
        dia['lluvia_mm'],
        config.LLUVIA_ATENCION, config.LLUVIA_ALERTA, config.LLUVIA_EMERGENCIA,
    )
    nivel_viento = nivel_por_umbrales(
        dia['viento_kmh'],
        config.VIENTO_ATENCION, config.VIENTO_ALERTA, config.VIENTO_EMERGENCIA,
    )

    # Cada motivo explica el valor y desde cuanto empieza ese nivel
    motivos = []
    causas = []

    if nivel_lluvia != 'normal':
        umbral = umbral_del_nivel(nivel_lluvia, 'lluvia')
        motivos.append(
            f'Se esperan {dia["lluvia_mm"]:.0f} mm de lluvia '
            f'({NOMBRES_NIVEL[nivel_lluvia].lower()} desde {umbral} mm).'
        )
        causas.append('lluvia')

    if nivel_viento != 'normal':
        umbral = umbral_del_nivel(nivel_viento, 'viento')
        motivos.append(
            f'Se espera viento de hasta {dia["viento_kmh"]:.0f} km/h '
            f'({NOMBRES_NIVEL[nivel_viento].lower()} desde {umbral} km/h).'
        )
        causas.append('viento')

    return {
        'nivel': el_peor(nivel_lluvia, nivel_viento),
        'motivos': motivos,
        'causa': ' y '.join(causas),     # 'lluvia', 'viento', 'lluvia y viento' o ''
    }


def umbral_del_nivel(nivel, fenomeno):
    """Umbral de config.py para un nivel y un fenomeno ('lluvia' o 'viento')."""
    umbrales = {
        'lluvia': {
            'atencion': config.LLUVIA_ATENCION,
            'alerta': config.LLUVIA_ALERTA,
            'emergencia': config.LLUVIA_EMERGENCIA,
        },
        'viento': {
            'atencion': config.VIENTO_ATENCION,
            'alerta': config.VIENTO_ALERTA,
            'emergencia': config.VIENTO_EMERGENCIA,
        },
    }

    return umbrales[fenomeno][nivel]


def evaluar_barrio(barrio, dia):
    """Paso 1 y paso 2 juntos: nivel de un barrio para un dia."""
    clima = nivel_del_clima(dia)
    nivel = clima['nivel']
    motivos = list(clima['motivos'])

    datos_barrio = barrios.reclamos_de_barrio(barrio)

    if nivel != 'normal' and nivel != 'emergencia' and datos_barrio['con_mas_reclamos']:
        nivel = subir_un_nivel(nivel)
        motivos.append(
            f'{barrio} está entre los {config.CANTIDAD_BARRIOS_CON_MAS_RECLAMOS} barrios '
            f'con más reclamos por sumideros y árboles en 2023 '
            f'({datos_barrio["reclamos"]} reclamos), por eso se sube un nivel.'
        )

    return {
        'nivel': nivel,
        'nivel_clima': clima['nivel'],
        'causa': clima['causa'],
        'motivos': motivos,
    }
