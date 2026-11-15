"""Normalize the September 2026 INAH snapshot in a private DuckDB workspace."""

import argparse
import csv
from collections import Counter
from datetime import date
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import platform
import re
import sys
from time import perf_counter, process_time
import unicodedata


VERSION = "inah-medallion-v1.0.0"
EDITION = "drive-2026-09-22"
MONTHS = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
INPUTS = {
    "museo": "INAH_visitantes_museos_general.csv",
    "zona_arqueologica": "INAH_visitantes_zonas_general.csv",
}
KEYS = ("anio", "estado", "clave_siinah", "recinto")
MISSING = {"", "ND", "N/D", "N.A.", "N/A", "NA", "-", "—", "–", "S/D", "SD", "NULL"}


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def fold(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold().strip())
                   if unicodedata.category(c) != "Mn")


def measure(text):
    value = text.strip()
    if value.upper() in MISSING:
        return None
    if re.fullmatch(r"[0-9]+", value):
        return int(value)
    raise ValueError("conteo_no_entero_o_negativo")


def inclusive_months(start, end):
    return [date(k // 12, k % 12 + 1, 1)
            for k in range(start.year * 12 + start.month - 1, end.year * 12 + end.month)]


def load_csv(path):
    payload = path.read_bytes()
    encoding = "utf-8-sig" if payload.startswith(b"\xef\xbb\xbf") else "utf-8"
    reader = csv.DictReader(StringIO(payload.decode(encoding), newline=""))
    rows = list(reader)
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError(f"Encabezado vacío o con columnas repetidas: {path.name}")
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"Ancho de fila inválido: {path.name}")
    return rows, {"file": path.name, "bytes": len(payload), "sha256": sha256(payload).hexdigest(),
                  "encoding": encoding, "rows": len(rows), "columns": reader.fieldnames}


def curate(collections, months, edition):
    bronze, silver, quarantine = [], [], []
    metrics = {}
    site_names = {}
    expected_years = {period.year for period in months}
    for kind, rows in collections.items():
        filename = INPUTS[kind]
        expected_fields = set(KEYS) | {f"{m}_{part}" for m in MONTHS for part in ("nac", "ext")}
        if rows and set(rows[0]) != expected_fields:
            raise ValueError(f"El esquema ancho no coincide con el contrato: {filename}")
        candidates = []
        reasons = Counter()
        missing_markers = Counter()
        for index, row in enumerate(rows, start=1):
            bronze.append((kind, filename, index, edition, json.dumps(row, ensure_ascii=False)))
            if fold(row["estado"]) != "san luis potosi":
                reasons["fuera_de_slp"] += 1
                continue
            code = row["clave_siinah"].strip()
            name = row["recinto"].strip()
            year_text = row["anio"].strip()
            if not re.fullmatch(r"[0-9]{4}", year_text) or not 1 <= int(year_text) <= 9999 or not code or not name:
                quarantine.append((kind, filename, index, None, "identidad_o_anio_invalido", edition))
                reasons["identidad_o_anio_invalido"] += 1
                continue
            year = int(year_text)
            if year not in expected_years:
                reasons["fuera_de_periodo"] += 1
                continue
            candidates.append((index, year, code, name, row))
        by_key = Counter((year, code) for _, year, code, _, _ in candidates)
        for index, year, code, name, row in candidates:
            site_id = f"{kind}:{code}"
            if by_key[year, code] > 1:
                quarantine.append((kind, filename, index, None, "recinto_anio_duplicado", edition))
                reasons["recinto_anio_duplicado"] += 1
                continue
            site_names.setdefault(site_id, name)
            reasons["fuente_unica_en_periodo"] += 1
            for period in months:
                if period.year != year:
                    continue
                key = MONTHS[period.month - 1]
                fields = (row[key + "_nac"], row[key + "_ext"])
                try:
                    national, foreign = (measure(value) for value in fields)
                except ValueError as error:
                    quarantine.append((kind, filename, index, period, str(error), edition))
                    continue
                for value in fields:
                    if value.strip().upper() in MISSING:
                        missing_markers[value] += 1
                status = ("reported" if None not in (national, foreign)
                          else "missing_pair" if national is None and foreign is None else "partial_pair")
                total = national + foreign if status == "reported" else None
                silver.append((site_id, code, name, kind, "24", year, period.month, period,
                               national, foreign, total, status, filename, edition, index, VERSION))
        metrics[kind] = {"raw_rows": len(rows), "row_disposition": dict(reasons),
                         "exact_duplicate_excess_national": len(rows) - len({tuple(row.items()) for row in rows}),
                         "missing_markers_in_silver_cells": dict(missing_markers)}
        if sum(reasons.values()) != len(rows):
            raise ValueError("Conservación Raw → Bronze")
    sites = [(site_id, site_id.split(":", 1)[1], name, site_id.split(":", 1)[0])
             for site_id, name in sorted(site_names.items())]
    return bronze, silver, quarantine, sites, metrics


SQL_TYPES = {
    "bronze": "site_type VARCHAR, source_id VARCHAR, source_row INTEGER, source_version VARCHAR, original JSON",
    "silver": """site_id VARCHAR, site_code VARCHAR, site_name VARCHAR, site_type VARCHAR, state_code VARCHAR,
        year INTEGER, month INTEGER, period DATE, national_visits BIGINT, foreign_visits BIGINT, total_visits BIGINT,
        observation_status VARCHAR, source_id VARCHAR, source_version VARCHAR, source_row INTEGER, transform_version VARCHAR""",
    "quarantine": "site_type VARCHAR, source_id VARCHAR, source_row INTEGER, period DATE, reason VARCHAR, source_version VARCHAR",
    "sites": "site_id VARCHAR, site_code VARCHAR, site_name VARCHAR, site_type VARCHAR",
    "periods": "period DATE",
}


def insert(db, table, records):
    db.execute(f"CREATE TABLE {table} ({SQL_TYPES[table]})")
    if records:
        marks = ", ".join(["?"] * len(records[0]))
        db.executemany(f"INSERT INTO {table} VALUES ({marks})", records)


def literal(path):
    return "'" + str(path.resolve()).replace("'", "''") + "'"


def table_rows(db, sql, arguments=()):
    query = db.execute(sql, arguments)
    columns = [item[0] for item in query.description]
    return [dict(zip(columns, row)) for row in query.fetchall()]


def save_csv(path, db, sql):
    query = db.execute(sql)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow([field[0] for field in query.description])
        writer.writerows(query.fetchall())


def compare_history(db, path):
    if not path.is_file():
        db.execute("""CREATE TABLE history AS SELECT site_code, site_type, period, national_visits,
                   foreign_visits, total_visits FROM gold WHERE false""")
        return {"status": "SIN_DATOS", "file": path.name}
    db.execute(f"CREATE TABLE historical_raw AS SELECT * FROM read_parquet({literal(path)})")
    archive = {"file": path.name, "sha256": sha256(path.read_bytes()).hexdigest(),
               "bytes": path.stat().st_size}
    archive["schema"] = table_rows(db, "DESCRIBE historical_raw")
    archive["parquet_metadata"] = table_rows(db, """SELECT row_group_id, row_group_num_rows, compression,
        count(*) AS columns FROM parquet_metadata(?) GROUP BY ALL ORDER BY 1, 3""", [str(path)])
    cols = {row["column_name"] for row in archive["schema"]}
    expected = {"cve_siinah", "site_type", "period", "national_visitors", "foreign_visitors", "total_visitors"}
    if not expected <= cols:
        raise ValueError(f"Campos históricos no encontrados: {sorted(expected - cols)}")
    db.execute("""CREATE TABLE history AS SELECT trim(cast(cve_siinah AS VARCHAR)) AS site_code,
        CASE WHEN lower(site_type) LIKE '%mus%' THEN 'museo'
             WHEN lower(site_type) LIKE '%arq%' OR lower(site_type) LIKE '%arch%' OR lower(site_type) LIKE '%zon%'
               THEN 'zona_arqueologica' END AS site_type,
        CASE WHEN regexp_full_match(cast(period AS VARCHAR), '[0-9]{4}-[0-9]{2}')
             THEN try_cast(cast(period AS VARCHAR) || '-01' AS DATE)
             WHEN day(try_cast(period AS DATE))=1 THEN try_cast(period AS DATE) END AS period,
        national_visitors AS national_visits, foreign_visitors AS foreign_visits,
        total_visitors AS total_visits FROM historical_raw""")
    archive["summary"] = table_rows(db, """SELECT count(*) AS rows, min(period) AS min_period,
        max(period) AS max_period, count(DISTINCT (site_type,site_code)) AS sites,
        count(*) - count(DISTINCT (site_type,site_code,period)) AS duplicate_keys,
        count(*) FILTER(WHERE period IS NULL OR site_code IS NULL OR site_type IS NULL) AS null_key,
        count(*) FILTER(WHERE total_visits = 0) AS zeros,
        count(*) FILTER(WHERE national_visits = 0) AS zero_national,
        count(*) FILTER(WHERE foreign_visits = 0) AS zero_foreign,
        count(*) FILTER(WHERE least(national_visits,foreign_visits,total_visits) < 0) AS negative,
        count(*) FILTER(WHERE total_visits IS DISTINCT FROM national_visits+foreign_visits) AS inconsistent
        FROM history""")[0]
    archive["by_site"] = table_rows(db, """SELECT site_type,site_code,count(*) AS rows,
        count(DISTINCT period) AS months FROM history GROUP BY ALL ORDER BY 1,2""")
    archive["original_site_types"] = table_rows(db, "SELECT DISTINCT site_type FROM historical_raw ORDER BY 1")
    archive["nulls_by_field"] = {col: db.execute(
        f'SELECT count(*) FILTER(WHERE "{col.replace(chr(34), chr(34)*2)}" IS NULL) FROM historical_raw'
    ).fetchone()[0] for col in sorted(cols)}
    return archive


def private_path(value):
    root = (Path(__file__).resolve().parents[3] / ".bigdata-private").resolve()
    output = Path(value).resolve()
    if not output.is_relative_to(root) or output == root:
        raise ValueError("Se requiere una subcarpeta bajo .bigdata-private")
    return output


def peak_rss_bytes():
    if sys.platform == "win32":
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
        success = read_memory(handle(), ctypes.byref(data), data.cb)
        return data.PeakWorkingSetSize if success else None
    import resource
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss if sys.platform == "darwin" else rss * 1024


def normalize_only(out, bronze, silver, quarantine, metrics, files, settings, timing, cpu):
    exports = {"bronze": bronze, "silver": silver, "quarantine": quarantine}
    orders = {"bronze": (1, 2), "silver": (0, 7), "quarantine": (1, 2)}
    hashes = {}
    for name, rows in exports.items():
        path = out / (name + ".csv")
        fields = [column.strip().split()[0] for column in SQL_TYPES[name].split(",")]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(fields)
            writer.writerows(sorted(rows, key=lambda row: tuple(row[i] for i in orders[name])))
        hashes[path.name] = sha256(path.read_bytes()).hexdigest()
    for kind, record in metrics.items():
        members = [row for row in silver if row[3] == kind]
        record["silver_rows"] = len(members)
        record["states"] = dict(Counter(row[11] for row in members))
        record["observed_total_zeros"] = sum(row[10] == 0 for row in members)
        record["null_total"] = sum(row[10] is None for row in members)
    if len(silver) != len({(row[0], row[7], row[13]) for row in silver}):
        raise ValueError("Clave repetida en Silver")
    dump(out / "quality.json", {"bronze_rows": len(bronze), "silver_rows": len(silver),
                               "quarantined_items": len(quarantine), "sources": metrics})
    hashes["quality.json"] = sha256((out / "quality.json").read_bytes()).hexdigest()
    dump(out / "manifest.json", {"inputs": files, "logical_sha256": hashes, "mode": "normalize-only",
                                  "runtime": {"python": platform.python_version()}, **settings})
    elapsed = perf_counter() - timing[0]
    dump(out / "performance.json", {"total_s": elapsed, "read_csv_s": timing[2]-timing[1],
        "normalize_s": timing[3]-timing[2], "process_cpu_s": process_time()-cpu,
        "peak_rss_bytes": peak_rss_bytes(), "bronze_rows_per_s_total": len(bronze)/elapsed,
        "output_bytes": {f.name:f.stat().st_size for f in out.iterdir() if f.is_file()}})


def run(args):
    started, cpu_started = perf_counter(), process_time()
    if not args.normalize_only:
        import duckdb
    after_import = perf_counter()
    inputs, out = private_path(args.input_dir), private_path(args.output_dir)
    if inputs == out or out.is_relative_to(inputs) or inputs.is_relative_to(out):
        raise ValueError("Entradas y salidas requieren directorios independientes")
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if start.day != 1 or end.day != 1 or start > end:
        raise ValueError("El intervalo requiere inicios de mes ordenados")
    months = inclusive_months(start, end)
    collections, files = {}, []
    for kind, name in INPUTS.items():
        collections[kind], info = load_csv(inputs / name)
        files.append(info)
    for extra in sorted(inputs.glob("*.csv")):
        if extra.name not in INPUTS.values():
            _, info = load_csv(extra)
            files.append(info)
    settings = {"edition": args.edition, "transform": VERSION, "window": [start, end],
                "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    after_load = perf_counter()
    bronze, silver, quarantine, sites, metrics = curate(collections, months, args.edition)
    after_curate = perf_counter()
    out.mkdir(parents=True, exist_ok=False)
    if args.normalize_only:
        normalize_only(out, bronze, silver, quarantine, metrics, files, settings,
                       (started, after_import, after_load, after_curate), cpu_started)
        return
    with duckdb.connect(str(out / "inah.duckdb"), config={"threads": 2}) as db:
        db.begin()
        for table, rows in (("bronze", bronze), ("silver", silver), ("quarantine", quarantine), ("sites", sites),
                            ("periods", [(month,) for month in months])):
            insert(db, table, rows)
        db.commit()
        after_staging = perf_counter()
        db.execute("""CREATE TABLE gold AS
            SELECT s.site_id, s.site_code, coalesce(v.site_name,s.site_name) AS site_name, s.site_type,
              '24' AS state_code, year(p.period) AS year, month(p.period) AS month, p.period,
              v.national_visits, v.foreign_visits, v.total_visits,
              coalesce(v.observation_status,'no_source_row') AS observation_status,
              coalesce(v.observation_status = 'reported',false) AS valid_for_comparison, v.source_id,
              coalesce(v.source_version,?) AS source_version, v.source_row, ? AS transform_version,
              'Entradas a recintos INAH de SLP incluidos en el corte' AS coverage
            FROM sites s CROSS JOIN periods p LEFT JOIN silver v USING(site_id,period)""", [args.edition, VERSION])
        after_gold = perf_counter()
        historical = compare_history(db, inputs / "cultural_visits_monthly.parquet")
        dump(out / "historical-audit.json", historical)
        checks = table_rows(db, """SELECT
            (SELECT count(*) FROM bronze) AS bronze_rows,
            (SELECT count(*) FROM silver) AS silver_rows,
            (SELECT count(*) FROM quarantine) AS quarantined_items,
            count(*) AS gold_rows,
            count(*) FILTER(WHERE observation_status='reported') AS reported_months,
            count(*) FILTER(WHERE observation_status='no_source_row') AS no_source_rows,
            count(*) FILTER(WHERE observation_status='missing_pair') AS missing_pairs,
            count(*) FILTER(WHERE observation_status='partial_pair') AS partial_pairs,
            count(*) FILTER(WHERE coalesce(total_visits = 0,false)) AS observed_total_zeros,
            count(*) FILTER(WHERE national_visits IS NULL) AS null_national,
            count(*) FILTER(WHERE foreign_visits IS NULL) AS null_foreign,
            count(*) FILTER(WHERE total_visits IS NULL) AS null_total,
            count(*)-count(DISTINCT(site_id,period,source_version)) AS duplicate_keys,
            count(*) FILTER(WHERE state_code!='24' OR month NOT BETWEEN 1 AND 12
                OR period!=make_date(year,month,1) OR source_version!=?
                OR least(total_visits,national_visits,foreign_visits)<0
                OR total_visits IS DISTINCT FROM national_visits+foreign_visits) AS invalid_gold,
            (SELECT count(*) FROM silver s ANTI JOIN bronze b
              ON s.source_id=b.source_id AND s.source_row=b.source_row AND s.source_version=b.source_version) AS unlinked_raw,
            (SELECT count(*) FROM silver ANTI JOIN sites USING(site_id)) AS unlinked_sites
            FROM gold""", [args.edition])[0]
        for check in ("invalid_gold", "duplicate_keys", "unlinked_raw", "unlinked_sites"):
            if checks[check]:
                raise ValueError(f"Control incumplido {check}: {checks[check]}")
        if checks["gold_rows"] != len(sites) * len(months) or checks["bronze_rows"] != sum(len(x) for x in collections.values()):
            raise ValueError("Conservación de filas incumplida")
        for key, values in metrics.items():
            subset = table_rows(db, """SELECT count(*) AS calendar_months,
              count(source_row) AS silver_rows, count(total_visits) AS reported_months,
              count(*) FILTER(WHERE total_visits=0) AS observed_total_zeros,
              count(*) FILTER(WHERE total_visits IS NULL) AS null_total
              FROM gold WHERE site_type=?""", [key])[0]
            values.update(subset)
            values["quarantine_reasons"] = dict(Counter(row[4] for row in quarantine if row[0] == key))
        dump(out / "quality.json", {"totals": checks, "sources": metrics})
        for table, order in (("bronze","source_id,source_row"), ("silver","site_id,period"),
                             ("gold","site_id,period"), ("quarantine","source_id,source_row,period")):
            db.execute(f"COPY (SELECT * FROM {table} ORDER BY {order}) TO {literal(out / (table + '.parquet'))} (FORMAT PARQUET, COMPRESSION ZSTD)")
        sql_path = Path(__file__).with_name("queries.sql")
        sql = sql_path.read_text(encoding="utf-8")
        queries = re.findall(r"^-- (Q\d)\s*\n(.*?)(?=^-- Q\d\s*$|\Z)", sql, flags=re.M | re.S)
        if len(queries) != 7:
            raise ValueError("Se esperaban siete consultas en queries.sql")
        query_seconds = {}
        for name, statement in queries:
            query_start = perf_counter()
            save_csv(out / f"{name}.csv", db, statement)
            query_seconds[name] = perf_counter() - query_start
            if name in ("Q1", "Q5", "Q6"):
                plans = db.execute("EXPLAIN ANALYZE " + statement).fetchall()
                (out / f"{name}-plan.txt").write_text("\n".join(row[1] for row in plans), encoding="utf-8")
        save_csv(out / "gold-canonical.csv", db, "SELECT * FROM gold ORDER BY site_id,period")
        schema = {name: table_rows(db, f"DESCRIBE {name}") for name in ("bronze", "silver", "gold", "quarantine")}
    canonical = ["gold-canonical.csv", "quality.json", *(f"Q{index}.csv" for index in range(1, 8))]
    hashes = {f: sha256((out / f).read_bytes()).hexdigest() for f in canonical}
    dump(out / "manifest.json", {"inputs": files, "historical": historical, "logical_sha256": hashes,
                                 "binary_sha256": {f.name: sha256(f.read_bytes()).hexdigest() for f in out.glob("*.parquet")},
                                 "schemas": schema, **settings,
                                 "sql_sha256": sha256(sql_path.read_bytes()).hexdigest(),
                                 "runtime": {"python": platform.python_version(), "duckdb": duckdb.__version__}})
    elapsed = perf_counter() - started
    dump(out / "performance.json", {"runtime_import_s": after_import-started, "read_csv_s": after_load-after_import,
        "normalize_s": after_curate-after_load, "duckdb_stage_s": after_staging-after_curate,
        "generate_gold_s": after_gold-after_staging, "query_export_seconds": query_seconds, "total_s": elapsed,
        "process_cpu_s": process_time()-cpu_started, "peak_rss_bytes": peak_rss_bytes(),
        "bronze_rows_per_s_total": len(bronze)/elapsed, "host_cpu_count": os.cpu_count(),
        "os": platform.system(), "processor": platform.processor(), "duckdb_threads": 2,
        "output_bytes": {f.name: f.stat().st_size for f in out.iterdir() if f.is_file()}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2026-08-01")
    parser.add_argument("--edition", default=EDITION)
    parser.add_argument("--normalize-only", action="store_true",
                        help="Ejecutar sólo la preparación CSV Raw, Bronze, Silver y calidad sin DuckDB")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
