"""Build a private, reproducible INAH/DataTur campaign warehouse."""
from argparse import ArgumentParser
from calendar import monthrange
from collections import Counter
from datetime import date
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from time import perf_counter, process_time
import json
import math
import platform
import re
import sys
import unicodedata
from zipfile import ZipFile

import duckdb
from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[3]
PRIVATE = ROOT / ".bigdata-private"
HERE = Path(__file__).resolve().parent
VERSION = "campaign-warehouse-v1.0.0"
CENTER = "datatur:slp-selected-hotel-center"
LABEL = "SAN LUIS POTOSI, S.L.P."
SCOPE = "SELECTED_HOTEL_CENTER_NOT_STATE"
MEASURE = "monthly_average_daily_rooms_preliminary"
MONTHS = ("enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre").split()
ARCHIVE = re.compile(r"(20\d{2})-MES_(\d{2})_Publico\.zip")
WINDOW = (date(2024, 1, 1), date(2026, 7, 1))
ROUNDING_TOLERANCE_PP = 0.1


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, allow_nan=False)


def save(path, value):
    path.write_text(json_text(value) + "\n", encoding="utf-8")


def protected_path(value):
    path = Path(value).resolve()
    if not path.is_relative_to(PRIVATE) or path == PRIVATE:
        raise ValueError("La ruta debe estar dentro de .bigdata-private")
    return path


def normalized(value):
    text = "" if value is None else str(value)
    return "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c)).strip().upper()


def dates(start, end):
    while start <= end:
        yield start
        start = date(start.year + (start.month == 12), start.month % 12 + 1, 1)


def read_sheet(sheet, edition):
    rows = sheet.iter_rows(max_col=21, values_only=True)
    header = [list(next(rows)) for _ in range(8)]
    title, period_text = normalized(header[1][2]), normalized(header[2][2])
    month = MONTHS[edition.month - 1].upper()
    last = monthrange(edition.year, edition.month)[1]
    expected_end = f"{last}-{month}-{edition.year}"
    if "ACUMULADO" in title or "ACUM" in normalized(sheet.title):
        scope = ("year_to_date" if re.fullmatch(fr"DEL 0?1-ENERO-{edition.year} AL {expected_end}", period_text)
                 else "auxiliary_unverified_window")
    elif re.fullmatch(fr"DEL 0?1-{month}-{edition.year} AL {expected_end}", period_text) and "MES DE" in title:
        scope = "monthly"
    else:
        raise ValueError(f"Hoja con temporalidad no reconocida: {sheet.title} / {header[2][2]}")
    if [normalized(header[5][i]) for i in (1, 2, 9, 16)] != [
        "CENTRO", "CUARTOS DISPONIBLES PROMEDIO DIARIO", "CUARTOS OCUPADOS", "OCUPACION"
    ]:
        raise ValueError(f"Encabezados de medida incompatibles: {sheet.title}")
    years = tuple(edition.year - n for n in (2, 1, 0))
    for anchor in (2, 9, 16):
        if tuple(str(header[6][anchor + i]).strip().rstrip("*").strip() for i in range(3)) != tuple(map(str, years)):
            raise ValueError(f"Edición o encabezados de año incompatibles: {sheet.title}")
    candidates = [(n, list(row)) for n, row in enumerate(rows, 9) if normalized(row[1]) == LABEL]
    if len(candidates) != 1:
        raise ValueError(f"{sheet.title}: se esperaba una fila de centro, hay {len(candidates)}")
    return scope, header, *candidates[0]


def reading(values):
    """Validate the reported three-cell measure without imputing."""
    numbers = []
    for value in values:
        if normalized(value).replace(".", "") in {"", "ND", "NC", "N/D", "N/C", "-"}:
            numbers.append(None)
        elif isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value):
            numbers.append(float(value))
        else:
            raise ValueError(f"Celda de medición no válida: {value!r}")
    available, occupied, rate = numbers
    if ((available is not None and available <= 0)
        or (occupied is not None and occupied < 0)
        or (occupied is not None and available is not None and occupied > available)
        or (rate is not None and not 0 <= rate <= 100)):
        raise ValueError(f"Denominadores o tasa fuera de dominio: {values!r}")
    if None in numbers:
        return *numbers, None, "source_missing"
    error = abs(rate - 100 * occupied / available)
    if error > ROUNDING_TOLERANCE_PP:
        raise ValueError(f"Tasa y denominadores no concuerdan: {values!r}, {error:.5f} pp")
    return *numbers, error, "reported"


def read_archive(path):
    match = ARCHIVE.fullmatch(path.name)
    if match is None:
        raise ValueError(f"Nombre de archivo inesperado: {path.name}")
    edition = date(*(int(x) for x in match.groups()), 1)
    source_id = f"DATATUR_MONITOR_{edition:%Y_%m}"
    records, candidates, retained = [], [], []
    with ZipFile(path) as archive:
        member = path.stem + ".xlsx"
        payload = archive.read(member)
        member_hash = sha256(payload).hexdigest()
        workbook = load_workbook(BytesIO(payload), read_only=True, data_only=True)
        try:
            for sheet in workbook:
                scope, header, line, row = read_sheet(sheet, edition)
                records.append((source_id, edition, path.name, member, member_hash, sheet.title, line,
                                scope, json_text(header), json_text(row)))
                if scope != "monthly":
                    continue
                for i, year in enumerate(range(edition.year - 2, edition.year + 1)):
                    cells = tuple(row[anchor + i] for anchor in (2, 9, 16))
                    period = date(year, edition.month, 1)
                    try:
                        available, occupied, rate, error, status = reading(cells)
                    except ValueError as exc:
                        retained.append((source_id, edition, period, sheet.title, line, json_text(cells), str(exc)))
                        continue
                    candidates.append((CENTER, LABEL, period, available, occupied, rate, error, status,
                                       source_id, edition, member, sheet.title, line, i == 2))
        finally:
            workbook.close()
    if sum(row[7] == "monthly" for row in records) != 1 or len(candidates) + len(retained) != 3:
        raise ValueError(f"Se esperaba una hoja mensual con tres añadas: {path.name}")
    return edition, records, candidates, retained


def query_rows(db, sql, params=()):
    result = db.execute(sql, params)
    names = [col[0] for col in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def sql_path(path):
    return "'" + str(path).replace("'", "''") + "'"


def write_table(db, name, schema, records):
    db.execute(f"CREATE TABLE {name} ({schema})")
    if records:
        slots = ",".join("?" for _ in records[0])
        db.executemany(f"INSERT INTO {name} VALUES ({slots})", records)


def audit_archives(inputs):
    cat = json.loads((ROOT / "docs/academic/uca-01-almacenamiento/bigdata-01-evidencia/drive-fuentes.json").read_text(encoding="utf-8"))
    expected = {Path(r[3]).name: r for r in cat["rows"] if r[3] and ARCHIVE.fullmatch(Path(r[3]).name)}
    raw, bronze, silver, quarantine, periods = [], [], [], [], []
    for path in sorted(inputs.glob("*-MES_*_Publico.zip")):
        row = expected.get(path.name)
        binary_hash = digest(path)
        if row is None or binary_hash != row[7] or path.stat().st_size != row[6]:
            raise ValueError(f"ZIP sin identidad verificada con el corte Drive: {path.name}")
        edition, archive_rows, normalized_rows, retained = read_archive(path)
        periods.append(edition)
        raw.append((row[0], edition, path.name, binary_hash, path.stat().st_size, row[8], row[9], row[13], row[16]))
        bronze.extend(archive_rows)
        silver.extend(normalized_rows)
        quarantine.extend(retained)
    if periods != list(dates(*WINDOW)):
        raise ValueError("Faltan, sobran o se repiten ediciones del corte DataTur")
    return raw, bronze, silver, quarantine


def compare_history(db, inputs):
    fields = ("period,year,month,tourism_center,municipality_name,geographic_scope,"
              "available_rooms_daily_avg,occupied_rooms_daily_avg,hotel_occupancy_percent,source_id,measure")
    db.execute(f"""CREATE VIEW comparable_datatur AS SELECT strftime(period,'%Y-%m') AS period,
        year(period)::BIGINT AS year, month(period)::BIGINT AS month, center_name AS tourism_center,
        'San Luis Potosí' AS municipality_name, geographic_scope,
        available_rooms_daily_avg,occupied_rooms_daily_avg,hotel_occupancy_percent,source_id,
        '{MEASURE}' AS measure FROM fact_datatur_occupancy_monthly""")
    results = {}
    for name in ("datatur_slp_city_monthly", "hotel_center_monthly"):
        path = inputs / f"{name}.parquet"
        db.execute(f"CREATE TEMP VIEW historical AS SELECT * FROM read_parquet({sql_path(path)})")
        count, keys, first, last = db.execute("SELECT count(*),count(DISTINCT period),min(period),max(period) FROM historical").fetchone()
        left = f"SELECT {fields} FROM comparable_datatur"
        right = f"SELECT {fields} FROM historical"
        extra, missing = db.execute(f"""SELECT
            (SELECT count(*) FROM ({left} EXCEPT ALL {right})),
            (SELECT count(*) FROM ({right} EXCEPT ALL {left}))""").fetchone()
        results[name] = {"rows": count, "distinct_periods": keys, "first": first, "last": last,
                         "new_only_or_changed": extra, "historical_only_or_changed": missing,
                         "sha256": digest(path), "bytes": path.stat().st_size,
                         "schema": query_rows(db, "DESCRIBE historical"),
                         "parquet": query_rows(db, "SELECT row_group_id,compression,count(*) AS columns FROM parquet_metadata(?) GROUP BY ALL ORDER BY 1,2", [str(path)])}
        db.execute("DROP VIEW historical")
        if keys != count or extra or missing:
            raise ValueError(f"El cotejo histórico de {name} no pasó: {extra=}, {missing=}, {keys=}, {count=}")
    return results


def import_inah(db, product):
    parquet, manifest = product / "gold.parquet", product / "manifest.json"
    info = json.loads(manifest.read_text(encoding="utf-8"))
    if digest(parquet) != info["binary_sha256"]["gold.parquet"]:
        raise ValueError("El Gold INAH no coincide con su manifiesto")
    db.execute(f"""CREATE TABLE fact_inah_visits_monthly AS SELECT
        *, 'registered_entries' AS unit, 'INAH_RECEPTION_SITE' AS geographic_scope
        FROM read_parquet({sql_path(parquet)})""")
    return {"sha256": digest(parquet), "manifest_sha256": digest(manifest), "bytes": parquet.stat().st_size}


def write_products(db, output):
    tables = {
        "raw_datatur_manifest": "edition", "bronze_datatur": "edition,sheet",
        "silver_datatur_vintages": "edition,period", "quarantine_datatur": "edition,period",
        "fact_datatur_occupancy_monthly": "period", "fact_inah_visits_monthly": "site_id,period",
        "dim_period": "period", "dim_entity": "entity_id", "dim_source": "source_id,source_version",
        "datatur_revisions": "period,comparison_edition", "campaign_calendar": "period",
    }
    hashes = {}
    for table, order in tables.items():
        query = f"SELECT * FROM {table} ORDER BY {order}"
        parquet = output / f"{table}.parquet"
        db.execute(f"COPY ({query}) TO {sql_path(parquet)} (FORMAT PARQUET, COMPRESSION ZSTD)")
        hashes[table] = {"canonical_sha256": sha256(json_text(query_rows(db, query)).encode()).hexdigest(),
                         "parquet_sha256": digest(parquet), "bytes": parquet.stat().st_size}
    return hashes


def peak_rss_bytes():
    if sys.platform != "win32":
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return rss if sys.platform == "darwin" else rss * 1024
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize",
            "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
            "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

    data = Counters()
    data.cb = ctypes.sizeof(data)
    handle = ctypes.windll.kernel32.GetCurrentProcess
    handle.restype = wintypes.HANDLE
    read_memory = ctypes.windll.psapi.GetProcessMemoryInfo
    read_memory.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    read_memory.restype = wintypes.BOOL
    return data.PeakWorkingSetSize if read_memory(handle(), ctypes.byref(data), data.cb) else None


def run(args):
    started, cpu = perf_counter(), process_time()
    inputs, inah, output = map(protected_path, (args.input_dir, args.inah_dir, args.output_dir))
    if output.is_relative_to(inputs) or output.is_relative_to(inah):
        raise ValueError("Las salidas deben estar separadas de las entradas")
    raw, bronze, silver, quarantine = audit_archives(inputs)
    extracted = perf_counter()
    output.mkdir(parents=True, exist_ok=False)
    with duckdb.connect(str(output / "campaign.duckdb"), config={"threads": 2}) as db:
        db.begin()
        write_table(db, "raw_datatur_manifest",
                    "source_id VARCHAR, edition DATE, archive VARCHAR, sha256 VARCHAR, bytes BIGINT, official_url VARCHAR, download_url VARCHAR, retrieved_at VARCHAR, rights VARCHAR", raw)
        write_table(db, "bronze_datatur",
                    "source_id VARCHAR, edition DATE, archive VARCHAR, member VARCHAR, member_sha256 VARCHAR, sheet VARCHAR, source_row INTEGER, window_kind VARCHAR, header JSON, cells JSON", bronze)
        write_table(db, "silver_datatur_vintages",
                    "center_id VARCHAR, center_name VARCHAR, period DATE, available_rooms_daily_avg DOUBLE, occupied_rooms_daily_avg DOUBLE, hotel_occupancy_percent DOUBLE, residual_pp DOUBLE, observation_status VARCHAR, source_id VARCHAR, edition DATE, member VARCHAR, sheet VARCHAR, source_row INTEGER, contemporary BOOLEAN", silver)
        write_table(db, "quarantine_datatur",
                    "source_id VARCHAR, edition DATE, period DATE, sheet VARCHAR, source_row INTEGER, cells JSON, reason VARCHAR", quarantine)
        inah_info = import_inah(db, inah)
        db.execute((HERE / "model.sql").read_text(encoding="utf-8"))
        db.commit()
        modeled = perf_counter()
        history = compare_history(db, inputs)
        checks = query_rows(db, (HERE / "quality.sql").read_text(encoding="utf-8"))[0]
        if (any(checks[name] for name in checks if name.startswith("fail_"))
            or len(raw) * 3 != len(silver) + len(quarantine)
            or checks["hotel_rows"] != len(raw)):
            raise ValueError(f"Falló calidad o conservación: {checks}")
        revisions = query_rows(db, """SELECT count(*) comparisons,
            count(*) FILTER(WHERE changed) changed,
            count(*) FILTER(WHERE abs(available_delta) > 1e-8) changed_available,
            count(*) FILTER(WHERE abs(occupied_delta) > 1e-8) changed_occupied,
            count(*) FILTER(WHERE abs(rate_delta_pp) > 1e-8) changed_rate,
            max(abs(rate_delta_pp)) max_abs_rate_delta_pp FROM datatur_revisions""")[0]
        quality = {"checks": checks, "raw_archives": len(raw), "raw_zip_bytes": sum(r[4] for r in raw),
                   "bronze_window_kinds": dict(Counter(r[7] for r in bronze)),
                   "silver_candidates": len(silver), "retained": len(quarantine),
                   "revision_pairs": revisions, "historical": history,
                   "rounding_tolerance_pp": ROUNDING_TOLERANCE_PP}
        save(output / "quality.json", quality)
        products = write_products(db, output)
        timings, queries = {}, {}
        script = (HERE / "queries.sql").read_text(encoding="utf-8")
        statements = re.findall(r"^-- (Q\d)\s*\n(.*?)(?=^-- Q\d\s*$|\Z)", script, re.M | re.S)
        if len(statements) != 8:
            raise ValueError("Se requieren ocho consultas")
        for name, statement in statements:
            start = perf_counter()
            rows = query_rows(db, statement)
            path = output / f"{name}.csv"
            db.execute(f"COPY ({statement.strip().rstrip(';')}) TO {sql_path(path)} (HEADER true)")
            timings[name] = perf_counter() - start
            queries[name] = {"rows": len(rows), "sha256": digest(path)}
    save(output / "manifest.json", {"transform": VERSION, "duckdb": duckdb.__version__,
         "python": platform.python_version(), "inah": inah_info, "products": products,
         "queries": queries, "quality_sha256": digest(output / "quality.json"),
         "code": {name: digest(HERE / name) for name in ("pipeline.py", "model.sql", "quality.sql", "queries.sql", "requirements.txt", "contract.json")}})
    save(output / "performance.json", {"extract_s": extracted-started, "model_s": modeled-extracted,
         "queries_export_s": timings, "total_s": perf_counter()-started, "cpu_s": process_time()-cpu,
         "peak_rss_bytes": peak_rss_bytes(), "duckdb_threads": 2,
         "system": platform.system(), "processor": platform.processor()})
    print(json_text({"quality": checks, "revision_pairs": revisions, "queries": queries}))


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default=".bigdata-private/datatur-inputs")
    parser.add_argument("--inah-dir", default=".bigdata-private/duckdb-run1")
    parser.add_argument("--output-dir", required=True)
    run(parser.parse_args())
