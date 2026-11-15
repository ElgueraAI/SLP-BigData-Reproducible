"""Adaptadores de distribución añadidos en la Misión Big Data 05."""

from argparse import ArgumentParser
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from shutil import copyfile
from types import SimpleNamespace

import duckdb


ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".bigdata-private"
HERE = Path(__file__).resolve().parent
PUBLIC_MANIFEST = HERE / "snapshot-manifest.json"


def module(mission, filename):
    path = HERE / mission / filename
    loader = importlib.util.spec_from_file_location(f"{mission}_{path.stem}", path)
    result = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(result)
    return result


def guard(path):
    resolved = Path(path).resolve()
    if resolved == PRIVATE or not resolved.is_relative_to(PRIVATE):
        raise ValueError("Usa una subcarpeta de .bigdata-private/ en la raíz de esta copia.")
    return resolved


def read_report(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def historical_json_digest(path):
    data = Path(path).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return sha256(data).hexdigest()


def query(db_path, statement):
    with duckdb.connect(str(guard(db_path)), read_only=True) as db:
        cursor = db.execute(statement)
        names = [d[0] for d in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]


def prepare_output(output_dir, inputs=()):
    target = guard(output_dir)
    if any(p == target or target.is_relative_to(p) or p.is_relative_to(target) for p in inputs):
        raise ValueError("Las carpetas de entrada y salida deben estar separadas.")
    target.mkdir(parents=True, exist_ok=False)
    return target


def inah_etl(inputs, out, start, end, edition):
    inah = module("bigdata02", "profile-cultural-visits.py")
    inah.private_path = guard
    inah.run(SimpleNamespace(input_dir=inputs, output_dir=out, start=start, end=end,
                             edition=edition, normalize_only=False))


def exact_snapshot_inputs(folder, expected):
    path = Path(folder).resolve()
    names = set(expected)
    missing = sorted(names - {entry.name for entry in path.iterdir()}) if path.is_dir() else sorted(names)
    if missing:
        raise ValueError("Faltan insumos autorizados en " + path.name + ": " + ", ".join(missing))
    extra_csv = sorted(p.name for p in path.glob("*.csv") if p.name not in names)
    if extra_csv and any(name.startswith("INAH_") for name in names):
        raise ValueError("Se detectaron CSV de edición no controlada: " + ", ".join(extra_csv))
    for name, meta in expected.items():
        resource = path / name
        if not resource.is_file() or resource.stat().st_size != meta["bytes"] or digest(resource) != meta["sha256"]:
            raise ValueError("El archivo no coincide con bytes y SHA-256 del corte original: " + name)
    return path


def projected_catalog(root, rows):
    """Present the restricted catalogue schema expected by the original runner."""
    folder = root / "docs/academic/uca-01-almacenamiento/bigdata-01-evidencia"
    folder.mkdir(parents=True)
    write_json(folder / "drive-fuentes.json", {"rows": rows})


def run_original(inah_dir, datatur_dir, output_dir):
    evidence = read_report(PUBLIC_MANIFEST)
    inah = exact_snapshot_inputs(inah_dir, evidence["inah"])
    datatur = exact_snapshot_inputs(datatur_dir, evidence["datatur"])
    out = prepare_output(output_dir, (inah, datatur))
    staged_inah, staged_datatur = out / "raw" / "inah", out / "raw" / "datatur"
    for source, destination, expected in ((inah, staged_inah, evidence["inah"]),
                                          (datatur, staged_datatur, evidence["datatur"])):
        destination.mkdir(parents=True)
        for name in expected:
            copyfile(source / name, destination / name)
        exact_snapshot_inputs(destination, expected)
    inah_etl(staged_inah, out / "inah", "2015-01-01", "2026-08-01", "drive-2026-09-22")
    adapter_root = out / "adapter_metadata"
    projected_catalog(adapter_root, evidence["datatur_catalogue"])
    ware = module("bigdata03", "pipeline.py")
    ware.ROOT, ware.PRIVATE = adapter_root, PRIVATE
    ware.run(SimpleNamespace(input_dir=staged_datatur, inah_dir=out / "inah", output_dir=out / "warehouse"))

    bd02 = read_report(out / "inah" / "manifest.json")
    bd03 = read_report(out / "warehouse" / "manifest.json")
    b2, b3 = evidence["expected"]["bigdata02"], evidence["expected"]["bigdata03"]
    b2_logical = dict(bd02["logical_sha256"], **{"quality.json": historical_json_digest(out / "inah" / "quality.json")})
    b2_match = b2_logical == b2["logical_sha256"]
    b3_match = (bd03["queries"] == b3["queries"] and historical_json_digest(out / "warehouse" / "quality.json") == b3["quality_sha256"]
                and {name: p["canonical_sha256"] for name, p in bd03["products"].items()} == b3["products"])
    binary = {"bigdata02": bd02["binary_sha256"] == b2["binary_sha256"],
              "bigdata03": {name: p["parquet_sha256"] for name, p in bd03["products"].items()} == b3["parquet"]}
    report = {"mode": "B", "classification": "[OBSERVADO/DERIVADO]",
              "quality_json_comparison": "CRLF para cotejar la representación del expediente Windows",
              "logical_equal": {"bigdata02": b2_match, "bigdata03": b3_match}, "parquet_binary_equal": binary}
    write_json(out / "comparison.json", report)
    if not (b2_match and b3_match):
        raise ValueError("La reproducción lógica difiere del expediente. Revisa comparison.json y el runtime.")
    return out


def run_demo(output_dir):
    from .demo_inputs import build_demo, configure_demo

    out = prepare_output(output_dir)
    inah_dir, datatur_dir = build_demo(out)
    inah_etl(inah_dir, out / "inah", "2025-01-01", "2025-03-01", "simulado-v1")
    ware = module("bigdata03", "pipeline.py")
    configure_demo(ware, out, datatur_dir)
    ware.run(SimpleNamespace(input_dir=datatur_dir, inah_dir=out / "inah", output_dir=out / "warehouse"))
    write_json(out / "comparison.json", {"mode": "A", "classification": "[SIMULADO]",
        "occupied_measure": "escenario ficticio", "comparison_with_original": "no aplicable"})
    return out


def run_benchmark(output_dir, rows=1000):
    if rows not in {1000, 10000, 100000}:
        raise ValueError("Escalas disponibles: 1000, 10000, 100000.")
    out = guard(output_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    benchmark = module("bigdata02", "benchmark.py")
    benchmark.pipeline.private_path = guard
    benchmark.run(rows, out, duckdb)
    return read_report(out / "benchmark.json")


def verify(first, second):
    left, right = guard(first), guard(second)
    reports = []
    for run in (left, right):
        meta = read_report(run / "comparison.json")
        inah = read_report(run / "inah" / "manifest.json")
        warehouse = read_report(run / "warehouse" / "manifest.json")
        output_paths = [(run / "inah" / name, value) for name, value in inah["logical_sha256"].items()]
        output_paths += [(run / "inah" / name, value) for name, value in inah["binary_sha256"].items()]
        output_paths += [(run / "warehouse" / f"{n}.parquet", v["parquet_sha256"]) for n,v in warehouse["products"].items()]
        output_paths += [(run / "warehouse" / f"{n}.csv", v["sha256"]) for n,v in warehouse["queries"].items()]
        output_paths += [(run / "warehouse" / "quality.json", warehouse["quality_sha256"])]
        if any(digest(path) != expected for path, expected in output_paths):
            raise ValueError("Un producto difiere de su manifiesto.")
        reports.append((meta["mode"], inah["logical_sha256"], warehouse["queries"],
                        warehouse["quality_sha256"], {n: v["canonical_sha256"] for n,v in warehouse["products"].items()}))
    if reports[0] != reports[1]:
        raise ValueError("Las corridas no son lógicamente comparables.")
    return {"logical_equal": True, "mode": reports[0][0], "queries": len(reports[0][2])}


def main():
    parser = ArgumentParser(description=__doc__)
    ops = parser.add_subparsers(dest="command", required=True)
    for name in ("demo", "original", "benchmark"):
        command = ops.add_parser(name)
        command.add_argument("--output-dir", required=True)
        if name == "original":
            command.add_argument("--inah-dir", required=True)
            command.add_argument("--datatur-dir", required=True)
        if name == "benchmark":
            command.add_argument("--rows", type=int, default=1000)
    check = ops.add_parser("verify")
    check.add_argument("--first", required=True)
    check.add_argument("--second", required=True)
    args = parser.parse_args()
    try:
        if args.command == "demo":
            result = str(run_demo(args.output_dir).relative_to(ROOT))
        elif args.command == "original":
            result = str(run_original(args.inah_dir, args.datatur_dir, args.output_dir).relative_to(ROOT))
        elif args.command == "benchmark":
            result = run_benchmark(args.output_dir, args.rows)
        else:
            result = verify(args.first, args.second)
    except (ValueError, FileNotFoundError, FileExistsError) as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
