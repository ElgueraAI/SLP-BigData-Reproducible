# Diccionario de productos

| Producto | Clave y grano | Medidas y unidades | Origen y cobertura |
|---|---|---|---|
| `fact_inah_visits_monthly` | `site_id, period`. Recinto y mes | `national_visits`, `foreign_visits` y `total_visits`, entradas registradas | INAH. Tres recintos del corte, enero 2015 a agosto 2026 |
| `silver_datatur_vintages` | `center_id, period, edition`. Centro, mes y edición | `available_rooms_daily_avg`, `occupied_rooms_daily_avg`, cuartos/día promedio. `hotel_occupancy_percent`, porcentaje | Hoja mensual de DataTur, conserva comparativas interanuales |
| `fact_datatur_occupancy_monthly` | `center_id, period`. Centro monitoreado y mes | Promedios diarios y porcentaje con denominador de disponibles | DataTur. Ediciones contemporáneas de enero 2024 a julio 2026 |
| `dim_period` | `period`. Primer día de mes | Año, mes y días civiles | Calendario |
| `dim_entity` | `entity_id` | Nombre, familia y ámbito | Identidades separadas por fuente |
| `dim_source` | `source_id, source_version` | Identificador, edición y URL | Metadatos de fuentes |
| `campaign_calendar` | `period` | Entradas por recinto, cuartos promedio y ocupación en columnas separadas | Alineación temporal. Fuera del corte DataTur, la ocupación permanece nula |

`observation_status` distingue conteos informados, fuente incompleta y ausencia de cobertura. Los localizadores de Bronze conservan archivo, fila, y hoja o miembro cuando corresponda. Las tablas de los ejemplos reproducen un subconjunto del esquema con claves ficticias y estado [SIMULADO].
