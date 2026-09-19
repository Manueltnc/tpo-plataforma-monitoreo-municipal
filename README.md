# Plataforma de monitoreo municipal de CABA

TPO de Taller de Programacion II (UADE).

El programa trae el pronostico del clima de una API publica, scrapea los
avisos publicados en un sitio oficial y calcula un puntaje de riesgo para
cada uno de los 48 barrios de CABA. Despues clasifica cada barrio en uno de
cuatro niveles (normal, atencion, alerta, emergencia) y muestra por consola
las alertas que habria que emitir.

Esta primera entrega cubre las necesidades N01 a N13.

## Como correrlo

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Despues hay que copiar `.env.example` a `.env` y completar la clave de
OpenWeather:

```
OPENWEATHER_API_KEY=tu_clave_aca
```
La API Key se extrae de https://openweathermap.org/api

Para correr el programa:

```
python main.py
```

## Estructura

```
main.py                     programa principal
monitoreo/
    app/
        config.py           umbrales, puntajes, URLs y palabras clave
        barrios.py          los 48 barrios, criticidad, reclamos y limpieza de texto
        reglas.py           las reglas de riesgo y la clasificacion
    apis/
        clima.py            consumo de la API de OpenWeather
    scraping/
        avisos.py           scraping del sitio oficial
    etl/                    segunda entrega
    reportes/               segunda entrega
    email/                  segunda entrega
tests/
data/fixtures/              una respuesta de la API guardada como muestra
```

## API publica y API privada (N13)

El proyecto usa las dos. La diferencia no esta en si piden clave o no, sino
en para quien fueron publicadas.

**OpenWeather es publica.** Tiene documentacion abierta, cualquiera se
registra y saca una clave gratis, y esta pensada para que la usen personas
que el proveedor no conoce. La clave sirve para contar cuantas llamadas hace
cada uno, no para decidir quien entra.

**El webhook interno del municipio seria privada.** No tiene documentacion
publica, nadie de afuera sabe que existe y solo la llama este sistema. Ahi la
credencial si decide si el que llama tiene permiso. Queda para la segunda
entrega.

| | OpenWeather | Webhook del municipio |
|---|---|---|
| Documentacion | publica | interna |
| Quien la puede llamar | cualquiera con una clave | solo este sistema |
| Para que sirve la credencial | contar llamadas | dar o negar permiso |
| Metodo | GET | POST |

## El scraping

El sitio que se scrapea es https://www.argentina.gob.ar/noticias.

Idealmente hubieramos scrapeado https://www.smn.gob.ar/alertas pero esa pagina requiere ejecutar
JavaScript y BeautifulSoup no lo hace.

El scraping viene **activado** por defecto. La consigna pide que se pueda
desactivar por configuracion, asi que en `monitoreo/app/config.py` esta la
constante:

```python
SCRAPING_ACTIVO = True
```

## Como se calcula el riesgo

| Puntos | Nivel |
|---|---|
| 70 o mas | emergencia |
| 45 a 69 | alerta |
| 20 a 44 | atencion |
| menos de 20 | normal |

Un ejemplo de la salida:

```
[EMERGENCIA] Villa Crespo - riesgo urbano
Puntaje de riesgo: 105
Motivos:
  - Lluvia muy alta: 85 mm
  - Viento fuerte: 70 km/h
  - Cuenca critica (nivel 5) con lluvia
  - 87 reclamos en el ultimo mes
```
Todos los umbrales y puntajes estan en `config.py`. Para cambiar cuando salta
una alerta se toca ese archivo y nada mas.

## Datos que todavia son de ejemplo

- Los umbrales de lluvia y viento son provisorios. Falta confirmarlos
  contra el Sistema de Alerta Temprana del SMN y citar la fuente.
- El diccionario `RECLAMOS` de `barrios.py` tiene valores de ejemplo. En la
  segunda entrega salen del CSV de SUACI 2023 leido con Pandas.
