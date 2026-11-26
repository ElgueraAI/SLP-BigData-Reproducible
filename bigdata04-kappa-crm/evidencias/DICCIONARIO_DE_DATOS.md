# Diccionario de datos del CRM

La evidencia de interacción, decisiones y cupos es [SIMULADO]. La instantánea `catalog.json` contiene 52 referencias editoriales de destino, ocho perfiles y doce intereses. Las referencias identifican sitios. Los actores, sesiones, campañas, exposiciones y usos del cupo se generan para el laboratorio. Los manifiestos declaran el esquema físico completo de cada tabla, sus filas, huellas y tamaño.

| Campo o unidad | Interpretación |
|---|---|
| `simulation_run_id`, `cut_id` | Corrida sintética y corte exportado. Se usan juntos para identificar una evidencia analítica. |
| `event_id`, `event_type`, `schema_version`, `source`, `synthetic` | Identidad y tipo del evento, versión 1, origen `simulator` y bandera verdadera. Un evento canónico aporta una vez. |
| `event_time`, `received_at`, `event_sequence` | Hora UTC simulada, sello real de recepción y orden lógico positivo por actor. El registro técnico distingue tiempo de negocio y latencia. |
| `demo_actor_id`, `session_id`, `route_id`, `impression_id` | Identificadores ficticios con alcance de corrida. El identificador vincula acciones con la entidad correspondiente. |
| `eligible_impressions`, `clicked_impressions`, `ctr_pct` | Conteos de impresiones elegibles y de impresiones elegibles con al menos un clic atribuido. CTR = 100 × segundo conteo / primer conteo. Con denominador cero, CTR nulo. |
| `eligible_click_actions`, `click_actions` | Acciones elegibles y acciones totales de clic. Una impresión puede acumular varias acciones. |
| `active`, `adds`, `removes` | Estado final y conteos de altas y bajas. El estado aplica la última secuencia válida. |
| `capacity`, `reservations`, `places_available`, `revision` | Plazas simuladas, reservas simuladas, diferencia entre ambas y versión de la revisión operativa. |
| `status`, `reason`, `automatic_increase` | Decisión de política, motivo y autorización automática. El prototipo conserva esta última en falso. |
| `partition`, `offset`, `committed`, `end`, `lag` | Posiciones de Kafka. El rezago es el número de posiciones pendientes entre el offset confirmado y el final. |

| Parquet | Grano |
|---|---|
| `events` | Un evento canónico por ID en el corte. |
| `campaign_metrics`, `ctr_daily`, `ctr_cells` | Métricas por familia y campaña. Las celdas agregan día UTC, perfil y destino cuando aplica. |
| `route_state`, `favorite_state`, `state_actions` | Una pertenencia de ruta o favorito por clave y una acción por evento de mutación. |
| `profiles`, `regions`, `destinations`, `interests` | Una fila de resumen por etiqueta del catálogo correspondiente. |
| `controls`, `decisions`, `decision_history` | Una revisión operativa, una decisión de corte o una decisión histórica por revisión, según la tabla. |

Consulte el [contrato de eventos](bigdata04-contratos.md) para los campos requeridos por cada tipo y las condiciones de atribución.
