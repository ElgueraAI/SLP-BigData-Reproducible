# Validación y seguridad de la distribución

Fecha de revisión: 14 de noviembre de 2026. Se utilizó Python 3.12.14, DuckDB 1.4.1 y openpyxl 3.1.5. La validación se realizó localmente. La ejecución en un runtime remoto de Colab queda pendiente.

| Control | Resultado |
|---|---|
| Notebooks | Se validó su estructura JSON y se ejecutaron en orden las celdas Python de cada uno de los seis archivos. Los notebooks de entrega conservan conteos de ejecución nulos y salidas vacías |
| Modo A | Nueve observaciones recinto-mes y dos observaciones hoteleras ficticias. Se conservaron un total nulo, ceros informados y un mes fuera de cobertura hotelera. Se ejecutaron y exportaron las ocho consultas |
| Reproducción histórica | 420 observaciones INAH y 31 DataTur. La comparación lógica y binaria de los productos Parquet coincidió con las referencias del expediente para ambos flujos |
| Benchmark didáctico | 1.000 eventos ficticios, 10 tardíos, 1.000 recuperados. El hash lógico antes y después de la reingesta coincidió |
| Pruebas automatizadas | Cuatro pruebas del paquete, incluida una que ejecuta 12 casos históricos de Python. La suite de integridad del proyecto original también pasó sus 11 casos |
| Código original | Las carpetas `src/bigdata02/` y `src/bigdata03/` conservan los archivos históricos byte a byte. El adaptador `src/repro.py` agrega preparación de rutas, controles de identidad y demostración |

## Controles de distribución

El ZIP se arma mediante una lista de carpetas y tipos de archivo admitidos. El manifiesto incluido solo contiene hashes, nombres, tamaños, metadatos de fuentes y resultados comparativos autorizados para la revisión académica. Los archivos de datos, la base privada, el contenido de reservas, los originales de Drive, el informe privado y las salidas de ejecución se excluyen del paquete. La revisión incluyó patrones de credenciales, enlaces privados y rutas de usuario.

`.gitignore` separa entradas y salidas privadas, entornos y cachés. El ZIP tiene una sola carpeta raíz. La licencia del código sigue pendiente de autorización y no se adjunta una licencia inventada. La revisión local no publica el repositorio ni cambia permisos en Drive.
