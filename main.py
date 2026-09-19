# Plataforma de monitoreo municipal de CABA
# Trae el clima, scrapea los avisos oficiales y calcula el riesgo por barrio.
# Se corre desde la carpeta del proyecto con: python main.py

from monitoreo.apis import clima
from monitoreo.app import barrios, config, reglas
from monitoreo.scraping import avisos


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
            'motivos': riesgo['motivos'],
            'nivel': reglas.clasificar(riesgo['puntos']),
        })

    return resultados


def contar_niveles(resultados):
    conteo = {'emergencia': 0, 'alerta': 0, 'atencion': 0, 'normal': 0}

    for fila in resultados:
        conteo[fila['nivel']] = conteo[fila['nivel']] + 1

    return conteo


def main():
    print('PLATAFORMA DE MONITOREO MUNICIPAL - CABA')
    print()

    # 1. Avisos del sitio oficial
    print('AVISOS OFICIALES')
    html = avisos.bajar_html(config.URLS_OFICIALES[0])
    todos, importantes = avisos.obtener_avisos(html)
    print(f'  Noticias encontradas: {len(todos)}')
    print(f'  Importantes para el sistema: {len(importantes)}')

    for aviso in importantes:
        print(f'  - {aviso["fecha"]}: {aviso["titulo"]}')
    print()

    print('BUSQUEDAS CON find_all')
    avisos.mostrar_busquedas(html)
    print()

    # 2. Pronostico del clima
    print('PRONOSTICO')
    dias = clima.obtener_pronostico()

    for dia in dias:
        print(f'  {dia["fecha"]}: {dia["lluvia_mm"]:.1f} mm, '
              f'viento {dia["viento_kmh"]:.0f} km/h, '
              f'de {dia["temp_min"]:.1f} a {dia["temp_max"]:.1f} grados')
    print()

    # 3. Riesgo por barrio
    dia = peor_dia(dias)
    print(f'RIESGO POR BARRIO (dia evaluado: {dia["fecha"]})')

    resultados = evaluar_barrios(dia)
    conteo = contar_niveles(resultados)

    for nivel in ['emergencia', 'alerta', 'atencion', 'normal']:
        print(f'  {nivel}: {conteo[nivel]} barrios')
    print()

    # 4. Alertas de los barrios que no estan en normal
    print('ALERTAS')
    hay_alertas = False

    for fila in resultados:
        if fila['nivel'] != 'normal':
            print(barrios.armar_mensaje(
                fila['barrio'],
                'riesgo urbano',
                fila['nivel'],
                fila['puntos'],
                fila['motivos'],
            ))
            print(f'  {reglas.que_hacer(fila["nivel"])}')
            print()
            hay_alertas = True

    if not hay_alertas:
        print('  Ningun barrio supera el umbral de atencion.')


if __name__ == '__main__':
    main()
