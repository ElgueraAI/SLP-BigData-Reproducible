# Dependencias y versiones

| Componente | Versión / alcance |
|---|---|
| Apache Kafka | Imagen `apache/kafka:4.3.1`, KRaft local, un nodo y una réplica. |
| MongoDB | Imagen `mongo:8.0.16` con el cliente mongosh incluido. |
| Python | 3.12 en Ubuntu 24.04 x86-64 para el perfil offline y Python 3 para los scripts del host. |
| Dependencias de la aplicación | `tornado==6.5.10`, `confluent-kafka==2.15.1`, `duckdb==1.5.5`, `pyarrow==25.0.1`, `psutil==7.2.2`, `pandas==2.3.3`, según Dockerfile. |
| Cuaderno | Python 3, pandas, Matplotlib e IPython. PyArrow activa la comprobación opcional del Parquet. `nbformat` y `nbclient` se usan al construir o probar el cuaderno localmente. |
| Pruebas | Python `unittest`. Las tres pruebas de persistencia requieren el MongoDB y mongosh del laboratorio y la variable `CRM_TEST_MONGO_URI`. |
| Utilidades opcionales | `catalog.mjs` usa Node.js y el compilado Astro del repositorio de origen para regenerar `catalog.json`. La instantánea incluida permite iniciar el sistema. `check_dashboard.mjs` utiliza Playwright Core 1.63 y Edge desde Windows en el repositorio de origen. |

El perfil portable instala Python desde los repositorios Ubuntu de la imagen y obtiene los paquetes Python especificados. Las dependencias transitivas y los paquetes del sistema se resuelven al construir. Consulte [instalación](INSTALACION_Y_REPRODUCCION.md) para conocer las condiciones de cada perfil.
