# Arquitectura de datos

El proyecto académico sustenta el diseño de una campaña turística inteligente y sustentable para San Luis Potosí. El portal Astro y el almacén analítico son flujos separados. El paquete de distribución contiene el flujo analítico y el código de referencia para su revisión académica.

## Capas ejecutadas

Raw conserva archivos y huellas SHA-256. Bronze conserva los valores fuente, encabezados y localizadores. Silver tipifica medidas, normaliza periodos y valida unidades, claves y valores. Gold materializa dos hechos en Parquet ZSTD. DuckDB carga esos hechos, crea dimensiones y consulta el calendario. Las consultas y controles de calidad viven en archivos SQL.

Los hechos comparten calendario y metadatos. INAH conserva entradas registradas a recintos y DataTur conserva cuartos promedio diario y porcentaje de ocupación del centro hotelero monitoreado. La unión temporal deja sus indicadores en columnas independientes. [Diagrama editable](../figures/flujo.md).

## Decisiones arquitectónicas

La auditoría Big Data 01 ponderó el ajuste técnico y obtuvo 94,2/100 para el procesamiento por lotes con Parquet y DuckDB. Fue un criterio técnico ponderado, separado de las mediciones experimentales. Los archivos de entrada llegan como cortes versionados. El procesamiento local aprovecha el formato columnar y permite revisar resultados sin operar un servicio activo.

| Alternativa | Función evaluada | Condición de reevaluación |
|---|---|---|
| MongoDB | Servicio documental opcional sobre resultados aprobados | Concurrencia o consultas geográficas que precisen una API |
| Spark | Procesamiento distribuido | Ventana de procesamiento incumplida con carga real y optimización local |
| Hadoop/HDFS | Almacenamiento distribuido | Infraestructura y operación institucional justificadas |
| Lambda / Kappa | Patrones con flujo de eventos | Eventos autorizados y objetivos de latencia medidos |

Big Data 01 auditó Atlas en lectura. La colección de 2.000 reservas carecía de procedencia y vínculo territorial acreditados para el proyecto. Su contenido queda fuera de los insumos y de este paquete. [Resultados verificados](resultados_verificados.md).
