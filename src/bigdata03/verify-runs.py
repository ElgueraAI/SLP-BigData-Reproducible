"""Compare actual private products and logical results across independent runs."""
from argparse import ArgumentParser
from hashlib import sha256
import json
import duckdb

from pipeline import json_text, protected_path, sql_path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require_hash(path, digest):
    if sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f"Hash no reproducible: {path}")


def validate(folder, manifest):
    require_hash(folder / "quality.json", manifest["quality_sha256"])
    for name, metric in manifest["queries"].items():
        require_hash(folder / f"{name}.csv", metric["sha256"])
    for name, metric in manifest["products"].items():
        require_hash(folder / f"{name}.parquet", metric["parquet_sha256"])
    db_file = folder / "campaign.duckdb"
    with duckdb.connect(str(db_file), read_only=True) as db:
        for table, expected in (("fact_inah_visits_monthly", 420), ("fact_datatur_occupancy_monthly", 31)):
            actual = db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            parquet = sql_path(folder / f"{table}.parquet")
            left = f"SELECT * FROM {table}"
            right = f"SELECT * FROM read_parquet({parquet})"
            differences = db.execute(f"""SELECT
                (SELECT count(*) FROM ({left} EXCEPT ALL {right})),
                (SELECT count(*) FROM ({right} EXCEPT ALL {left}))""").fetchone()
            if actual != expected or differences != (0, 0):
                raise ValueError(f"Base y Parquet no concuerdan: {table} {actual} {differences}")


def compare(left, right):
    manifests = [read(folder / "manifest.json") for folder in (left, right)]
    for folder, manifest in zip((left, right), manifests, strict=True):
        validate(folder, manifest)
    a, b = manifests
    logical_match = (
        all(a[x] == b[x] for x in ("transform", "code", "quality_sha256", "queries", "inah"))
        and set(a["products"]) == set(b["products"])
        and all(a["products"][key]["canonical_sha256"] == b["products"][key]["canonical_sha256"]
                for key in a["products"])
    )
    if not logical_match:
        raise ValueError("Las corridas no son lógicamente reproducibles")
    binary_match = all(a["products"][key]["parquet_sha256"] == b["products"][key]["parquet_sha256"]
                       for key in a["products"])
    return {"logical_equal": logical_match, "parquet_binary_equal": binary_match,
            "products": len(a["products"]), "queries": len(a["queries"])}


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("first")
    parser.add_argument("second")
    args = parser.parse_args()
    print(json_text(compare(protected_path(args.first), protected_path(args.second))))
