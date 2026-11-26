# Instalación y reproducción

Extraiga el ZIP completo y abra una terminal en la carpeta que contiene `LEEME.md`. Los ejemplos de terminal siguientes usan Bash en Linux o Ubuntu WSL2. Desde PowerShell se abre Ubuntu mediante `wsl.exe -d Ubuntu-24.04`. Docker Engine, Docker Compose v2 o posterior con `--wait` y Python 3 son requisitos del host. Los scripts de medición usan las interfaces de Linux, como `/proc` y los cgroups del contenedor.

## Perfil offline WSL2 ya ensayado

Requiere Ubuntu 24.04 x86-64, las imágenes locales `apache/kafka:4.3.1` y `mongo:8.0.16`, y un entorno compatible con Python 3.12. La lista de versiones está en [dependencias del perfil](DEPENDENCIAS.md). Defina `BIGDATA04_SITE_PACKAGES` con la ruta Linux del entorno ya instalado. Compose monta esa ruta y las bibliotecas del host en modo lectura. El perfil offline reutiliza una instalación previa.

```bash
B=scripts/academic/bigdata04
export BIGDATA04_SITE_PACKAGES=/ruta/real/al/entorno/lib/python3.12/site-packages
docker compose -f "$B/compose.yaml" -f "$B/compose.wsl.yaml" \
  up -d --no-build --pull never --wait --wait-timeout 180
dc() { docker compose -f "$B/compose.yaml" -f "$B/compose.wsl.yaml" "$@"; }
PROFILE=--offline
```

## Perfil Docker portátil

En un equipo con Docker Engine o Docker Desktop en modo de contenedores Linux, la imagen de aplicación se genera desde el Dockerfile. La construcción requiere acceso al registro de Docker, repositorios de Ubuntu y PyPI. La instalación desde cero sigue pendiente de validación. Use los comandos de Bash en Linux o WSL con integración Docker.

```bash
B=scripts/academic/bigdata04
docker compose -f "$B/compose.yaml" up -d --build --wait --wait-timeout 180
dc() { docker compose -f "$B/compose.yaml" "$@"; }
PROFILE=
```

Los comandos estándar usan el nombre `slp-bigdata04` y los puertos locales 18404 y 18504, esperados por los scripts de medición y recuperación. Ejecútelos en un equipo donde esos recursos estén libres. El ensayo aislado del expediente empleó otro nombre de proyecto y eliminó las publicaciones de puerto mediante un archivo Compose adicional. Los dos inicializadores del stack, `broker-storage` y `topics`, deben terminar satisfactoriamente.

## Verificar y generar un escenario nuevo

```bash
dc ps
curl -i http://127.0.0.1:18404/health
RUN="run-profesor-$(date +%s)"
python3 "$B/showcase.py" ${PROFILE:+$PROFILE} --run "$RUN" --stage initial
# Observe el corte inicial en el dashboard y luego aplique el cambio de cupo.
python3 "$B/showcase.py" ${PROFILE:+$PROFILE} --run "$RUN" --stage change
dc exec -T api python lag.py
dc exec -T -e CRM_TEST_MONGO_URI=mongodb://mongo:27017 \
  api python -m unittest -v test_pipeline test_reducer
```

Abra [el dashboard local](http://127.0.0.1:18504/) y seleccione `$RUN`. El guion inicial genera 19 eventos canónicos y siete impresiones con clic entre nueve elegibles. El segundo lote incluye un duplicado y deja 22 canónicos. Aquismón pasa de candidato a pausa y conserva las dos revisiones. Cualquier destino sin revisión figura como `sin_datos`. Para seguir el ejemplo del estudiante, observe Real de Catorce (A01).

## Probar la recuperación y el replay

```bash
REC="run-recuperacion-$(date +%s)"
python3 "$B/benchmark.py" ${PROFILE:+$PROFILE} --run "$REC" --count 1000 --recovery
python3 "$B/drills.py" ${PROFILE:+$PROFILE} --run "$REC"
```

El benchmark pausa y reinicia el consumidor. El segundo comando ensaya replay y reinicia brevemente Kafka y MongoDB del laboratorio. Utilice una instalación dedicada para estos ensayos. Consulte `result.json` y `drills.json` en `.bigdata-private/bigdata04/benchmarks/$REC/` y compruebe que el rezago final sea cero. La duración depende del equipo. Detenga los servicios con `dc stop` para conservar los volúmenes.

## Verificar un corte entregado

```bash
dc exec -T api python export.py --verify \
  /results/exports/run-04-1000a/4f48fd191f63018895284202/manifest.json
dc exec -T api python audit.py \
  /results/exports/run-04-1000a/4f48fd191f63018895284202/manifest.json \
  /results/exports/run-04-10000a/0b28e4636c07a28b8505e847/manifest.json \
  /results/exports/run-04-100000a/d0d0c103c2c610332488cbeb/manifest.json
```

En Colab, ejecute todas las celdas del cuaderno. Para comprobar un corte Parquet, suba una copia de su carpeta completa al directorio de trabajo de esa sesión y nómbrela `export/`. El cuaderno coteja huellas y cardinalidades con las corridas embebidas. El HTML permite revisar el código, las ocho gráficas y las seis tablas sin ejecutar Python. El análisis histórico del repositorio de origen es contextual y el ensayo distribuido se realiza sin `--historical`.
