# San Luis Potosí · Big Data reproducible

Paquete académico para la UCA de Herramientas para el Almacenamiento de Grandes Volúmenes, Universidad Rosario Castellanos, semestre 2026-2. Reúne el trabajo de auditoría, preparación e integración del almacén analítico que sirve de evidencia para una campaña turística inteligente y sustentable.

Las fuentes estudiadas fueron las entradas a recintos del INAH y la actividad del centro hotelero monitoreado por DataTur. Python organiza Raw, Bronze, Silver y Gold, Parquet guarda los productos por columnas y DuckDB ejecuta las consultas de calendario y calidad. [Fuentes y metodología](docs/metodologia.md) · [Arquitectura](docs/arquitectura.md) · [Diagrama editable](figures/flujo.md).

## Big Data 04 — Arquitectura Kappa y CRM turístico

**Big Data 01–03** documenta el almacén histórico Medallion para preparar, almacenar e integrar las fuentes turísticas oficiales. **Big Data 04** incorpora una arquitectura Kappa que procesa continuamente los eventos sintéticos de un CRM turístico y registra decisiones de elegibilidad para una campaña.

| Objetivo | Acceso directo |
|---|---|
| **Ver resultados** | [Colab ejecutado](https://colab.research.google.com/drive/1fS4TH9e0PiOsWHfEhIpZRNRcSa1rA10J?usp=sharing) · [Notebook en GitHub](bigdata04-kappa-crm/UCA01_BigData04_Kappa_CRM_SLP.ipynb) · [Descargar HTML y abrirlo localmente](https://raw.githubusercontent.com/ElgueraAI/SLP-BigData-Reproducible/main/bigdata04-kappa-crm/UCA01_BigData04_Kappa_CRM_SLP.html) |
| **Consultar instrucciones** | [Guía PDF para el profesor](bigdata04-kappa-crm/LEEME_PROFESOR.pdf) · [Documentación técnica y límites](bigdata04-kappa-crm/README.md) · [Evidencia experimental](bigdata04-kappa-crm/evidencias/BIGDATA04_RESULTADOS_VERIFICADOS.md) |
| **Reproducir el sistema completo** | [Descargar ZIP](https://raw.githubusercontent.com/ElgueraAI/SLP-BigData-Reproducible/main/bigdata04-kappa-crm/UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip) · [Huellas SHA-256](bigdata04-kappa-crm/SHA256SUMS.txt) |

[![Abrir en Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1fS4TH9e0PiOsWHfEhIpZRNRcSa1rA10J?usp=sharing)

Colab reproduce el análisis y las ocho gráficas. El flujo Kafka–MongoDB se ejecuta en Docker. La extracción aislada se verificó con el perfil offline de WSL2. La instalación del perfil Docker portátil desde cero queda pendiente.

## Dos formas de ejecución

| Modo | Entrada | Finalidad |
|---|---|---|
| **A · Demostración** | Ejemplos autogenerados y etiquetados [SIMULADO] | Ejecutar las transformaciones y consultas de muestra sin credenciales |
| **B · Experimento original** | Archivos autorizados del corte de septiembre de 2026 | Verificar SHA-256, reconstruir los hechos y cotejar los resultados históricos |

El ZIP distribuye código, notebooks, pruebas, metadatos de verificación y documentación. Las salidas generadas se escriben bajo `.bigdata-private/`. Las entradas originales y derivados del proyecto se entregan por separado cuando corresponda y exista autorización.

## Google Colab

1. Descomprime una copia local del ZIP para localizar los archivos `.ipynb`. Conserva el ZIP original con el nombre `SLP-BigData-Reproducible.zip`.
2. En [Google Colab](https://colab.research.google.com/), usa **Archivo → Subir notebook** y selecciona uno de los seis archivos.
3. Ejecuta la celda de preparación. Si el código no está en la sesión, selecciona el ZIP de distribución cuando la celda lo pida. Colab instala las dependencias fijadas si faltan.
4. Ejecuta las celdas restantes en orden. Se inicia en modo A. En modo B, configura las dos rutas de insumos y usa el servicio remoto solamente si esa transferencia está autorizada. El modo B también se ejecuta localmente.

Los archivos del entorno temporal de Colab y las dependencias se restablecen al iniciar una sesión nueva. El código y los resultados visibles de un notebook sí pueden compartirse con él. Los notebooks de distribución se entregan con celdas sin resultados guardados. [Preguntas frecuentes oficiales de Colab](https://research.google.com/colaboratory/faq.html).

| Notebook | Ejercicio |
|---|---|
| [01 · Arquitectura](notebooks/01_Arquitectura_Data_Lake.ipynb) | Capas, tablas y calendario |
| [02 · INAH](notebooks/02_ETL_INAH.ipynb) | CSV ancho, pivote, estados y linaje |
| [03 · DataTur](notebooks/03_ETL_DataTur.ipynb) | Lectura XLSX, edición y denominador |
| [04 · Consultas](notebooks/04_DuckDB_Consultas_SQL.ipynb) | Cobertura, claves y controles SQL |
| [05 · Calidad](notebooks/05_Calidad_y_Validacion.ipynb) | Nulos, ceros, duplicados y dos corridas |
| [06 · Benchmark](notebooks/06_Benchmark_Escalabilidad.ipynb) | 1.000 eventos ficticios y replay. Escalas mayores opcionales |

Después de publicar con autorización, cada URL de apertura se construye con la ruta real `https://colab.research.google.com/github/{propietario}/{repositorio}/blob/{rama}/notebooks/{archivo}.ipynb`. Los valores entre llaves son campos de configuración. [Ejemplo oficial de integración con GitHub](https://github.com/googlecolab/colabtools/blob/main/notebooks/colab-github-demo.ipynb).

## Visual Studio Code

Abre la carpeta descomprimida como proyecto y usa la terminal integrada. Python 3.12 reproduce el entorno histórico. Para notebooks selecciona el intérprete del entorno virtual. La interfaz de Jupyter usa `ipykernel` si la extensión lo solicita. Los scripts y pruebas usan las dependencias fijadas del paquete.

```powershell
python -m venv .venv
$py = '.venv/Scripts/python.exe'
& $py -m pip install -r requirements.txt
& $py -m src.repro demo --output-dir .bigdata-private/demo
& $py -m unittest discover -s tests -v
```

En macOS o Linux, sustituye el intérprete por `.venv/bin/python`. Abre `sql/` para revisar los scripts. Desde Python, una consulta de lectura se ejecuta así:

```python
from pathlib import Path
from src.repro import query

db = Path(".bigdata-private/demo/warehouse/campaign.duckdb")
print(query(db, "SELECT count(*) AS filas FROM fact_inah_visits_monthly"))
```

Usa directorios nuevos para cada corrida. [Procedimiento original, verificación y entradas](docs/reproducibilidad.md).

## Evidencia y límites

La ejecución original procesó 420 observaciones INAH y 31 DataTur. Los conteos se refieren a entradas de tres recintos y ocupación de un centro monitoreado. Los tamaños del benchmark representan eventos ficticios. Los resultados de demostración tienen sus propios denominadores. La campaña requiere verificar capacidad, operación, derechos y medición del piloto. [Resultados históricos](docs/resultados_verificados.md).

La carpeta está preparada para revisión y para inicializar un repositorio independiente si se autoriza su publicación. La licencia del código queda pendiente de decisión del titular. [Validación y seguridad](docs/validacion_seguridad.md).
