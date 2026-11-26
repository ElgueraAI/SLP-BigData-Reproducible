# Demostración de cinco minutos en Windows

**ENTORNO ACADÉMICO — DATOS SINTÉTICOS.** Preparar el stack desde la raíz del proyecto con el README de instalación ([ruta `scripts/academic/bigdata04/README.md` dentro del ZIP](../UCA01_BigData04_Kappa_CRM_SLP_Reproducible.zip)). Reservar cinco minutos de exposición una vez que Kafka, MongoDB, la API, el consumidor y el tablero estén listos. Los grupos, las bases de replay y los volúmenes de experimentos previos se conservan.

### 0:00 a 0:40 · Servicios y recorrido

Mostrar el [diagrama de arquitectura](bigdata04-arquitectura.md). Identificar el origen en el simulador, la posición en el broker y la escritura del consumidor antes del commit. Ejecutar en PowerShell desde la raíz de la rama de trabajo.

```powershell
$base = 'scripts/academic/bigdata04'
$stack = @('-d','Ubuntu-24.04','--exec','docker','compose','-f',"$base/compose.yaml",'-f',"$base/compose.wsl.yaml")
$p = @('-d','Ubuntu-24.04','--exec','/usr/bin/python3','-B')
$run = 'run-demo-' + (Get-Date -Format yyyyMMddHHmmss)
wsl.exe @stack ps
Invoke-RestMethod http://127.0.0.1:18404/health
Start-Process http://127.0.0.1:18504/
```

### 0:40 a 1:40 · Primera exposición

```powershell
wsl.exe @p "$base/showcase.py" --offline --run $run --stage initial
wsl.exe @stack exec -T api python lag.py
```

Seleccionar la corrida en el tablero. El acuse muestra tópico, partición y offset. En «Inteligencia publicitaria» hay nueve impresiones elegibles y siete con clic. En «Sustentabilidad», Xilitla (H07) registra siete clics y diez de diez plazas reservadas. Aquismón (H06) dispone de seis plazas simuladas. El primero queda en pausa y el segundo requiere revisión humana. Inspeccionar también un destino sin información operativa.

### 1:40 a 2:45 · Cambio de capacidad, duplicado y bajas

```powershell
wsl.exe @p "$base/showcase.py" --offline --run $run --stage change
wsl.exe @stack exec -T -e "AUDIT_RUN=$run" mongo mongosh --quiet --eval 'printjson(db.getSiblingDB("slp_bigdata04_demo").events.countDocuments({simulation_run_id:process.env.AUDIT_RUN}))'
```

Observar el cambio sin recargar la página. La primera impresión llega otra vez con el mismo identificador. La cuenta de impresiones elegibles permanece en nueve. En Mi Ruta quedan dos altas, una baja y una parada activa. El favorito retirado y vuelto a guardar queda activo. La revisión D cambia el cupo total de Aquismón a cuatro, con cuatro plazas reservadas. El historial conserva ambas decisiones y la razón de la pausa.

### 2:45 a 4:00 · Recuperación real

```powershell
$recovery = 'run-clase-' + (Get-Date -Format yyyyMMddHHmmss)
wsl.exe @p "$base/benchmark.py" --offline --historical --run $recovery --count 1000 --recovery
$r = Get-Content ".bigdata-private/bigdata04/benchmarks/$recovery/result.json" -Raw | ConvertFrom-Json
$r.recovery
```

El comando espera la persistencia de un prefijo, detiene el consumidor, continúa la publicación y lo reinicia con el mismo grupo. Mostrar las posiciones `before`, `during` y `after`, así como los segundos observados. En una computadora más lenta, mostrar el expediente de la corrida ya ejecutada mientras termina la nueva.

### 4:00 a 5:00 · Rendimiento y decisión publicitaria

Abrir la [tabla de resultados verificados](BIGDATA04_RESULTADOS_VERIFICADOS.md) y el [cuaderno ejecutado](../UCA01_BigData04_Kappa_CRM_SLP.ipynb). Comparar los percentiles físicos de persistencia con la tasa de eventos únicos. Explicar al grupo qué permite estudiar un clic atribuible y por qué la comprobación operativa precede a una propuesta de pauta. Para cerrar usar `wsl.exe @stack stop` si se desea detener los servicios.
