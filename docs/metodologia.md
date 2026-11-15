# Metodología de preparación y consulta

## INAH

Los CSV originales presentan meses en columnas y separan entradas nacionales y extranjeras. El ETL conserva cada fila de origen, filtra San Luis Potosí y normaliza los pares a una fila por recinto y mes. La clave incluye el tipo de recinto. Los totales requieren los dos conteos. Cero es una observación informada. El valor ausente permanece nulo. Las filas conflictivas se retienen para revisión.

## DataTur

Se verifica el ZIP de la edición. Se conservan encabezados, filas, rangos y hojas auxiliares. La hoja mensual se valida contra los días civiles del mes y sus tres años comparativos. Silver retiene cada lectura con su edición. Gold selecciona las observaciones contemporáneas. Las hojas acumuladas y auxiliares se conservan en Bronze. Una tasa válida satisface el dominio 0–100 y se concilia con 100 × ocupados / disponibles para el mismo centro y periodo, con tolerancia de 0,1 puntos porcentuales en el ETL histórico.

## Control experimental

El calendario se consulta por ventana, grano y unidad. El cotejo simétrico con el histórico, los hashes lógicos y los hashes binarios se comprueban por separado. Los dos experimentos de eventos emplean identificadores ficticios y una semilla reproducible. Los resultados de calidad histórica y los resultados de demostración tienen universos distintos.

## Fuentes documentales

- [Visitantes a museos abiertos al público, INAH](https://www.datos.inah.gob.mx/datos-abiertos/visitantes-museos)
- [Visitantes a zonas arqueológicas, INAH](https://www.datos.inah.gob.mx/datos-abiertos/visitantes-zonas-arqueologicas)
- [Monitoreo hotelero mensual, DataTur](https://datatur.sectur.gob.mx/SitePages/hoteleria.aspx)
- [Síntesis metodológica, DataTur](https://datatur.sectur.gob.mx/documentoscompartidos/monitoreo/ACTHOT_SintesisMetodologica.pdf)
