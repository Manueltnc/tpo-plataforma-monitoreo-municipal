# Consigna del TPO

Transcripcion de los documentos de catedra. Fuente de verdad para el alcance.
Este archivo SI va al entregable.

---

## Solicitud de proyecto 1. Plataforma de monitoreo municipal de clima, alertas urbanas y servicios publicos

**Tipo de entidad solicitante:** Municipalidad u organismo publico de defensa
civil y atencion ciudadana.

**Objetivo:** Integrar datos meteorologicos, avisos publicados en sitios
oficiales y reportes internos para generar tableros y alertas por correo sobre
riesgos urbanos.

**Equipo sugerido:** 6 estudiantes (lider tecnico, dev scraping/API, dev
ETL-Pandas, dev correo/reportes, tester/documentador, responsable de
integracion). Nota: este TPO se desarrolla en solitario.

**Duracion:** 4 meses, entregas parciales cada 2 semanas y demostracion final.

---

## Alcance funcional minimo solicitado

La columna "Entrega" marca el corte acordado: la primera entrega cubre hasta
Unidad 3 (APIs). Todo lo de Pandas, visualizacion y email queda para la segunda.

| # | Necesidad funcional | Conceptos | Unidad | Entrega |
|---|---|---|---|---|
| N01 | Configurar un proyecto Python modular con carpetas app, scraping, apis, etl, reportes, email y tests. | entorno, modulos | 1 | **1** |
| N02 | Calcular indicadores de riesgo urbano combinando lluvia, temperatura, viento, cantidad de reclamos y criticidad de barrios mediante operadores aritmeticos, relacionales y logicos. | operadores | 1 | **1** |
| N03 | Clasificar eventos en normal, atencion, alerta y emergencia usando estructuras de control y reglas configurables. | control | 1 | **1** |
| N04 | Crear funciones para validar barrios, limpiar descripciones de reclamos, consumir clima, transformar datos y enviar alertas. | funciones | 1 | **1** |
| N05 | Mantener listas de barrios, URL oficiales, palabras clave de emergencia, destinatarios de guardia y correos de areas operativas. | listas | 1 | **1** |
| N06 | Usar diccionarios para mapear barrios con responsables, estaciones meteorologicas, endpoints, API keys y umbrales por zona. | diccionarios | 1 | **1** |
| N07 | Procesar cadenas de caracteres para normalizar nombres de barrios, extraer dominios de URL publicas y construir mensajes institucionales. | cadenas | 1 | **1** |
| N08 | Registrar dominio, DNS, IP resuelta y navegador usado para revisar el sitio oficial de alertas y noticias municipales. | web, DNS, IP | 2 | **1** |
| N09 | Inspeccionar manualmente el codigo HTML del sitio, identificar etiquetas principales como html, head, body, div, table, tr, td, a, img, span y sus atributos. | HTML | 2 | **1** |
| N10 | Construir un modulo de web scraping con requests y BeautifulSoup que respete terminos de uso, robots.txt y limites de frecuencia. | scraping | 2 | **1** |
| N11 | Recuperar valores de elementos HTML encontrados: texto, href, src, class, id, data-* y atributos relevantes. | HTML atributos | 2 | **1** |
| N12 | Utilizar find_all con busqueda por etiqueta, clase, id, atributos, texto, funcion lambda y combinaciones de criterios. | find_all | 2 | **1** |
| N13 | Integrar al menos una API publica y distinguir en la documentacion una API publica frente a una privada o interna. | API | 3 | **1** |
| N14 | Consumir respuestas JSON y, cuando sea posible, XML, explicando diferencias de estructura y parseo. | JSON/XML | 3 | **1** |
| N15 | Usar metodos HTTP GET y POST como minimo, y documentar cuando serian necesarios PUT, PATCH y DELETE. | HTTP | 3 | **1** |
| N16 | Instalar, importar y usar requests para llamadas HTTP, gestionando status codes, headers, parametros, timeout y errores. | requests | 3 | **1** |
| N17 | Implementar autenticacion con API key o token en headers o parametros, evitando exponer credenciales en el codigo fuente. | auth | 3 | **1** |
| N18 | Ejecutar una practica de consumo de API publica, por ejemplo OpenWeatherMap u otra equivalente con clave de prueba. | API publica | 3 | **1** |
| N19 | Disenar un proceso ETL completo: extraccion web/API/archivo comprimido, transformacion con Pandas y carga en CSV, Excel o base local. | ETL | 4 | 2 |
| N20 | Crear DataFrames y Series, aplicar operaciones basicas, metodos principales, cambios de tipos, manejo de nulos y funciones por columna. | Pandas | 4 | 2 |
| N21 | Leer datos con Pandas desde CSV, Excel, JSON y archivos comprimidos, y exportar resultados limpios a CSV, Excel y JSON. | import/export | 4 | 2 |
| N22 | Realizar agregaciones, agrupaciones, manejo de fechas, merge, join, concat y comparacion temporal de datasets. | Pandas avanzado | 5 | 2 |
| N23 | Generar visualizaciones basicas con DataFrame.plot para tendencias, barras, histogramas o rankings. | visualizacion | 5 | 2 |
| N24 | Automatizar envio de emails con smtplib y EmailMessage, incluyendo asunto, cuerpo, destinatarios, adjuntos y conexion a SMTP. | email | 6 | 2 |
| N25 | Documentar protocolos SMTP, POP e IMAP, servidor de email utilizado y condiciones para acceso a Gmail desde Python mediante contrasena de aplicacion u OAuth. | SMTP POP IMAP | 6 | 2 |

---

## Criterios de aceptacion academica y tecnica

- La plataforma debe generar un reporte diario por barrio y un correo de alerta
  si algun indicador supera el umbral definido.
- El scraping debe limitarse a fuentes publicas permitidas y debe poder
  desactivarse por configuracion.
- El entregable debe incluir evidencia de consumo de API publica de clima,
  ETL en Pandas y grafico de evolucion semanal.

Los tres criterios se evaluan sobre el entregable final, no sobre la entrega 1.

---

## Programa de la materia (unidades)

**Unidad 1 - Conceptos fundamentales de Python.** Variables. Literales. Tipos de
datos. print() e input(). Operadores. Estructuras de control. Entorno de
desarrollo. Funciones. Modulos. Listas y sus operaciones, funciones y metodos.
Diccionarios. Cadenas de caracteres.

**Unidad 2 - Web Scraping con Python.** Navegadores. URL, DNS, IP. Sitio web.
Inspeccion del codigo HTML. Etiquetas principales (html, head, body, a, img).
Atributos. Ver codigo fuente e inspeccionar. Concepcion de web scraping.
Requests y BeautifulSoup. Metodos get, find y find_all. Recuperacion de valores
de las partes del elemento HTML. Opciones de busqueda.

**Unidad 3 - Consumo de APIs con Python.** Concepto de API. APIs publicas vs
privadas. Formatos de respuesta (JSON, XML). Metodos HTTP: GET, POST, PUT,
DELETE. Codigos de estado (200, 400, 404, 500). Modulo requests. Solicitudes GET
y POST. Manejo de respuestas JSON. Parametros en GET. Autenticacion con API keys
y tokens. Manejo de errores. Validacion de respuestas. Rate limiting.
Ejercitacion sobre API publica (ej. OpenWeatherMap).

**--- CORTE DE LA PRIMERA ENTREGA ---**

**Unidad 4 - Importar/Exportar datos con Python.** Proceso ETL. Estructuras de
datos en Pandas: DataFrame y Series. Etiquetas de columna e indices de fila.
Operaciones basicas. Metodos loc, sort_values, sort_index, set_index,
reset_index, query, iloc, concat, drop, sample, nsmallest, head, tail.
Agregacion: sum, mean, min, max. Importacion: read_excel, read_csv, read_table,
read_json, read_sql, read_html. Lectura de comprimidos (ZIP). Exportacion:
to_excel, to_csv.

**Unidad 5 - Trabajar con datos en Python.** Nulos y faltantes: isna, isnull,
notna, notnull, fillna, ffill, bfill, dropna, replace. apply y map. Cambios de
tipo: astype, convert_dtypes. Agregacion y agrupacion: groupby, agg, transform,
pivot_table, rolling, expanding, shift. Fechas: pd.to_datetime, dt.year,
dt.month, dt.day. Combinacion: merge, join, concat, append. Visualizacion con
.plot().

**Unidad 6 - Automatizacion de correos.** Servicio y servidor de email.
Protocolos SMTP, POP, IMAP. smtplib y EmailMessage. Composicion del email.
Conexion al servidor SMTP. Envio. Correos con formato HTML. Adjuntos. Acceso a
Gmail desde Python.
