# Demostracion del envio de correos (N24).
# Arma el correo del reporte con adjuntos, muestra como quedo y lo envia.
# Si no hay credenciales en el .env, lo guarda como borrador .eml en data/processed/correos.

from monitoreo.app import servicio
from monitoreo.email import alertas


def main():
    riesgo = servicio.riesgo_actual(usar_cache=False)
    adjuntos = alertas.adjuntos_del_reporte()
    msg = alertas.armar_correo_reporte(riesgo, adjuntos)

    print('CORREO ARMADO')
    print(f'  Asunto: {msg["Subject"]}')
    print(f'  De: {msg["From"]}')
    print(f'  Para: {msg["To"]}')
    print(f'  Cuerpo en HTML: {"si" if msg.get_body(("html",)) is not None else "no"}')
    print(f'  Adjuntos ({len(adjuntos)}):')
    for archivo in adjuntos:
        print(f'    - {archivo.name}')

    print()
    print('ENVIO')
    resultado = alertas.enviar(msg)
    print(f'  {resultado["estado"]}: {resultado["detalle"]}')


if __name__ == '__main__':
    main()
