"""Compare execution and result delivery for Big Data 02's synthetic Q2."""

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from statistics import median
from time import perf_counter

import duckdb


def load_previous():
    path = Path(__file__).parents[1] / "bigdata02" / "benchmark.py"
    spec = importlib.util.spec_from_file_location("previous_benchmark", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def csv_digest(path):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        next(reader)
        records = [(*row[:-1], int(row[-1])) for row in reader]
    payload = json.dumps(records, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def run(source, output, previous):
    output.mkdir()
    query = previous.QUERY["Q2"]
    export = output / "q2.csv"
    with duckdb.connect(config={"threads": 2}) as db:
        db.execute("SET TimeZone='UTC'")
        db.execute("CREATE TABLE events AS SELECT * FROM read_parquet(?)", [str(source)])
        rows = db.execute("SELECT count(*) FROM events").fetchone()[0]
        variants = {
            "memory_python_hash": query,
            "parquet_python_hash": query.replace("FROM events", f"FROM read_parquet({previous.pipeline.literal(source)})"),
            "memory_python_csv": query,
            "memory_sql_csv": query,
        }
        results = {}
        reference = None
        for name, sql in variants.items():
            times, hashes = [], []
            profile = db.execute("EXPLAIN ANALYZE " + sql).fetchone()[1]
            (output / (name + "-plan.txt")).write_text(profile, encoding="utf-8")
            for _ in range(5):
                begin = perf_counter()
                if name == "memory_sql_csv":
                    db.execute(f"COPY ({sql}) TO {previous.pipeline.literal(export)} (FORMAT CSV, HEADER)")
                elif name == "memory_python_csv":
                    cursor = db.execute(sql)
                    rows_to_export = cursor.fetchall()
                    with export.open("w", encoding="utf-8", newline="") as stream:
                        writer = csv.writer(stream, lineterminator="\n")
                        writer.writerow([column[0] for column in cursor.description])
                        writer.writerows(rows_to_export)
                else:
                    hashes.append(previous.digest_rows(db.execute(sql)))
                times.append(perf_counter() - begin)
            if name.endswith("_csv"):
                hashes.append(csv_digest(export))
            if reference is None:
                reference = hashes[0]
            if any(value != reference for value in hashes):
                raise ValueError(f"Q2 result changed: {name}")
            results[name] = {"seconds": times, "median_seconds": median(times), "logical_sha256": reference}
        begin = perf_counter()
        cardinality = db.execute(f"SELECT count(*) FROM ({query})").fetchone()[0]
        check_elapsed = perf_counter() - begin
        result = {
            "evidence": "[SIMULADO]", "input_rows": rows, "output_groups": cardinality,
            "csv_bytes": export.stat().st_size, "input_parquet_bytes": source.stat().st_size,
            "engine": duckdb.__version__, "threads": 2, "variants": results,
            "count_only_seconds": check_elapsed, "process_peak_rss_bytes": previous.pipeline.peak_rss_bytes(),
        }
        (output / "profile.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    previous = load_previous()
    source, output = map(previous.pipeline.private_path, (args.input_dir, args.output_dir))
    output.mkdir(parents=True)
    for size in (10000, 100000):
        run(source / str(size) / "events.parquet", output / str(size), previous)


if __name__ == "__main__":
    main()
