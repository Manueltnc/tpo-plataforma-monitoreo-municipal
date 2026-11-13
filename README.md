# Plataforma de monitoreo municipal de CABA

TPO de Taller de Programacion II (UADE). Solicitud 1: monitoreo municipal de clima,
alertas urbanas y servicios publicos.

## Para quien es

Para el **vecino de un barrio de CABA**. El sistema le responde una pregunta:

> En los proximos dias, ¿hay riesgo por lluvia o viento en mi barrio? ¿Que tengo que hacer?
> ¿Hay algun aviso oficial sobre el clima?

El vecino se registra en nuestra API con su barrio. Con su clave puede consultar su barrio
cuando quiera, y si su barrio entra en riesgo le llega un correo.

Ademas, la guardia municipal recibe todos los dias un reporte con los 48 barrios.

## Como probarlo (sin claves)

No hace falta ninguna clave ni cuenta. Sin clave de OpenWeather se usa un pronostico
guardado, y sin cuenta de correo los mails se guardan como archivos `.eml` que se pueden
abrir con Outlook, Thunderbird o la app Correo de Windows.

**1. Instalar** (Windows. En Mac o Linux: `source .venv/bin/activate` y `cp`)

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

El `.env` que se copia ya viene listo para probar: usa un pronostico guardado con dias de
tormenta (`forecast_tormenta.json`) para que se vean alertas.

**2. Correr las pruebas**

```
python -m tests.test_plataforma
```

**3. Ver la API funcionando**

```
python demo_api.py
```

Levanta la API, registra una vecina de Palermo, consulta su barrio y muestra el JSON de
respuesta y los errores (sin clave, clave invalida, barrio que no existe, email repetido).

**4. Registrarse como vecino**

```
python -m uvicorn monitoreo.apis.servidor:app
```

Abrir http://127.0.0.1:8000/docs en el navegador. Ahi FastAPI arma una pagina para probar
la API:

- En `POST /usuarios` tocar *Try it out* y mandar, por ejemplo:
  `{"nombre": "Profe", "email": "profe@ejemplo.com", "barrio": "Palermo"}`.
  La respuesta trae la `api_key`.
- En `GET /mi-barrio` tocar *Try it out*, pegar la clave en `x-api-key` y ejecutar.

Cortar el servidor con `Ctrl+C`.

**5. Correr el programa del dia**

```
python main.py
```

Muestra el pronostico, los avisos oficiales y los barrios por nivel. Guarda el reporte en
`data/processed/reportes/`, el grafico en `data/processed/graficos/pronostico.png` y los
correos en `data/processed/correos/` (uno para la guardia y uno para cada vecino registrado
cuyo barrio esta en riesgo).

**Para recibir los correos de verdad:** completar `EMAIL_USER` y `EMAIL_PASSWORD` en el
`.env` con una cuenta de Gmail (ver "Gmail desde Python" mas abajo) y registrarse con un
correo real. Las direcciones `@ejemplo.com` nunca se envian.

**Para usar el clima real:** sacar una clave gratis en https://openweathermap.org/api y
ponerla en `OPENWEATHER_API_KEY`.

## Que hace cada archivo

| Comando | Que hace | Cuando |
|---|---|---|
| `python main.py` | pronostico + avisos + nivel de cada barrio + reporte + correos | una vez por dia |
| `python -m uvicorn monitoreo.apis.servidor:app` | levanta la API para los vecinos | siempre prendida |
| `python ejecutar_etl.py` | procesa el SUACI 2023 completo | una sola vez |
| `python demo_api.py` | muestra la API funcionando | para probar |
| `python -m tests.test_plataforma` | pruebas | para probar |

```
monitoreo/
    app/        config.py (criterios y rutas), reglas.py (niveles), barrios.py, servicio.py
    apis/       clima.py (OpenWeather), servidor.py (API propia), usuarios.py, cliente.py
    scraping/   avisos.py
    etl/        extraer.py, transformar.py, cargar.py, pipeline.py
    reportes/   reporte.py, graficos.py
    email/      alertas.py
tests/          test_plataforma.py
data/fixtures/  pronosticos guardados, pagina de noticias guardada, muestra del SUACI
data/processed/ resultados del ETL hechos con el SUACI completo
```

## De donde salen los datos

| Dato | Fuente | Como entra |
|---|---|---|
| Lluvia, viento y temperatura de los proximos 5 dias | OpenWeather, `/data/2.5/forecast` | API publica, en cada corrida |
| Reclamos por barrio | SUACI 2023 (Sistema Unico de Atencion Ciudadana), portal de datos abiertos de la Ciudad, data.buenosaires.gob.ar | ETL con pandas, una sola vez |
| Avisos oficiales sobre el clima | https://www.argentina.gob.ar/noticias | scraping, en cada corrida |

CABA tiene un solo pronostico para toda la ciudad. Lo que diferencia a un barrio de otro
son sus reclamos historicos.

## Como se decide el nivel (N02, N03)

Hay cuatro niveles: **normal, atencion, alerta y emergencia**. Son los mismos colores que
usa el SMN: verde, amarillo, naranja y rojo. El nivel se decide en dos pasos:

**Paso 1. El clima define el nivel.** Se compara la lluvia y el viento previstos para cada
dia con estos valores y se toma el peor de los dos:

| | Atencion | Alerta | Emergencia |
|---|---|---|---|
| Lluvia en el dia | 20 mm | 40 mm | 70 mm |
| Viento maximo | 40 km/h | 59 km/h | 80 km/h |

**Paso 2. El barrio puede subir un nivel.** Si el barrio esta entre los 16 barrios con mas
reclamos por sumideros, calles anegadas y arboles en 2023, sube un nivel. Son los barrios
donde los desagues y los arboles fallan mas seguido, asi que la misma lluvia les hace mas
dano. Si el clima es normal, no sube: sin lluvia ni viento fuerte no hay riesgo.

Ejemplo: se esperan 25 mm de lluvia. En Retiro (puesto 46 de 48 en reclamos) queda en
**atencion**. En Palermo (puesto 1, 2.419 reclamos) sube a **alerta**.

Para el vecino se muestra el peor dia de los proximos cinco. Si hay dos dias con el mismo
nivel, se muestra el primero, para avisar con tiempo.

### De donde sale cada valor

| Criterio | De donde sale |
|---|---|
| Lluvia: 20, 40 y 70 mm | El SMN publica avisos amarillos de 20 a 40 mm y de 40 a 70 mm, y naranjas de 60 a 100 mm ([ejemplo](https://ellitoral.com/informacion-general/vivo-ahora-hoy-tormenta-santafe-avanza-22-octubre-servicio-meteorologico-nacional-alerta-naranja_0_p8BXXlCzcJ.html)). Tomamos 20 y 40 como en sus avisos amarillos, y 70 (donde termina el amarillo) como emergencia, para avisar antes que el SMN. |
| Viento: 40, 59 y 80 km/h | Un aviso amarillo del SMN para CABA habla de rafagas de 50 a 70 km/h ([ejemplo](https://diariodecuyo.com.ar/noticias/alerta-meteorologica-nivel-naranja-por-severas-tormentas-y-actividad-electrica-en-buenos-aires-1588530.html)). OpenWeather da el viento promedio y no las rafagas, por eso usamos valores un poco mas bajos. |
| Los 4 niveles | Semaforo de alertas del SMN ([que significa cada color](https://www.infobae.com/salud/ciencia/2025/02/11/que-significan-las-alertas-roja-naranja-y-amarilla-por-tormentas-del-servicio-meteorologico-nacional/)). |
| 16 barrios con mas reclamos | Un tercio de los 48 barrios. Divide a los barrios en tres grupos parejos y sube solo al grupo de arriba. |
| Que reclamos cuentan | Sumideros, pluviales, calles anegadas, poda y extraccion de arboles: son los que dependen de la lluvia y el viento. No cuentan veredas, higiene o transito. |

Todos los valores estan en `monitoreo/app/config.py`. Si hay que cambiar un criterio, se
cambia ahi y no en el codigo.

La temperatura se muestra pero no cambia el nivel: el calor es un riesgo de salud y el SMN
lo maneja con otro sistema (olas de calor).

## Scraping (N08 a N12)

Leemos la pagina de noticias del gobierno nacional (https://www.argentina.gob.ar/noticias)
con `requests` y `BeautifulSoup`. De cada noticia sacamos el titulo, la fecha y el link. Nos
quedamos solo con las que tienen palabras del clima en el titulo (alerta, tormenta, lluvia,
temporal, viento, etc.). Esas aparecen como "avisos oficiales" en la API, en el reporte y en
el correo del vecino, con su link. **No cambian el nivel**: son informacion extra.

- Antes de leer la pagina se revisa su `robots.txt`, y se lee una sola vez por corrida.
- Se puede apagar con `SCRAPING_ACTIVO = False` en `config.py`.
- Elegimos esta pagina porque se arma en el servidor y BeautifulSoup la puede leer. La de
  alertas del SMN (smn.gob.ar/alertas) seria mejor, pero necesita JavaScript y devuelve 403.
- Muchos dias no hay ninguna noticia del clima. En ese caso se informa "no encontramos
  noticias oficiales sobre el clima".
- Dominio, IP, navegador y etiquetas de la pagina estan anotados al principio de
  `monitoreo/scraping/avisos.py`. Las seis busquedas con `find_all` (por etiqueta, clase,
  id, atributo, texto y lambda) estan en `mostrar_busquedas()` y se prueban con una copia
  guardada de la pagina.

## API propia (N13 a N17)

Hecha con FastAPI (`monitoreo/apis/servidor.py`). La clave va en el header `X-API-Key`.

| Metodo y ruta | Que hace | Pide clave |
|---|---|---|
| `GET /salud` | para ver si el servidor esta prendido | no |
| `POST /usuarios` | registro: nombre, email y barrio. Devuelve la API key | no |
| `GET /mi-barrio` | riesgo del barrio con el que se registro el vecino | si |
| `GET /riesgo/{barrio}` | riesgo de cualquier barrio | si |

Ejemplo de respuesta de `GET /mi-barrio` (recortada):

```json
{
  "barrio": "Palermo",
  "resumen": "Palermo: alerta por viento el domingo 13/09",
  "nivel": "alerta",
  "nivel_numero": 2,
  "fecha": "2026-09-13",
  "que_hacer": "Evitá salir si no es necesario. No dejes el auto en calles que se inundan y no te refugies debajo de árboles.",
  "motivos": [
    "Se espera viento de hasta 43 km/h (atención desde 40 km/h).",
    "Palermo está entre los 16 barrios con más reclamos por sumideros y árboles en 2023 (2419 reclamos), por eso se sube un nivel."
  ],
  "proximos_dias": [
    {"fecha": "2026-09-13", "dia": "domingo 13/09", "nivel": "alerta", "lluvia_mm": 5.5,
     "viento_max_kmh": 43, "temp_min": 6, "temp_max": 11}
  ],
  "avisos_oficiales": [],
  "actualizado": "13/11/2026 13:52"
}
```

`nivel_numero` (0 normal, 1 atencion, 2 alerta, 3 emergencia) es para que otro programa
pueda ordenar o comparar. Una persona lee `resumen`, `motivos` y `que_hacer`.

**Errores:** 401 (falta la clave o no existe), 404 (barrio que no existe), 409 (email ya
registrado), 422 (datos invalidos) y 429 (mas de 30 pedidos por minuto con la misma clave).

**Usuarios:** se guardan en `data/usuarios.csv` (nombre, email, barrio, api_key, fecha de
alta), que se lee y se escribe con pandas. Ese archivo no se sube al repositorio porque
tiene las claves.

**Otros metodos (N15):** no los implementamos, pero tendrian sentido `PATCH /usuarios` para
que un vecino cambie de barrio y `DELETE /usuarios` para darse de baja. `PUT` serviria para
reemplazar todos sus datos de una vez.

| | OpenWeather | Nuestra API |
|---|---|---|
| Tipo (N13) | publica | privada |
| Documentacion | abierta | interna (`/docs`) |
| Quien la usa | cualquiera con una clave gratis | vecinos registrados |
| Para que sirve la clave | contar las llamadas | dar o negar acceso |
| Metodos | GET | GET y POST |

**JSON (N14):** OpenWeather responde en JSON y se lee con `respuesta.json()`. Trae bloques
de 3 horas con `main.temp`, `wind.speed` (en m/s) y `rain.3h`, que no aparece cuando no
llueve (por eso se lee con `.get()`). `validar_respuesta()` revisa la forma antes de usarla.
No trabajamos con XML.

**requests (N16):** `monitoreo/apis/clima.py` hace GET con parametros, timeout y
`raise_for_status()`. `monitoreo/apis/cliente.py` consulta nuestra API con POST, headers y
manejo de status codes.

## Correos (N24, N25)

`monitoreo/email/alertas.py` usa `smtplib` y `EmailMessage`. Hay dos correos:

- **Al vecino**, cuando su barrio llega a atencion o mas. Asunto del tipo
  `ALERTA en Palermo: viento el domingo 13/09`. Dice el nivel, por que, que hacer, como vienen
  los proximos dias y los avisos oficiales. Va en texto y en HTML, con el grafico del
  pronostico adjunto.
- **A la guardia municipal** (`EMAIL_GUARDIA` en el `.env`), todos los dias: cuantos barrios
  hay en cada nivel, con el reporte completo y el grafico adjuntos.

Si faltan las credenciales, si el destinatario es `@ejemplo.com` o si el envio falla, el
correo se guarda como `.eml` en `data/processed/correos` y no se pierde.

El envio usa `SMTP_SSL` en el puerto 465. Con `SMTP_PORT=587` se usa una conexion normal
que se cifra con `starttls()`. Los pasos son los de la clase 12: armar el mensaje,
conectarse, `login()` y `send_message()`.

### Protocolos y Gmail desde Python

- **Recorrido de un correo:** el programa entrega el mensaje al servidor de envio, este lo
  pasa al servidor del destinatario y ahi queda en su buzon hasta que lo lee.
- **SMTP** sirve para **enviar** correos y pasarlos entre servidores. Es el unico que usamos.
- **POP3** sirve para **bajar** los mensajes del buzon a la computadora. Normalmente los borra
  del servidor y no maneja carpetas.
- **IMAP** sirve para **leer y ordenar** el buzon en el servidor. Los mensajes quedan ahi y se
  ven igual desde todos los dispositivos. Se usaria con `imaplib` para leer respuestas.
- **Servidor:** `smtp.gmail.com`.
- **Gmail desde Python:** Google no acepta la contraseña normal de la cuenta en un
  programa. Hay dos formas:
  1. **Contraseña de aplicacion (la que usamos):** activar la verificacion en dos pasos y
     generar una clave de 16 letras en https://myaccount.google.com/apppasswords. Esa clave
     va en `EMAIL_PASSWORD`. En cuentas de trabajo el administrador la puede tener bloqueada.
  2. **OAuth 2.0:** el programa usa un permiso (token) que da el usuario en vez de una clave.
     Es mas seguro, pero no lo implementamos.

## ETL con pandas (N19 a N23)

`python ejecutar_etl.py` procesa el SUACI 2023 completo (unos 190 MB, no esta en el repo).
Hay que bajarlo del portal de datos abiertos de la Ciudad y ponerlo en `data/raw/` como
`.csv` o `.zip`. Los resultados ya estan en `data/processed`, asi que no hace falta correrlo
para probar el programa. Las pruebas usan una muestra de 5.000 filas
(`data/fixtures/suaci_2023_muestra.zip`).

- **Extraer:** `read_csv` del CSV o del ZIP, solo con las columnas que usamos, y `concat`
  si hay varios archivos.
- **Transformar:** nulos (`dropna`, `fillna`), nombres de barrio normalizados con `map`,
  fechas con `to_datetime`, tipos con `astype`, filtros con `query`, conteo por barrio con
  `groupby` y `merge` contra la lista de 48 barrios, puesto de cada barrio con
  `sort_values`, serie semanal con `rolling` y `shift`, y primer contra segundo semestre
  con `join`.
- **Cargar:** `reclamos_por_barrio.csv` y `.json`, `reclamos_clima_semanal.csv`,
  `comparacion_semestres.csv` y `resumen_etl.xlsx` (una hoja por tabla). Se vuelven a leer
  desde CSV, JSON y Excel para comprobar que quedaron bien.
- **Graficos (N23):** dos, con `DataFrame.plot()`. La evolucion semanal de reclamos
  (`evolucion_semanal.png`) y el pronostico de los proximos dias contra los umbrales
  (`pronostico.png`, el que se adjunta en los correos).

## Limitaciones

- El pronostico es uno solo para toda la ciudad: puede llover fuerte en Liniers y no en
  Puerto Madero, pero el sistema ve el mismo clima en todos lados.
- Los reclamos no estan divididos por poblacion ni por superficie, y los barrios grandes
  tienden a tener mas. El SUACI es de 2023: para uso real habria que actualizarlo.
- El SMN define sus umbrales por region y en 12 o 24 horas. Nosotros usamos la lluvia
  total del dia y valores de referencia de sus avisos, no la tabla oficial de CABA.

## Mapa de la consigna

| Necesidad | Donde esta |
|---|---|
| N01 carpetas | `monitoreo/` con app, scraping, apis, etl, reportes, email y `tests/` |
| N02 operadores | aritmeticos en `clima.py` (suma de la lluvia del dia, m/s a km/h), relacionales y logicos en `reglas.py` (umbrales, paso 2) |
| N03 niveles y reglas configurables | `reglas.nivel_por_umbrales()` con if/elif, valores en `config.py` |
| N04 funciones | `barrios.validar_barrio()`, `normalizar()`, `clima.limpiar_bloques()`, `alertas.enviar()` |
| N05 listas | `BARRIOS`, `URLS_OFICIALES`, `PALABRAS_CLAVE`, `get_correos_guardia()` |
| N06 diccionarios | `ALIAS_BARRIOS`, `NOMBRES_NIVEL`, `RECOMENDACIONES`, umbrales en `reglas.umbral_del_nivel()` |
| N07 cadenas | `barrios.normalizar()`, `extraer_dominio()`, textos de los correos |
| N08 y N09 dominio, IP, etiquetas | encabezado de `scraping/avisos.py` |
| N10 a N12 scraping | `scraping/avisos.py` |
| N13 a N18 APIs | `apis/clima.py`, `apis/servidor.py`, `apis/cliente.py`, `apis/usuarios.py` |
| N19 a N23 ETL y graficos | `etl/`, `reportes/graficos.py` |
| N24 y N25 correo | `email/alertas.py` y la seccion de correos de este README |
