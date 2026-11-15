# Flujo analítico

```mermaid
flowchart LR
    I["INAH · CSV"] --> IR["Raw · SHA-256"]
    D["DataTur · ZIP, XLSX y PDF"] --> DR["Raw · SHA-256"]
    IR --> IB["Bronze · fila y origen"]
    DR --> DB["Bronze · encabezado y hoja"]
    IB --> IS["Silver · recinto y mes"]
    DB --> DS["Silver · centro, mes y edición"]
    IS --> IG["Gold · entradas por recinto"]
    DS --> DG["Gold · ocupación del centro"]
    IG --> W["DuckDB · dimensiones y hechos"]
    DG --> W
    W --> C["Calendario · indicadores separados"]
    C --> Q["Consultas SQL y calidad"]
```

El diagrama representa las ejecuciones históricas de Big Data 02 y 03. La demostración utiliza entradas generadas [SIMULADO] y la misma lógica de transformación y consulta cuando se indica.
