# Resultados históricos verificados

Fecha de verificación original: 14 de noviembre de 2026. La fuente de evidencia es el expediente técnico Big Data 01–03 del proyecto. Los valores de esta página son agregados documentales, separados de los resultados ejecutables de la demostración.

| Evidencia | Resultado | Universo |
|---|---|---|
| Auditoría Big Data 01 | 401 archivos visibles, 1.368.589.545 bytes, 91 fuentes Raw conciliadas y 27 tablas Silver/Gold catalogadas | Árbol visible de Drive. El tamaño incluye representaciones repetidas |
| Reproducción Big Data 02 | 8.210 filas fuente en Bronze, 420 Gold y 63 totales cero. Coincidieron 420 claves y conteos históricos | Tres recintos INAH, 140 meses por recinto, enero 2015 a agosto 2026 |
| Integración Big Data 03 | 31 ZIP DataTur, 93 lecturas por edición en Silver y 31 meses Gold. Cero cambios en 26 comparaciones con edición contemporánea | Centro hotelero monitoreado, enero 2024 a julio 2026 |
| Cotejo Big Data 03 | 31/31 filas en ambos Parquet históricos. 109 meses fuera del corte DataTur en el calendario de 140 meses | Gold hotelero y calendario con cobertura independiente |
| Determinismo Big Data 02 | Cuatro Parquet y siete consultas iguales en dos procesos | Salidas de las dos corridas INAH |
| Determinismo Big Data 03 | 11 Parquet y ocho consultas iguales en dos procesos | Salidas de la integración |
| Rendimiento Big Data 02 | 9,875 y 7,304 s | Flujo INAH completo, con exportaciones |
| Rendimiento Big Data 03 | 4,008 y 3,699 s | Integración, controles y exportaciones |
| [SIMULADO] Benchmark Big Data 02 | 10.000 y 100.000 eventos únicos recuperados con hash idéntico | Reingesta de eventos ficticios, con duplicados y tardíos |
| [SIMULADO] Benchmark Big Data 03 | Mediana para exportar Q2 en 100.000 eventos, 750,47 ms con Python y 295,82 ms con DuckDB COPY | Cinco repeticiones, mismo resultado CSV, medición local |

Las cifras INAH describen entradas a recintos. DataTur describe el centro monitoreado. Las hipótesis de calendario dependen de la ventana. Usar estas salidas para redistribuir pauta exige verificar operación, derechos, acceso, capacidad, costos y respuesta atribuible a un piloto.
