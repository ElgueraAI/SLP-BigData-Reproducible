# Auditoría independiente de Big Data 04

**Dictamen al 25 de noviembre de 2026.** La evidencia respalda la demostración académica local con interacciones, identidades y cupos [SIMULADO]. Se verificaron el flujo Kafka–MongoDB, la recuperación, el replay y los tres cortes analíticos. El alcance es un host WSL2, un broker con réplica uno y un ensayo por volumen. El entorno se mantiene en loopback y queda reservado al laboratorio. La evidencia disponible no permite caracterizar impacto turístico, carga real, escalabilidad entre nodos ni aptitud para operación pública.

Rama `feature/academic-multiagents`, base `3fe53fc`. Las cifras de latencia, disponibilidad, offsets y recursos son [OBSERVADO] en el sistema de demostración. Las cifras de interacción, estados y decisiones se reconstruyeron como [DERIVADO] sobre entradas [SIMULADO]. El [informe de resultados](BIGDATA04_RESULTADOS_VERIFICADOS.md) fija semilla 42 y UTC para las tres corridas. Las rutas privadas se indican relativas a `.bigdata-private/bigdata04/` y corresponden a evidencia local ignorada por Git. [Plan de aceptación](bigdata04-plan-pruebas.md) · [Agregados de medición](measurements.json).

## Conciliación independiente

Se ejecutó `audit.py` con DuckDB 1.5.5 y PyArrow 25.0.1 en WSL. El auditor abrió los archivos en un proceso separado y trabajó directamente desde `events.parquet`. Comparó bytes y SHA-256, esquemas, procedencia, identidad de corrida y corte, contenido lógico y paridad entre las 14 tablas de DuckDB y Parquet en ambos sentidos con `EXCEPT ALL`. Cada manifiesto enumera 16 artefactos. Se verificaron los tres cortes de escala y el corte de replay. Los hashes lógicos se recalcularon de los archivos, incluidas las huellas del catálogo, corpus, controles y resultados. Auditor SQL ([ruta `scripts/academic/bigdata04/audit.py` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)) · Evidencia local `audit-independent.json`.

Para el CTR, la consulta descartó identificadores de impresión ambiguos. Una impresión elegible requiere fracción visible ≥ 0,50 y permanencia ≥ 1.000 ms. El clic debe corresponder a la misma familia, actor, sesión, destino y campaña, con tiempo igual o posterior al de la impresión. El numerador cuenta exposiciones elegibles distintas con al menos un clic y atribuye ese resultado al día UTC de la impresión. El cálculo se contrastó por celda completa, por día y por campaña. Los grupos de denominador cero devolvieron nulo.

| Intentos HTTP | Aceptados | Cuarentena API | Únicos | Duplicados | Tardíos únicos | CTR Agua | CTR Cultura |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.000 | 977 | 23 | 950 | 27 | 39 | 14/37 = 37,84 % | 16/38 = 42,11 % |
| 10.000 | 9.793 | 207 | 9.490 | 303 | 1.254 | 153/343 = 44,61 % | 124/327 = 37,92 % |
| 100.000 | 98.010 | 1.990 | 94.999 | 3.011 | 13.065 | 1.395/3.312 = 42,12 % | 1.343/3.259 = 41,21 % |

Las tres series conciliaron intentos con aceptados y rechazados, y aceptados con únicos y duplicados. Los cortes terminales del tablero tienen otros identificadores y tiempos de evaluación. El hash del corpus, los conteos de eventos, las métricas de campaña y los estados activos coincidieron con sus respectivos cortes exportados. El watermark es histórico por partición y persiste entre corridas. Los tardíos únicos registrados con umbral de 5 s y los retrasos intencionales del simulador son medidas distintas. Evidencia local `benchmarks/<corrida>/{result,flow,publication,dashboard-after}.json`.

La consulta de estado seleccionó la última mutación por `(event_sequence, event_id)` para cada actor, ruta y destino, o actor y destino para favoritos. Contrastó marcas activas e inactivas y contabilizó las acciones canónicas de alta y baja por separado.

| Intentos | Rutas altas/bajas/activas/inactivas | Favoritos altas/bajas/activos/inactivos |
|---:|---:|---:|
| 1.000 | 59 / 18 / 41 / 18 | 41 / 14 / 27 / 14 |
| 10.000 | 636 / 229 / 407 / 226 | 456 / 174 / 282 / 173 |
| 100.000 | 6.385 / 2.395 / 3.990 / 2.360 | 4.431 / 1.790 / 2.641 / 1.769 |

En las tres escalas, A agotó sus 10 plazas, B conservó seis plazas inicialmente y pasó a candidato con revisión humana, y D registró la revisión 2 con cuatro plazas y cuatro reservas y pausó B. Las 50 fichas sin revisión conservaron el estado C. Cero filas autorizaron un aumento automático. El ensayo de interfaz registró siete clics digitales para H07 y cero para H06, con el cambio B→D y un elemento activo final tanto en rutas como en favoritos. Evidencia local `dashboard-qa/{flujo-inicial,flujo-intermedio-observado,flujo-revision-d}.json`.

## Pruebas de aceptación

| ID | Resultado y alcance comprobado | Evidencia |
|---|---|---|
| T01 | Validada. El SHA-256 del compilado coincide con el catálogo, 52 destinos, 4 regiones, 8 perfiles y 12 intereses. El validador rechaza un destino ajeno. | `catalog.json`, `dist/data/intel.json`, `test_strict_shape_types_and_catalogs`. |
| T02 | Validada. Los 13 tipos y sus campos obligatorios tienen cobertura automatizada. Las pruebas HTTP con productor de prueba cubren 202/207/400/413/503. El flujo real confirma 202 tras acuse Kafka y 400 por campo extra. | `test_pipeline.py`, `audit-unittest.txt`, `audit-ack.json`. |
| T03 | Validada. Un cliente cerró el socket tras enviar el cuerpo. El corte mostró un hecho durable antes del reenvío. Kafka acusó el duplicado y el conflicto en nuevas posiciones. El consumidor registró un único, un duplicado y un conflicto, conservó H06 y marcó el corte conflictivo. | `audit-ack.py`, `audit-ack.json`. |
| T04 | Validada. El oráculo de ruta desordenada conserva dos altas, una baja y H06 activo. Los tres cortes concilian las filas de estado y acciones. | `test_route_and_favorite_tombstones_survive_replay`, `audit-independent.json`. |
| T05 | Validada. El reingreso de un favorito conserva un activo y la eliminación de otro actor no altera su estado. Las tres exportaciones y el replay concilian. | `test_route_and_favorite_tombstones_survive_replay`, `audit-independent.json`. |
| T06 | Validada. Se reprodujeron dos denominadores y un numerador (50 %), dos acciones elegibles y CTR nulo con denominador cero. Incluye umbral, clic huérfano, cruzado, previo y repetido. | `test_ctr_reconciles_late_transport_and_utc_window`, `audit.py`. |
| T07 | Validada. Una lista de dos destinos y un guardado atribuido producen una sola mutación activa de ruta. Las recomendaciones también se reconstruyeron desde los Parquet. | `test_recommendation_count_shares_single_route_mutation`, `audit.py`. |
| T08 | Validada. El clic después de medianoche UTC conserva el día de su impresión. El orden inverso de transporte produce el mismo resultado. MongoDB cuenta una llegada fuera de tolerancia en una base de prueba. | `test_ctr_reconciles_late_transport_and_utc_window`, `test_batched_canonical_classification_cuts_and_replay`. |
| T09 | Validada. Con el mismo consumidor, el rezago total de entrada y cuarentena fue 0→500→0 y drenó 16,30 s después de la orden de arranque. En consumidor aislado se forzó salida 86 entre persistencia y commit y se releyeron 500 posiciones sin nueva publicación. | `benchmarks/run-04-1000a/{result,drills}.json`. |
| T10 | Validada. El replay en grupo y base nuevos drenó 10,44 s después del reinicio. Se verificaron conteos y hashes lógicos iguales del corpus, catálogo, controles y resultados con la misma fecha de evaluación. | `benchmarks/run-04-1000a/replay.json`, `audit-independent.json`. |
| T11 | Validada. Broker y MongoDB reiniciados con volúmenes conservados. Se comprobaron posiciones y 950 únicos persistentes. Un fallo de escritura inyectado antes del manifiesto en un directorio temporal preservó el SHA-256 y acceso al corte anterior y no publicó uno parcial. | `benchmarks/run-04-1000a/drills.json`, `audit-staging.{py,json}`. |
| T12 | Validada con retest. Las tres salidas y el replay pasaron verificación física y lógica. Se probó el rechazo de corridas mezcladas, inventario incompleto y esquema declarado alterado. Se comprobó la igualdad fila por fila de DuckDB y Parquet. Los históricos conservan conteo, unidad, periodo y hash, en lectura separada. | `audit-independent.json`, `test_mixed_runs_are_rejected`, `test_parquet_duckdb_and_hashes_are_verified`, `historical-{before,after}.json`. |
| T13 | Validada. A–D comprobados con Parquet y tablero. El ensayo automatizado verifica vigencia vencida y alerta ambiental. | `audit-independent.json`, `dashboard-qa/flujo-revision-d.json`, `test_cases_a_to_d_and_expired_newer_revision`. |
| T14 | Validada. En Edge, tras dos publicaciones confirmadas por API, la misma pestaña se actualizó de uno a dos canónicos en dos cortes con fecha UTC. Se comprobaron los cinco módulos, la revisión D y la degradación real. Durante la caída de API, el tablero conservó un corte con 22 únicos y recuperó las señales de API y Kafka al reanudar. | `audit-live.{mjs,json}`, `dashboard-qa/{browser-results,flujo-intermedio-observado,api-outage}.json`. |
| T15 | Validada en el alcance local. Docker publica la API en `127.0.0.1:18404` y el tablero en `127.0.0.1:18504`. Kafka y MongoDB carecen de puertos publicados. La captura de red del tablero solo registró el origen local. La API devolvió `unknown_fields` sin eco del centinela, ausente también en los logs examinados y en los documentos de la corrida de prueba en MongoDB. Se conservaron los SHA-256 del PDF rector, DuckDB histórico y dos Parquet oficiales. | `compose.yaml`, `api.py`, `audit-{ack,live,canary-logs,canary-mongo}.json`, `historical-{before,after}.json`, inspección Git. |
| T16 | Validada. La API devolvió 503 con Kafka detenido. Con Mongo detenido quedaron 30 entregas pendientes y los offsets confirmados no avanzaron. Tras el arranque, los offsets alcanzaron el final. El productor de prueba cubre fallo de acuse y salud degradada. | `benchmarks/run-04-1000a/drills.json`, `test_status_codes_and_failed_ack`. |

El auditor ejecutó `docker compose … exec -T -e CRM_TEST_MONGO_URI=mongodb://mongo:27017 api python -m unittest -v test_pipeline test_reducer`. Pasaron 17/17 sin omisiones, en 5,582 s antes de la corrección del verificador. La coordinación reejecutó 17/17 en 7,733 s con la regresión ampliada. Las tres pruebas de persistencia usaron bases aisladas de MongoDB real. La coordinación confirmó `npm.cmd test` con 166/166 y `npm.cmd run check` con 207 archivos, cero errores, cero advertencias y 11 pistas. El alcance de esta revisión no incluyó repetir `npm run build`, `verify:pages`, `verify:routing` ni `verify:navigation`. La comparación Git confirmó ausencia de cambios de Big Data 04 en `src`, `public`, `package.json` y la configuración Astro. Evidencia local `audit-unittest.txt`, `portal-test.txt` y `portal-check.txt`.

En Edge se verificaron la navegación por teclado hacia el enlace de salto, el control de pausa, filtros, cinco secciones y ausencia de desbordamiento horizontal de la página a 1.440, 820 y 390 px. La consola no registró errores en esas capturas. Los valores de CLS de esa ejecución fueron 0,0336, 0,0050 y 0. Las pruebas corresponden a un navegador de laboratorio y cubren esos puntos de accesibilidad. [Guion de demo](BIGDATA04_GUIA_DEMO_PROFESOR.md) · Evidencia local `dashboard-qa/browser-results.json`.

## Hallazgos y retest

| Severidad | Hallazgo y reproducción | Corrección o alcance del retest |
|---|---|---|
| P0 | No se identificó un fallo crítico en el entorno local revisado. | Dictamen limitado a la demostración con corpus sintético. |
| P1 corregido | En la primera versión, el listado mutable `manifest.files` permitía omitir `crm.duckdb` o `indicators.json`. Un corte podía declararse verificado sin corroborar bytes, esquema o contenido DuckDB. La regresión reproduce las omisiones y la alteración de esquema con un manifiesto temporal. | El verificador ahora exige el inventario, coteja tamaño, SHA-256, esquema y metadatos de corte y contrasta DuckDB con Parquet. La regresión pasó y la verificación SQL independiente concilió los cuatro cortes. Implementación ([ruta `scripts/academic/bigdata04/export.py` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)) · Regresión ([ruta `scripts/academic/bigdata04/test_reducer.py` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)). |
| P2 abierto | El perfil Docker con construcción y descargas quedó [SIN_DATOS]. El laboratorio ejecutó el perfil offline con bibliotecas de Ubuntu 24.04 ya instaladas. | Para reivindicar portabilidad entre equipos, reproducir el perfil portátil en host limpio con dependencias aprobadas y ejecutar la prueba de humo. Compose ([ruta `scripts/academic/bigdata04/compose.yaml` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)) · Arranque ([ruta `scripts/academic/bigdata04/README.md` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)). |
| P2 abierto | La medición única por escala no separa variación entre corridas, arranque frío y caliente ni capacidad distribuida. El consumo de CPU y RAM está muestreado por cgroup. Los bytes disponibles son de exportación y MongoDB acumulado. | Mantener las comparaciones descriptivas y repetir cargas antes de fijar un objetivo operativo. El informe de resultados documenta unidades y alcance. [Medición](BIGDATA04_RESULTADOS_VERIFICADOS.md) · Captura de recursos ([ruta `scripts/academic/bigdata04/benchmark.py` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)). |
| P2 condicionado | El API local acepta el contrato sintético sin autenticación y limita tamaño y lote, pero no aplica una cuota por cliente. El broker tiene retención y, en esta topología, una sola réplica. La confiabilidad demostrada cubre reinicio con almacenamiento conservado. | Estas condiciones son compatibles con el laboratorio cerrado. Operación pública requeriría diseño, autorización y validación separados, con autenticación, límites de tasa, retención y recuperación acordes al uso. API ([ruta `scripts/academic/bigdata04/api.py` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)) · [Arquitectura](bigdata04-arquitectura.md). |

## Informe, cuaderno y transferencia

La rúbrica privada contiene 24 páginas. En las páginas 5 y 6 establece la extensión sugerida de 30–40 páginas para el informe integrado de campaña y asigna 12 % al criterio de almacenamiento e integración. El incidente crítico y sus preguntas constan en las páginas 15 y 16. La entrega de esta misión es el informe especializado de la UCA, pedido con un máximo preferido de 15 páginas. Su PDF tiene 12 páginas, incluidas portada y referencias. Se cotejaron el texto en tercera persona, referencias en última página, separación entre datos oficiales, interacciones sintéticas y medición técnica, y las respuestas al incidente en el diseño de datos, la verificación operativa y la privacidad. Según el control de Word, la pieza contiene tres ecuaciones nativas, dos figuras y siete tablas. Se verificaron las copias de Word y PDF en `Documents` por SHA-256. La validación del informe integrado de campaña y su paginación queda fuera del alcance de esta misión.

El cuaderno pasó ejecución local con kernel Python en WSL tanto con sus agregados embebidos como con un corte Parquet. Los dos modos produjeron ocho figuras y ejecutaron 11 celdas de código. [SIN_DATOS] Ejecución en Google Colab alojado. La matriz de transferencia del informe enlaza almacenamiento, Apriori, K-means, modelos estocásticos, investigación de operaciones y mercadotecnia con sus insumos y límites. La campaña recibe un protocolo de instrumentación y condiciones operativas para un piloto. Ninguna salida acredita afluencia, conversión, ROI, causalidad ni capacidad real de un destino. [Cuaderno](../UCA01_BigData04_Kappa_CRM_SLP.ipynb) · [Transferencia](BIGDATA04_TRANSFERENCIA_MERCADOTECNIA.md) · Evidencia local `notebook-validation.json`.

## Repetición del cotejo independiente

Desde la raíz del repositorio en PowerShell, se pueden pasar los manifiestos terminados al verificador independiente. Los manifiestos de replay bajo la carpeta privada `replay/` se pueden añadir como argumentos.

```powershell
$raiz = '.bigdata-private/bigdata04'
$manifiestos = Get-ChildItem "$raiz/exports/run-04-1000a/*/manifest.json", `
  "$raiz/exports/run-04-10000a/*/manifest.json", "$raiz/exports/run-04-100000a/*/manifest.json" |
  ForEach-Object { (Resolve-Path $_ -Relative) -replace '\\', '/' }
wsl.exe -d Ubuntu-24.04 --exec /ruta/al/entorno/bin/python -B `
  scripts/academic/bigdata04/audit.py @manifiestos
```
