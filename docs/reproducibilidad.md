# Reproducción del experimento original

El modo B usa los archivos autorizados del corte de adquisición del 22 de septiembre de 2026. El procedimiento se puede ejecutar desde una carpeta independiente. La lógica adaptada se distingue del código histórico que se conserva como referencia, con su organización y supuestos documentados.

## Archivos de INAH

Coloca los dos CSV de visitas, los dos catálogos de recintos, los cuatro diccionarios y el Gold histórico en una carpeta privada. Las fuentes son los archivos de museos y zonas arqueológicas conservados en el corte. La versión actual de los portales puede tener meses y hashes distintos.

- `INAH_visitantes_museos_general.csv`, `INAH_visitantes_zonas_general.csv`
- `INAH_museos.csv`, `INAH_zonas_arqueologicas.csv`
- `diccionario_museos.csv`, `diccionario_zonas_arqueologicas.csv`
- `diccionario_visitantes_museos_general.csv`, `diccionario_visitantes_zonas_general.csv`
- `cultural_visits_monthly.parquet`

## Archivos de DataTur

Coloca los 31 ZIP `AAAA-MES_MM_Publico.zip` de enero de 2024 a julio de 2026 y las referencias `datatur_slp_city_monthly.parquet` y `hotel_center_monthly.parquet` en otra carpeta privada. El ETL usa el miembro XLSX mensual y preserva la procedencia de las hojas. Los Parquet son los del corte del expediente. [Monitoreo hotelero oficial](https://datatur.sectur.gob.mx/SitePages/hoteleria.aspx).

## Ejecución en Windows

Desde la raíz del paquete, después de configurar el entorno virtual descrito en el README:

```powershell
& $py -m src.repro original --inah-dir .bigdata-private/input-inah --datatur-dir .bigdata-private/input-datatur --output-dir .bigdata-private/corrida-a
& $py -m src.repro original --inah-dir .bigdata-private/input-inah --datatur-dir .bigdata-private/input-datatur --output-dir .bigdata-private/corrida-b
& $py -m src.repro verify --first .bigdata-private/corrida-a --second .bigdata-private/corrida-b
```

Las rutas de entrada son configurables. Se valida su identidad antes de procesar. Si una fuente cambió o falta, se informa qué archivo impide reproducir el corte. El modo A no requiere esos archivos.

## Comprobación

Revisa `inah/quality.json`, `warehouse/quality.json`, los manifiestos y los CSV de consultas. El cotejo histórico compara valores y claves en ambos sentidos. El verificador compara por separado las representaciones lógicas y binarias de los productos.

El inventario de entrada y los valores de comparación se encuentran en `src/snapshot-manifest.json`. Para revisar los programas en su forma histórica, consulta `src/bigdata02/` y `src/bigdata03/`. El punto de entrada para una carpeta independiente es `src/repro.py`. Conserva las transformaciones originales y suministra desde el exterior la configuración, el catálogo mínimo de huellas y la zona de salida. Para comparar el hash del JSON histórico generado en Windows se usa su representación CRLF canónica para ese cotejo. Los binarios se comparan por separado.

El entorno original usó Python 3.12.14, DuckDB 1.4.1 y openpyxl 3.1.5. Resultados de rendimiento, huellas de bases físicas y recursos pueden variar por equipo y runtime. Las métricas históricas del banco se interpretan según sus escalas y protocolo. [Resultados](resultados_verificados.md).
