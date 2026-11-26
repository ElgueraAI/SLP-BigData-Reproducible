# Auditoría de cierre de Big Data 04

**Fecha del cierre: 25 de noviembre de 2026, hora del centro de México.** Se cotejaron el informe Word y el PDF de 12 páginas con los cortes originales, el ensayo posterior del estudiante y el nuevo ensayo de extracción. Los sellos de proceso de la sesión nocturna aparecen como 26 de noviembre en UTC.

## Conciliación con el informe entregado

| Evidencia | Identificador y resultado | Correspondencia con el informe |
|---|---|---|
| Experimento original [SIMULADO] | `run-04-1000a`, `run-04-10000a` y `run-04-100000a`. Los cortes conservan 950, 9.490 y 94.999 eventos únicos. | Word y PDF coinciden con los manifiestos; las tres corridas permanecen en el cuaderno y en las mediciones originales. |
| Recuperación original [OBSERVADO] | `run-04-1000a`; 500 posiciones pendientes durante la pausa, 16,30 s para drenar, rezago final 0. | Coincide con el valor del informe. El replay cotejó las 14 tablas. |
| Recuperación posterior [OBSERVADO] | `run-clase-20261125201705`; 16,43327055 s entre arranque y drenaje, rezago final 0. | Se añade con su propio `result.json` y corte. El informe conserva 16,30 s para la corrida original. |
| Demostración original [SIMULADO] | `run-demo-visual`; caso C destacado en la transferencia de Mercadotecnia: Las Pozas de Edward James (H08). | El cuadro del informe describe el caso C como un destino sin revisión operativa. La versión de transferencia identifica Las Pozas para el guion original. |
| Demostración posterior del estudiante [SIMULADO] | `run-demo-20261125200543`; 19 eventos canónicos en el prefijo inicial, 22 al cierre. Caso C: Real de Catorce (A01), `sin_datos`. | La consulta directa del registro y del corte final de MongoDB confirma los conteos y la decisión de A01. Se conserva en `.bigdata-private/bigdata04/demo-estudiante.json`. |

En el corte `7a47c8f181a25651dc3191d8` de la demostración posterior, `camp-cultura` conservó siete impresiones con clic atribuido entre nueve elegibles. Cálculo [DERIVADO]: 100 × 7 / 9 = 77,78 % redondeado a dos decimales. Tras un duplicado hubo 23 entregas y 22 eventos únicos. Para Aquismón (H06), el historial conserva la revisión 1 como candidato, con 10 plazas y 4 reservas, y la revisión 2 como pausa, con 4 plazas y 4 reservas. Las plazas son simuladas.

## Verificación del paquete extraído

Se extrajo el ZIP de ensayo y se inició el código empaquetado con el perfil offline WSL2. El proyecto Docker de prueba tuvo su propia red interna y volúmenes. La API y el tablero devolvieron HTTP 200 desde esa red y Kafka estuvo disponible. Pasaron las **17 pruebas** con MongoDB, sin omisiones. El verificador cotejó los cinco manifiestos y sus 14 tablas por corte. Durante la parada del consumidor aislado quedaron 50 eventos nuevos pendientes. Se reinició el consumidor y el rezago final fue 0 tras 19,64 s. La comparación de contenedores confirmó que los cinco servicios del stack original permanecieron activos con las mismas identidades. Se detuvo solo el stack de prueba y se conservaron sus volúmenes. Registro del ensayo ([ruta `.bigdata-private/bigdata04/aislamiento-resultados.json` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)).

El perfil portátil se comprobó hasta el análisis de configuración de Compose. La construcción desde cero y la instalación independiente en otro equipo requieren validar las dependencias externas. La prueba offline reutilizó imágenes y dependencias ya presentes.

## Consulta del cuaderno y contenido distribuido

Se incluyó el [enlace de Colab verificado por el estudiante](https://colab.research.google.com/drive/1fS4TH9e0PiOsWHfEhIpZRNRcSa1rA10J?usp=sharing) junto con el IPYNB y el HTML ejecutado. La confirmación alojada proviene del estudiante. El archivo local incluye las 11 celdas y las ocho gráficas. La validación previa del cuaderno en WSL quedó registrada en `.bigdata-private/bigdata04/notebook-validation.json`.

La distribución contiene la instantánea editorial mínima del catálogo, los eventos ficticios, las salidas del CRM y el registro técnico seleccionado. El informe Word y el PDF se cotejaron localmente y conservan la versión ya entregada por separado. Se excluyeron del ZIP los informes que identifican a sus autores, los documentos universitarios restringidos, el histórico INAH/DataTur, los montajes y rutas personales de entorno, los secretos y los datos personales. Los manifiestos originales conservan sus referencias agregadas al contexto histórico y sus huellas. Las fuentes históricas permanecen fuera del paquete.
