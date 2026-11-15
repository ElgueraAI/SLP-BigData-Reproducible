"""Measure 10,000 and 100,000 fictitious events, isolated from INAH."""

import argparse
import csv
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import platform
from time import perf_counter, process_time


spec = importlib.util.spec_from_file_location("cultural_visits", Path(__file__).with_name("profile-cultural-visits.py"))
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)
SEED = "slp-bench-v1:20261114"
EPOCH = datetime(2025, 1, 1, tzinfo=timezone.utc)
KINDS = ("destination_view", "campaign_click", "planning_start", "region_select", "route_query", "content_interaction")
CHANNELS = ("search", "social", "email", "referral")
FIELDS = ("event_id", "event_time", "event_type", "destination_id", "municipality_id", "campaign_id",
          "channel", "synthetic_flag", "source_type", "schema_version", "arrival_time")
QUERY = {
    "Q1": """SELECT count(*) FROM events WHERE event_time >= TIMESTAMPTZ '2025-01-01 00:00:00+00'
             AND event_time < TIMESTAMPTZ '2025-02-01 00:00:00+00' AND destination_id='synthetic-dest-000'""",
    "Q2": """SELECT cast(event_time AS DATE) AS day, municipality_id, campaign_id, channel, event_type, count(*)
             FROM events GROUP BY ALL ORDER BY ALL""",
    "Q3": """SELECT coalesce(d.region_id,'unresolved') AS region_id, count(*) AS events,
             count(*) FILTER (WHERE d.destination_id IS NULL) AS unresolved
             FROM events e LEFT JOIN dimensions d USING(destination_id,municipality_id)
             GROUP BY ALL ORDER BY ALL""",
}


def choice(index, key, modulus):
    data = sha256(f"{SEED}:{index}:{key}".encode()).digest()
    return int.from_bytes(data[:8], "big") % modulus


def events(index):
    municipality = choice(index, "municipality", 58)
    candidates = range(municipality, 174, 58)
    destination = candidates[choice(index, "destination", len(candidates))]
    moment = EPOCH + timedelta(seconds=choice(index, "time", 7776000))
    return (f"synthetic-event-{index:06}", moment.isoformat(), KINDS[choice(index, "type", len(KINDS))],
            f"synthetic-dest-{destination:03}", f"synthetic-mun-{municipality:02}",
            f"synthetic-campaign-{choice(index, 'campaign', 6):02}", CHANNELS[choice(index, "channel", len(CHANNELS))],
            True, "synthetic", "1.0.0", moment.isoformat())


def generate(folder, size):
    with (folder / "events.csv").open("w", encoding="utf-8", newline="") as main, (
        folder / "replay.csv"
    ).open("w", encoding="utf-8", newline="") as replay:
        original, recover = (csv.writer(stream, lineterminator="\n") for stream in (main, replay))
        original.writerow(FIELDS)
        recover.writerow(FIELDS)
        for index in range(size):
            record = events(index)
            original.writerow(record)
            if index % 100 == 0:
                recover.writerow(record)
            arrival = datetime.fromisoformat(record[-1])
            if index % 100 == 1:
                arrival += timedelta(days=1)
            recover.writerow((*record[:-1], arrival.isoformat()))


def digest_rows(cursor):
    return sha256(json.dumps(cursor.fetchall(), default=str, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def event_digest(db, table):
    return digest_rows(db.execute(f"""SELECT * EXCLUDE(event_time,arrival_time),
        epoch_us(event_time) AS event_time_us FROM {table} ORDER BY event_id"""))


def run(size, folder, duckdb):
    folder.mkdir(exist_ok=False)
    start, cpu = perf_counter(), process_time()
    generate(folder, size)
    generated = perf_counter()
    with duckdb.connect(config={"threads": 2}) as db:
        db.execute("SET TimeZone='UTC'")
        csv_type = """types={'event_time':'TIMESTAMPTZ','arrival_time':'TIMESTAMPTZ',
                      'synthetic_flag':'BOOLEAN','schema_version':'VARCHAR'}"""
        event_csv, replay_csv = (pipeline.literal(folder / name) for name in ("events.csv", "replay.csv"))
        db.execute(f"CREATE TABLE events AS SELECT * FROM read_csv({event_csv},{csv_type})")
        db.execute("""CREATE TABLE dimensions AS
            SELECT printf('synthetic-dest-%03d', i) destination_id,
                   printf('synthetic-mun-%02d', i%58) municipality_id,
                   printf('synthetic-region-%d',i%58%4) region_id FROM range(174) t(i)""")
        ingested = perf_counter()
        db.execute(f"""COPY (SELECT * FROM events ORDER BY event_id)
            TO {pipeline.literal(folder / "events.parquet")} (FORMAT PARQUET, COMPRESSION ZSTD)""")
        parquet_written = perf_counter()
        verification = db.execute("SELECT count(*),count(*) FILTER(WHERE synthetic_flag AND source_type='synthetic') FROM events").fetchone()
        if verification != (size, size):
            raise ValueError("Conservación y marca sintética incumplidas")
        base = event_digest(db, "events")
        stamps = {}
        for key, query in QUERY.items():
            durations = []
            hash_value = None
            for _ in range(3):
                tick = perf_counter()
                value = digest_rows(db.execute(query))
                durations.append(perf_counter() - tick)
                if hash_value is not None and hash_value != value:
                    raise ValueError(f"Resultado inconsistente: {key}")
                hash_value = value
            stamps[key] = {"seconds": durations, "sha256": hash_value}
        event_read = perf_counter()
        db.execute(f"CREATE TABLE recovery AS SELECT * FROM read_csv({replay_csv},{csv_type})")
        db.execute(f"INSERT INTO recovery SELECT * FROM read_csv({replay_csv},{csv_type})")
        db.execute("""CREATE TABLE deduplicated AS SELECT * FROM recovery
            QUALIFY row_number() OVER (PARTITION BY event_id ORDER BY arrival_time DESC)=1""")
        seen, once, delayed, unresolved = db.execute("""SELECT (SELECT count(*) FROM recovery),
            count(*),count(*) FILTER(WHERE arrival_time > event_time),
            count(*) FILTER(WHERE d.destination_id IS NULL)
            FROM deduplicated LEFT JOIN dimensions d USING(destination_id,municipality_id)""").fetchone()
        restored = event_digest(db, "deduplicated")
        if once != size or delayed != size//100 or unresolved or base != restored:
            raise ValueError("La recuperación y reingesta no conservan el historial lógico")
    elapsed = perf_counter() - start
    pipeline.dump(folder / "benchmark.json", {
        "classification": "[SIMULADO]", "rows": size, "seed": SEED, "runtime": platform.python_version(),
        "duckdb": duckdb.__version__, "generation_s": generated-start, "ingestion_s": ingested-generated,
        "rows_per_s_ingestion": size/(ingested-generated), "parquet_write_s": parquet_written-ingested,
        "recovery_s": perf_counter()-event_read, "elapsed_s": elapsed, "process_cpu_s": process_time()-cpu,
        "peak_rss_bytes": pipeline.peak_rss_bytes(), "peak_rss_scope": "proceso de ambos escalones",
        "csv_bytes": (folder/"events.csv").stat().st_size, "parquet_bytes": (folder/"events.parquet").stat().st_size,
        "queries": stamps, "duplicated_intake_rows": seen-once, "recovered_late_rows": delayed,
        "recovered_rows": once, "initial_sha256": base, "recovered_sha256": restored,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    import duckdb
    out = pipeline.private_path(args.output_dir)
    out.mkdir(parents=True, exist_ok=False)
    for size in (10000, 100000):
        run(size, out / str(size), duckdb)


if __name__ == "__main__":
    main()
