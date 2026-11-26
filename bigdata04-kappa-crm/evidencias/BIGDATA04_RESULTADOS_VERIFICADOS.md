# Resultados verificados de Big Data 04

[OBSERVADO] Mediciones del 25 de noviembre de 2026, rama `feature/academic-multiagents`, base `3fe53fc`. Cada fila corresponde a una ejecución completa con semilla 42. El corpus es [SIMULADO]. La publicación se hizo por HTTP en lotes de hasta 250 intentos con confirmación de Kafka. El contador de eventos únicos se cotejó con MongoDB, Parquet, DuckDB y el tablero.

## Conservación y rendimiento

| Intentos | Kafka aceptó | Cuarentena API | Únicos | Duplicados | Únicos tardíos | E2E únicos/s | Consumo activo únicos/s |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 977 | 23 | 950 | 27 | 39 | 43.90 | 1123.74 |
| 10,000 | 9,793 | 207 | 9,490 | 303 | 1,254 | 542.25 | 943.54 |
| 100,000 | 98,010 | 1,990 | 94,999 | 3,011 | 13,065 | 674.11 | 1460.32 |

Cada intento terminó aceptado o rechazado. Los aceptados se reconciliaron con únicos y duplicados; el rezago final fue cero en las tres corridas. El rendimiento extremo a extremo divide únicos por el intervalo entre inicio de publicación y drenaje confirmado. El activo divide únicos por la suma de milisegundos activos de los lotes de entrada. El caso de 1.000 incluye una pausa controlada. La marca temporal máxima de cada partición es compartida entre corridas y el generador reinicia su reloj. El conteo de tardíos observados (umbral 5 s) puede incluir eventos adicionales a los retenidos deliberadamente por el simulador.

| Intentos | Media ms | p50 ms | p95 ms | p99 ms | Generación s | Publicación s | Validación s | Persistencia s | Consulta DuckDB s | Refresco servidor s |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 8511.94 | 363.00 | 16836.00 | 16838.00 | 0.027 | 0.199 | 0.114 | 0.708 | 0.095 | 0.193 |
| 10,000 | 7403.97 | 8556.00 | 13359.55 | 13427.00 | 0.571 | 3.347 | 1.688 | 8.154 | 0.080 | 0.826 |
| 100,000 | 52138.61 | 49911.00 | 116176.00 | 122281.00 | 2.235 | 13.249 | 12.014 | 51.361 | 0.116 | 11.065 |

Las latencias miden desde la aceptación para publicación hasta el acuse durable del primer registro en MongoDB. Se empleó interpolación lineal sobre nuevos únicos. Las fases se superponen y el refresco corresponde al servidor. El sondeo del navegador y el tiempo de dibujo de la pantalla se evalúan aparte.

## Recursos y almacenamiento

Host de medición: Linux-6.18.33.2-microsoft-standard-WSL2-x86_64-with-glibc2.39. CPU Intel(R) Core(TM) i7-7820HQ CPU @ 2.90GHz, 6 procesadores lógicos, MemTotal:       10184824 kB. Docker Engine 29.8.1; Docker Compose version v5.5.1.

| Intentos | Cgroup máximo muestreado por servicio (MiB)¹ | CPU acumulada observada por servicio (s) | Archivos exportados (bytes) | Mongo al cierre con índices (bytes) |
|---:|---|---|---:|---:|
| 1,000 | api 198.6, broker 672.8, consumer 225.8, dashboard 258.4, mongo 529.0 | api 9.18, broker 5.88, consumer 0.09, dashboard 1.51, mongo 1.86 | 4,638,654 | 241,664 |
| 10,000 | api 80.2, broker 450.8, consumer 232.0, dashboard 337.3, mongo 237.9 | api 4.80, broker 8.85, consumer 6.69, dashboard 5.06, mongo 5.74 | 5,271,051 | 3,026,944 |
| 100,000 | api 90.0, broker 599.3, consumer 293.3, dashboard 1367.7, mongo 480.9 | api 30.05, broker 38.85, consumer 34.55, dashboard 105.32, mongo 55.98 | 14,169,419 | 48,668,672 |

¹ Memoria total cargada al cgroup desde `memory.current`, con caché incluida. El máximo es el mayor valor muestreado. La CPU se obtiene de diferencias positivas de `cpu.stat/usage_usec` entre muestras del mismo contenedor. Los intervalos de indisponibilidad constan en resources.json. Mongo mide el almacenamiento acumulado de la base de demostración. Se conserva una medición por escala y un único nodo con réplica uno. [SIN_DATOS] Escalabilidad entre nodos, alta disponibilidad y variación entre repeticiones.

## Recuperación y replay

En run-04-1000a, el rezago pasó de 0 a 500 offsets durante la pausa, y a 0 tras 16.30 s desde la orden de arranque. El replay independiente salió con código 86 al inyectar una caída entre persistencia y commit. Se releyeron 500 posiciones. Coincidieron el corpus, las restricciones, los resultados y las cantidades por tabla en 14 tablas. Con Kafka detenido, HTTP respondió 503. Sin Mongo, 30 eventos quedaron pendientes sin adelantar el commit. Al reabrir los servicios persistieron 950 eventos canónicos en la primera corrida.

## Trazabilidad

| Corrida | Corte exportado | SHA-256 lógico de los resultados |
|---|---|---|
| `run-04-1000a` | `4f48fd191f63018895284202` | `cbb6761349fdc513968ec041a4b62bc980aa9ac24081d90d12341741225402d6` |
| `run-04-10000a` | `0b28e4636c07a28b8505e847` | `3464944fe711c1f1359dfadce2e46021ef4f2eaacf1246fbdbee5ddeacb80c53` |
| `run-04-100000a` | `d0d0c103c2c610332488cbeb` | `c7d92fb77a25bfbd8aa1a4e38bc9f756a998deac09225765269603369223eda8` |

Los manifiestos completos están bajo `.bigdata-private/bigdata04/exports/<corrida>/<corte>/manifest.json`. Las fases y los recursos pueden cotejarse en `benchmarks/<corrida>/{result,environment,resources}.json`. El laboratorio ejecutó el perfil Docker offline. La construcción mediante descargas del Dockerfile portátil queda sin verificar. [Agregados usados por el cuaderno](measurements.json) · Protocolo de reproducción ([ruta `scripts/academic/bigdata04/README.md` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)).
