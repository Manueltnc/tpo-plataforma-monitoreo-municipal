# Indicador de riesgo urbano y su clasificacion (N02, N03)
#
# DISENO (un solo indicador, el IRU = Indice de Riesgo Urbano por clima):
#
#   IRU = peligro_meteorologico x factor_de_vulnerabilidad_del_barrio
#
# 1. PELIGRO (0 a 100): que tan fuerte es el fenomeno que viene.
#    Se calcula para la lluvia (mm por dia) y para el viento (km/h) y se toma
#    el MAYOR de los dos, porque con uno solo ya alcanza para hacer dano.
#    Si ademas se dan los dos juntos (tormenta con viento) se suman puntos
#    extra: es cuando mas se caen los arboles.
# 2. VULNERABILIDAD (0.75 a 1.25): que tan seguido falla la infraestructura en
#    ese barrio. Sale de los reclamos reales del SUACI 2023 por sumideros,
#    calles anegadas, poda y extraccion de arboles. Los barrios se ordenan de
#    menos a mas reclamos y el factor sube en forma proporcional.
#
# La vulnerabilidad solo amplifica o atenua: si no hay peligro, el IRU es 0.

from monitoreo.app import barrios, config


def puntaje_amenaza(valor, u_atencion, u_alerta, u_emergencia):
    """Convierte una medida (mm o km/h) en puntos de 0 a 100.

    Es una interpolacion por tramos que hace coincidir los umbrales con los
    cortes del indice: al llegar al umbral de atencion se tienen justo
    CORTE_ATENCION puntos, al de alerta CORTE_ALERTA, y asi.
    """
    if valor <= 0:
        return 0.0

    tramos = [
        (0, 0),
        (u_atencion, config.CORTE_ATENCION),
        (u_alerta, config.CORTE_ALERTA),
        (u_emergencia, config.CORTE_EMERGENCIA),
        (u_emergencia * 2, 100),
    ]

    if valor >= tramos[-1][0]:
        return 100.0

    for i in range(1, len(tramos)):
        x0, y0 = tramos[i - 1]
        x1, y1 = tramos[i]

        if valor <= x1:
            return y0 + (y1 - y0) * (valor - x0) / (x1 - x0)

    return 100.0


def peligro_meteorologico(dia):
    p_lluvia = puntaje_amenaza(
        dia['lluvia_mm'],
        config.LLUVIA_ATENCION, config.LLUVIA_ALERTA, config.LLUVIA_EMERGENCIA,
    )
    p_viento = puntaje_amenaza(
        dia['viento_kmh'],
        config.VIENTO_ATENCION, config.VIENTO_ALERTA, config.VIENTO_EMERGENCIA,
    )

    peligro = max(p_lluvia, p_viento)
    motivos = []

    if p_lluvia >= config.CORTE_ATENCION:
        motivos.append(f'Lluvia prevista: {dia["lluvia_mm"]:.0f} mm')

    if p_viento >= config.CORTE_ATENCION:
        motivos.append(f'Viento previsto: {dia["viento_kmh"]:.0f} km/h')

    if p_lluvia >= config.CORTE_ATENCION and p_viento >= config.CORTE_ATENCION:
        peligro = peligro + config.PUNTOS_COMPUESTO
        motivos.append('Lluvia y viento juntos: riesgo de arboles caidos')

    return {'peligro': min(peligro, 100), 'motivos': motivos}


def evaluar_riesgo(barrio, dia):
    clima = peligro_meteorologico(dia)
    vulnerabilidad = barrios.vulnerabilidad_de_barrio(barrio)
    factor = vulnerabilidad['factor']

    puntos = round(min(clima['peligro'] * factor, 100), 1)

    motivos = list(clima['motivos'])
    if clima['peligro'] > 0 and vulnerabilidad['reclamos'] > 0:
        motivos.append(
            f'Historial: {vulnerabilidad["reclamos"]} reclamos por sumideros y '
            f'arbolado en 2023 (factor {factor:.2f})'
        )

    return {
        'puntos': puntos,
        'peligro': round(clima['peligro'], 1),
        'factor': factor,
        'motivos': motivos,
    }


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
