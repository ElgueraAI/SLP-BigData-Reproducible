# Uso del CRM en una campaña piloto para Xilitla y Aquismón

**Decisión de campaña.** [HIPÓTESIS] Mercadotecnia puede ensayar dos creatividades sobre agua y cultura con una llamada a consultar la ficha y planear un itinerario. Xilitla (H07) y Aquismón (H06) delimitan el ensayo en Huasteca. Los mensajes sobre disponibilidad y acceso requieren verificación operativa previa con responsables locales. El documento rector vincula segmentación, mensajes, desempeño e impacto con las decisiones de campaña (Universidad Rosario Castellanos, *PP 5TO SEMESTRE*, pp. 3–5, 22–24 y rúbrica en pp. 7–8).

## Perfil, creatividad y llamada a la acción

| Campaña | Perfil hipotético | Pieza propuesta y CTA principal | Justificación |
|---|---|---|---|
| `camp-agua` | `explorador-natural`, con interés en naturaleza y agua | Video corto sobre cómo planear una parada en Cascada de Tamul, en Aquismón. CTA «Consulta condiciones de acceso». | La minería identificó Tamul como opción afín a aventura y documentó un antecedente de temporada. La publicación exige revisar la operación de la atracción con sus responsables. El control sintético del ensayo corresponde a la ficha general de Aquismón (H06). |
| `camp-cultura` | `viajero-cultural`, con interés en arte y cultura | Carrusel sobre arte y cultura en Xilitla. CTA «Consulta la ficha de Xilitla». | El catálogo documenta afinidad editorial con arte y cultura. La ficha reúne el contexto para planear y permite guardar la parada en Mi Ruta. |

La correspondencia entre perfil, pieza y CTA es una hipótesis editorial. [SIN_DATOS] Faltan datos consentidos para validar la afinidad. El simulador elige la campaña al azar con independencia del perfil y usa la misma regla aleatoria de clic en ambas campañas. Catálogo ([ruta `scripts/academic/bigdata04/catalog.json` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)) · Apriori (referencia del repositorio de origen) · Generador ([ruta `scripts/academic/bigdata04/simulator.py` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)).

## CTR de la prueba de carga

[DERIVADO] sobre datos [SIMULADO]. Corrida `run-04-100000a`, semilla 42, corte `d0d0c103c2c610332488cbeb` del 25 de noviembre de 2026 a las 14:59:50 UTC. Los 100.000 intentos comprenden todos los tipos de evento del catálogo. La tabla abarca la familia `campaign`, agregada para todos los perfiles y destinos de la corrida.

| Campaña | Impresiones elegibles con al menos un clic elegible | Impresiones elegibles únicas | CTR |
|---|---:|---:|---:|
| `camp-agua` | 1.395 | 3.312 | 42,12 % |
| `camp-cultura` | 1.343 | 3.259 | 41,21 % |

El CTR divide el numerador entre el denominador y multiplica por 100. La elegibilidad requiere un mínimo de 50 % de área visible durante 1.000 ms y un clic atribuible en la misma sesión para entrar en el numerador. El resultado confirma el cálculo de ambos indicadores a escala de laboratorio. La comparación de rendimiento creativo queda pendiente de un piloto autorizado con asignación aleatoria y seguimiento consentido. [Agregados de la corrida](measurements.json) · Vista `campaign_summary` ([ruta `scripts/academic/bigdata04/queries.sql` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)) · [Manifiesto y trazabilidad](BIGDATA04_RESULTADOS_VERIFICADOS.md).

## Instrumentación del piloto

| Elemento del piloto | Instrumentación y unidad | Decisión transferida |
|---|---|---|
| Exposición | Por campaña y fecha UTC de la impresión, área visible ≥50 % por ≥1 s y exposición con id único | En el piloto, usar `utm_content` para identificar cada pieza. Verificar que cada variante obtuvo oportunidades de exposición comparables. |
| Respuesta | Impresiones elegibles con al menos un clic elegible / impresiones elegibles × 100; denominador cero se informa sin estimación | Preparar una comparación con asignación aleatoria, horizonte y tamaño de muestra definidos antes del piloto. Las dos tasas simuladas solo verifican la lectura del sistema. |
| Interés en itinerarios | Altas y bajas por evento único, junto al número de destinos activos al final | Estudiar si el mensaje conduce a guardar una ficha y si después se conserva. Etiquetar ruta y favorito por separado. |
| Atribución a recomendación | Elementos mostrados por lista y acciones de guardado atribuidas a sugerencias | Investigar discrepancias entre listas mostradas, altas atribuidas y paradas activas. |
| Cupo, acceso y ambiente | Expediente de revisión, plazas autorizadas y reservadas en el mismo intervalo, disponibilidad, fuente y vigencia | Retirar la candidatura ante cupo agotado, cierre, alerta o evidencia insuficiente. Registrar motivo y revisión. |

## Demostración visual y decisiones A–D

[SIMULADO] La corrida visual `run-demo-visual` muestra `camp-cultura` con el perfil ficticio `viajero-cultural`. En la demostración del 25 de noviembre de 2026 hubo siete impresiones elegibles con clic entre nueve elegibles (77,78 %). La retransmisión de una impresión conserva el denominador de nueve. Estas cifras corresponden al guion visual y se consultan en su propio corte del tablero. [Guion y comandos](BIGDATA04_GUIA_DEMO_PROFESOR.md) · Eventos del guion ([ruta `scripts/academic/bigdata04/showcase.py` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)).

| Caso | Entrada del escenario visual [SIMULADO] | Resultado de la regla y decisión para mercadotecnia |
|---|---|---|
| A · Xilitla (H07) | Siete clics con ocho impresiones elegibles. Diez reservas para diez plazas. | **Pausa.** El cupo disponible es cero. Retirar la promoción del destino hasta tener una revisión vigente favorable. |
| B · Aquismón (H06) | Una impresión elegible sin clic. Cuatro reservas para diez plazas. | **Candidato.** Las seis plazas disponibles permiten pasar a revisión humana de acceso, operación y ambiente antes de considerar pauta. |
| C · Las Pozas de Edward James (H08) | Destino de contraste sin revisión operativa en la demostración. | **Sin datos.** Excluir de la reasignación de presupuesto hasta contar con su propio expediente verificado y vigente. |
| D · Aquismón (H06) | La segunda revisión reduce el cupo a cuatro plazas y conserva cuatro reservas. | **Pausa.** La revisión sustituye la candidatura B. Registrar fecha y motivo del cambio y detener la promoción hasta una nueva revisión favorable. |

La regla `capacity-gate-v1` calcula plazas disponibles como cupo menos reservas para el mismo intervalo. Una plaza disponible es el mínimo del ensayo. El registro conserva las revisiones y exige aprobación humana para cualquier aumento de pauta. En la prueba de carga también quedaron Xilitla y Aquismón en pausa al cierre, según el historial del mismo corte. Regla y datos de los casos ([ruta `scripts/academic/bigdata04/policy.py` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)) · [Historial de la prueba de carga](measurements.json).

**Conexión con las seis UCA.** Big Data entrega denominadores y cortes reproducibles. Apriori identifica combinaciones temáticas de la oferta y respalda la formulación de variantes. K-means aporta contexto sobre la composición municipal de la oferta. [HIPÓTESIS] Estocásticos podrá variar las llegadas y los cambios de cupo con supuestos documentados. Investigación de Operaciones podrá usar la elegibilidad como restricción binaria cuando se disponga de costos y respuesta por canal. Mercadotecnia podrá comparar creatividades entre destinos verificados con presupuesto, consentimiento, calendario y métricas definidos. Apriori (referencia del repositorio de origen) · K-means (referencia del repositorio de origen) · Plan de campaña (referencia del repositorio de origen).

**Evidencia que falta para decidir sobre destinos reales.** [SIN_DATOS] Faltan cupos operativos autorizados, reservas comparables por intervalo, vigencia local de restricciones, medición consentida de exposición real, inversión, conversiones y ROI. [OBSERVADO] Los datos históricos de INAH describen entradas a recintos. DataTur informa ocupación del centro monitoreado. Sus cortes mensuales ayudan a formular preguntas de calendario. La evaluación de redistribución física e impacto social y ambiental necesitaría un diseño con afluencia independiente, periodos comparables y seguimiento de los destinos emisores y receptores. Cobertura histórica (referencia del repositorio de origen).
