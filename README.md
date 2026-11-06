# Plataforma de monitoreo municipal de CABA

TPO de Taller de Programacion II (UADE). Solicitud 1: monitoreo municipal de clima,
alertas urbanas y servicios publicos.

El programa trae el pronostico del clima de una API publica, scrapea los avisos de un
sitio oficial, calcula un indice de riesgo para cada uno de los 48 barrios de CABA usando
los reclamos reales del SUACI 2023, y junta todo en un reporte.

Necesidades cubiertas: N01 a N25 (primera entrega corregida, ETL con Pandas y correos).

## Como correrlo

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copiar `.env.example` a `.env` y completar la clave de OpenWeather
(https://openweathermap.org/api). **Sin clave el programa igual funciona**: usa un
pronostico guardado en `data/fixtures` y lo avisa por pantalla. Los valores de relleno
de `.env.example` (los que empiezan con `tu_`) se ignoran, como si no estuvieran.

| Archivo | Que hace |
|---|---|
| `ejecutar_etl.py` | ETL sobre el SUACI 2023: deja tablas, Excel, JSON y graficos en `data/processed` |
| `main.py` | Avisos + pronostico + riesgo por barrio + **reporte integrado** |
| `demo_api.py` | Levanta la API propia y la consulta (registro, API key, errores) |
| `demo_correo.py` | Arma el correo del reporte con adjuntos y lo envia (o lo guarda como borrador) |
| `python -m tests.test_entrega2` | Pruebas |

El SUACI completo (`sistema-unico-de-atencion-ciudadana-2023.csv`, ~190 MB) va en
`data/raw/` y no se sube al repositorio. Puede estar como `.csv` o `.zip`. Si no esta,
el ETL usa una muestra de 5.000 filas (`data/fixtures/suaci_2023_muestra.zip`).
Los resultados ya generados con el archivo completo estan en `data/processed`.

Para ver alertas sin depender del clima real, poner en `.env`:
`PRONOSTICO_FIXTURE=forecast_tormenta.json`.

## Estructura

```
main.py, ejecutar_etl.py, demo_api.py, demo_correo.py
monitoreo/
    app/        config.py, barrios.py, reglas.py (el indicador), servicio.py
    apis/       clima.py (OpenWeather), servidor.py (API propia), cliente.py, usuarios.py
    scraping/   avisos.py
    etl/        extraer.py, transformar.py, cargar.py, pipeline.py
    reportes/   graficos.py, reporte.py
    email/      alertas.py (armado y envio de correos)
tests/
data/fixtures/  muestras chicas   data/raw/  datos crudos   data/processed/  resultados
```

## El indicador de riesgo (N02, N03)

Hay un solo indicador, el **IRU (Indice de Riesgo Urbano por clima)**, de 0 a 100:

```
IRU = peligro meteorologico  x  factor de vulnerabilidad del barrio
```

**Peligro (0 a 100).** Se calcula por separado para la lluvia (mm por dia) y el viento
(km/h) con una interpolacion por tramos pensada para que los umbrales coincidan con los
cortes del indice: al llegar al umbral de atencion se tienen 20 puntos, al de alerta 45 y
al de emergencia 70. Se toma el **mayor** de los dos, porque un solo fenomeno alcanza para
causar dano. Si lluvia y viento llegan juntos al nivel de atencion se suman 10 puntos,
porque esa combinacion es la que mas arboles tira.

**Vulnerabilidad (0.75 a 1.25).** Mide que tan seguido falla la infraestructura en cada
barrio. Sale de los reclamos reales del SUACI 2023 sobre sumideros, calles anegadas, poda y
extraccion de arboles. Los 48 barrios se ordenan por cantidad de reclamos y el factor sube
de forma proporcional. Solo amplifica o atenua: sin peligro, el indice es 0.

**Cortes:** menos de 20 normal, 20 a 44 atencion, 45 a 69 alerta, 70 o mas emergencia.

### De donde sale cada dato

| Dato | Fuente | Estado |
|---|---|---|
| Lluvia y viento previstos | API OpenWeather (pronostico a 5 dias) | real |
| Reclamos por barrio | SUACI 2023, portal de datos abiertos de la Ciudad | real |
| Umbrales de lluvia y viento | Valores de referencia tomados de los rangos que el SMN publica en sus avisos de tormenta (amarillo entre 20 y 70 mm, naranja entre 60 y 100 mm). La tabla oficial por region esta en la Nota Tecnica SMN 2021-109 y en "Umbrales para los alertas al publico" (repositorio.smn.gob.ar) | **aproximados: falta contrastarlos con la tabla de CABA** |
| Cortes del indice y rango del factor | criterio propio del grupo | a justificar |

### Respaldo de los niveles y umbrales

- **Niveles.** El indicador usa cuatro niveles (normal, atencion, alerta, emergencia) que
  equivalen al semaforo del SMN: verde, amarillo (*Informate*), naranja (*Preparate*) y rojo
  (*Segui instrucciones oficiales*). Pagina de alertas del SMN: https://www.smn.gob.ar/alertas_area.
  Explicacion de los colores: https://www.infobae.com/salud/ciencia/2025/02/11/que-significan-las-alertas-roja-naranja-y-amarilla-por-tormentas-del-servicio-meteorologico-nacional/
- **Metodologia.** El SMN define sus umbrales de lluvia a partir de percentiles (90, 95 y 99)
  de la lluvia diaria historica de sus estaciones, uno por cada nivel amarillo, naranja y rojo.
  Los niveles amarillo y naranja se miden en hasta 12 horas y el rojo en 24 horas
  (Nota Tecnica SMN 2021-109, repositorio.smn.gob.ar). Este proyecto no tiene la serie
  historica de lluvia, por eso usa umbrales fijos y configurables.
- **Valores de referencia.** Avisos del SMN reproducidos en medios:
  amarillo con 20 a 40 mm o 40 a 70 mm y naranja con 60 a 100 mm
  (https://ellitoral.com/informacion-general/vivo-ahora-hoy-tormenta-santafe-avanza-22-octubre-servicio-meteorologico-nacional-alerta-naranja_0_p8BXXlCzcJ.html,
  region de Santa Fe). Para CABA, un aviso amarillo prevea rafagas de 50 a 70 km/h
  (https://diariodecuyo.com.ar/noticias/alerta-meteorologica-nivel-naranja-por-severas-tormentas-y-actividad-electrica-en-buenos-aires-1588530.html).
- **Decision propia.** Los cortes del indice se fijaron para que la alerta salte **antes** que
  la del SMN (por ejemplo, atencion desde 20 mm), porque defensa civil necesita anticipacion.

### Decisiones de diseno

- **Por que esos reclamos:** los sumideros fallan con lluvia fuerte y los arboles ceden con
  viento. No se cuentan los reclamos de higiene, veredas o transito porque no dependen del
  clima. Los patrones estan en `config.PATRONES_RECLAMOS_CLIMA`.
- **Por que no se usa la temperatura:** el calor extremo es un riesgo sanitario, no de
  infraestructura urbana, y se mide con otro sistema del SMN (olas de calor).
- **Por que un factor y no sumar puntos:** el reclamo historico no es un peligro por si
  mismo; dice cuanto sufre cada barrio ante el mismo temporal.
- **Se reemplazo** la tabla de "criticidad por cuenca", que no tenia fuente citada, y los
  reclamos de ejemplo escritos a mano.

### Limitaciones

- Los reclamos no estan normalizados por poblacion, superficie ni cantidad de arboles: los
  barrios grandes tienden a tener mas. Tampoco se sabe que reclamo fue causado por una
  tormenta concreta.
- El SUACI es de 2023; para uso real habria que actualizarlo todos los meses.
- Cerca del 5% de los reclamos no trae barrio y se descarta.
- **Umbrales:** son parametros de `config.py`, no verdades fijas. El SMN define sus umbrales
  por region y en periodos de 12 o 24 horas; aca se usa un acumulado diario como aproximacion.
- **Viento:** el SMN mide **rafagas**, pero el pronostico de OpenWeather entrega la
  **velocidad media**. Por eso los umbrales de viento del indicador (40, 59 y 80 km/h) son mas
  bajos que los de rafagas del SMN y no se pueden comparar de forma directa.

## API publica y API privada (N13)

| | OpenWeather | API propia del proyecto |
|---|---|---|
| Tipo | publica | privada |
| Documentacion | abierta | interna |
| Quien la llama | cualquiera con una clave gratis | usuarios registrados en el sistema |
| Para que sirve la clave | contar llamadas | dar o negar acceso |
| Metodos usados | GET | GET y POST |

## JSON (N14)

La respuesta de OpenWeather llega en JSON y se lee con `respuesta.json()`
(`monitoreo/apis/clima.py`). Trae una lista de bloques de 3 horas con `main.temp`,
`wind.speed` (en m/s) y `rain.3h` (que no aparece cuando no llueve). Antes de usarla,
`validar_respuesta` comprueba que tenga la forma esperada. No se trabaja con XML.

## API propia (N15, N16, N17)

Hecha con FastAPI (`monitoreo/apis/servidor.py`) y consultada con `requests`
(`monitoreo/apis/cliente.py`).

| Metodo y ruta | Que hace |
|---|---|
| `GET /salud` | publica, para ver si el servidor esta vivo |
| `POST /usuarios` | registro de usuarios. Devuelve la **API key** (se muestra una sola vez) |
| `GET /riesgo?nivel_minimo=alerta` | riesgo de los barrios, filtrable. Necesita API key |
| `GET /riesgo/{barrio}` | riesgo de un barrio. Necesita API key |

- **Autenticacion (N17):** la clave viaja en el header `X-API-Key`. En la base SQLite
  (`data/usuarios.db`) solo se guarda su hash. La clave de OpenWeather vive en `.env`.
- **Errores:** 401 (falta o es invalida la clave), 404 (barrio inexistente), 409 (email
  ya registrado), 422 (datos invalidos) y 429 (mas de 30 pedidos por minuto).
- **requests (N16):** el cliente usa POST con JSON, GET con parametros y headers, timeout
  y manejo de status codes y de errores de conexion.

Para levantar el servidor solo: `python -m uvicorn monitoreo.apis.servidor:app`
(documentacion automatica en http://127.0.0.1:8000/docs).

## ETL con Pandas (N19 a N23)

`ejecutar_etl.py` corre el proceso completo (`monitoreo/etl/`):

- **Extraer:** SUACI desde CSV o ZIP (`read_csv` con `usecols`, `concat` si hay varios
  archivos), pronostico desde la API y avisos desde el scraping, todo a DataFrames.
- **Transformar:** descarte de nulos (`dropna`, `fillna`), normalizacion de barrios
  (`map` y alias para `Boca`, `Paternal` y `Villa Gral. Mitre`), fechas con `to_datetime`,
  cambios de tipo (`astype`), filtros con `query`, agrupaciones (`groupby`, `agg`,
  `transform`, `pivot_table`), serie semanal con `rolling` y `shift`, y combinaciones con
  `merge` (contra la lista de 48 barrios) y `join` (comparacion entre semestres).
- **Cargar:** CSV, Excel (`resumen_etl.xlsx`, una hoja por tabla) y JSON en
  `data/processed`. Se vuelven a leer desde los tres formatos como control.
- **Graficos (N23):** con `DataFrame.plot()`, en `data/processed/graficos`: evolucion
  semanal, ranking de barrios, histograma y comparacion de semestres.

## Reporte integrado

`main.py` arma un unico reporte (`data/processed/reportes/reporte_FECHA.md`) con el
resumen por nivel, el pronostico de la API, los avisos del scraping, el ranking del
indicador y el contexto historico del ETL.

## Correo (N24 y N25)

### Como funciona el envio (N24)

El modulo `monitoreo/email/alertas.py` usa `smtplib` y `EmailMessage`. Despues de armar el
reporte, `main.py` manda dos tipos de correo:

- **Reporte diario:** cuerpo en texto y en HTML con el resumen por nivel y los 10 barrios de
  mayor indice, mas **adjuntos**: el reporte, los 4 graficos y el Excel del ETL.
- **Alerta:** si algun barrio llega al nivel `NIVEL_MINIMO_ALERTA` (por defecto, alerta o
  emergencia), un correo aparte con el mensaje de cada barrio y la accion recomendada.
  Es el correo que pide el criterio de aceptacion de la consigna.

El envio se hace por SSL (puerto 465) con `SMTP_SSL`. Si se cambia `SMTP_PORT` a 587 se usa
una conexion normal cifrada con `starttls()`. Los pasos son los de la clase 12: armar el
mensaje, conectarse, autenticarse con `login()` y enviar con `send_message()`.

**Si algo falla, el mensaje no se pierde.** Cada envio devuelve un estado:

| Estado | Cuando pasa |
|---|---|
| `enviado` | el servidor lo acepto |
| `borrador` | faltan `EMAIL_USER`, `EMAIL_PASSWORD` o destinatarios reales: se guarda un `.eml` en `data/processed/correos` y se avisa por pantalla |
| `error` | el servidor rechazo la clave o no hubo conexion: tambien se guarda el `.eml` |

Un `.eml` se puede abrir con el cliente de correo (por ejemplo Outlook) para ver como quedo.

### Configuracion

Todo va en el `.env`, nunca en el codigo (ver `.env.example`):

```
EMAIL_USER=tu_correo@gmail.com
EMAIL_PASSWORD=la_contrasena_de_aplicacion
EMAIL_RECEIVER=destinatario1@dominio.com,destinatario2@dominio.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
```

`demo_correo.py` arma el correo, muestra asunto, destinatarios y adjuntos, y lo envia.
Los destinatarios `@ejemplo.com` se consideran de relleno y nunca se envian.

### Servicio de correo, protocolos y Gmail (N25)

- **Recorrido de un correo:** el cliente (el programa que envia o lee) entrega el mensaje al
  servidor de envio, este lo reenvia al servidor del destinatario y alli queda guardado en
  el buzon hasta que el destinatario lo lee.
- **SMTP** (*Simple Mail Transfer Protocol*, RFC 5321) sirve para **enviar** y transferir
  correos entre servidores. Es el unico protocolo que usa este proyecto.
- **POP3** sirve para **descargar** los mensajes del buzon al dispositivo local, y
  normalmente los borra del servidor. No maneja carpetas ni estados.
- **IMAP** sirve para **leer y gestionar** el buzon en el servidor: los mensajes quedan
  ahi y se sincronizan entre dispositivos, con carpetas, marcas y busquedas. Seria el
  protocolo para leer respuestas desde Python con `imaplib`; el proyecto solo envia.
- **Servidor usado:** `smtp.gmail.com`, puerto 465 (SSL).
- **Condiciones para usar Gmail desde Python:** Google ya no acepta la contrasena normal
  de la cuenta en un programa. Hay dos caminos:
  1. **Contrasena de aplicacion (la que usamos):** hay que activar la verificacion en dos
     pasos y generar una clave de 16 caracteres en *Cuenta de Google > Seguridad >
     Contrasenas de aplicaciones* (https://myaccount.google.com/apppasswords). Esa clave va
     en `EMAIL_PASSWORD`.
  2. **OAuth 2.0:** el programa recibe un token autorizado por el usuario en vez de una
     clave. Es mas seguro y es lo que se usaria en un sistema real, pero no esta
     implementado en este TPO.

El archivo `.gitignore` excluye el `.env`, asi que la clave no viaja al repositorio.

## El scraping

El sitio es https://www.argentina.gob.ar/noticias. El de https://www.smn.gob.ar/alertas
seria mas adecuado pero requiere JavaScript, que BeautifulSoup no ejecuta. El scraping
viene activado y se apaga con `SCRAPING_ACTIVO = False` en `monitoreo/app/config.py`.

## Pendientes

- Contrastar los umbrales de lluvia y viento con la tabla oficial del SMN para CABA y citarla.
