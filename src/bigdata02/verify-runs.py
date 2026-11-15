"""Compare two independent INAH runs and verify recorded logical output hashes."""

import argparse
import csv
from hashlib import sha256
import importlib.util
import json
from pathlib import Path


spec = importlib.util.spec_from_file_location("cultural_visits", Path(__file__).with_name("profile-cultural-visits.py"))
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify(first, second):
    manifests = [read_json(folder / "manifest.json") for folder in (first, second)]
    for folder, manifest in zip((first, second), manifests):
        for hashes in ("logical_sha256", "binary_sha256"):
            for name, digest in manifest.get(hashes, {}).items():
                if sha256((folder / name).read_bytes()).hexdigest() != digest:
                    raise ValueError(f"Archivo no coincide con manifiesto: {folder.name}/{name}")
    logical = [{key: value for key, value in manifest.items() if key != "binary_sha256"} for manifest in manifests]
    if logical[0] != logical[1]:
        raise ValueError("Difieren las entradas, el esquema, la configuración o las salidas lógicas")
    return {
        "logical_equal": True,
        "logical_sha256": logical[0]["logical_sha256"],
        "binary_comparable": "binary_sha256" in manifests[0],
        "binary_equal": manifests[0].get("binary_sha256") == manifests[1].get("binary_sha256")
                        if "binary_sha256" in manifests[0] else None,
        "quality": read_json(first / "quality.json"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first")
    parser.add_argument("second")
    args = parser.parse_args()
    first, second = (pipeline.private_path(value) for value in (args.first, args.second))
    if first == second:
        raise ValueError("Se requieren dos directorios de ejecución independientes")
    result = verify(first, second)
    if (first / "Q6.csv").exists():
        with (first / "Q6.csv").open(encoding="utf-8", newline="") as stream:
            from collections import Counter
            result["historical_comparison"] = dict(Counter(row["comparison"] for row in csv.DictReader(stream)))
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
