"""Generate fictitious INAH-style CSV and DataTur-style editions for teaching."""

import csv
from datetime import date
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
from shutil import copyfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from openpyxl import Workbook

from .repro import HERE, PRIVATE, module, projected_catalog


CENTER_ID = "simulado:centro-01"
CENTER_NAME = "CENTRO FICTICIO [SIMULADO]"
SITES = (
    ("museo", "2301600", "9000001", "Museo ficticio [SIMULADO]"),
    ("zona_arqueologica", "3120099", "9000002", "Zona ficticia A [SIMULADO]"),
    ("zona_arqueologica", "3120100", "9000003", "Zona ficticia B [SIMULADO]"),
)


def stable_zip(target, entries):
    with ZipFile(target, "w") as archive:
        for name, payload in entries:
            entry = ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
            archive.writestr(entry, payload, compress_type=ZIP_DEFLATED)


def workbook_bytes(month, measure):
    book = Workbook()
    sheet = book.active
    sheet.title = "ExcelMes"
    name, days = {1: ("ENERO", 31), 2: ("FEBRERO", 28)}[month]
    sheet.cell(2, 3, f"RESULTADOS DEL MES DE {name}")
    sheet.cell(3, 3, f"DEL 01-{name}-2025 AL {days}-{name}-2025")
    sheet.cell(6, 2, "CENTRO")
    anchors = (3, 10, 17)
    for column, title in zip(anchors, ("CUARTOS DISPONIBLES PROMEDIO DIARIO", "CUARTOS OCUPADOS", "OCUPACION"), strict=True):
        sheet.cell(6, column, title)
        for index, year in enumerate((2023, 2024, 2025)):
            sheet.cell(7, column + index, year)
    sheet.cell(9, 2, CENTER_NAME)
    for offset, occupied in enumerate((30, 40, measure)):
        for column, value in zip(anchors, (100, occupied, occupied), strict=True):
            sheet.cell(9, column + offset, value)
    initial = BytesIO()
    book.save(initial)
    book.close()
    entries = []
    with ZipFile(initial) as archive:
        for name in archive.namelist():
            payload = archive.read(name)
            if name == "docProps/core.xml":
                payload = re.sub(rb">\d{4}-\d\d-\d\dT[^<]+<", b">2025-01-01T00:00:00Z<", payload)
            entries.append((name, payload))
    final = BytesIO()
    stable_zip(final, entries)
    return final.getvalue()


def build_demo(out):
    inah = module("bigdata02", "profile-cultural-visits.py")
    raw_inah, raw_hotel = out / "raw" / "inah", out / "raw" / "datatur"
    raw_inah.mkdir(parents=True)
    raw_hotel.mkdir(parents=True)
    fields = [*inah.KEYS, *(f"{month}_{origin}" for month in inah.MONTHS for origin in ("nac", "ext"))]
    for kind, filename in inah.INPUTS.items():
        with (raw_inah / filename).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for index, (site_kind, _, code, label) in enumerate(SITES):
                if site_kind == kind:
                    row = dict(zip(inah.KEYS, ("2025", "San Luis Potosí", code, label), strict=True))
                    row.update(enero_nac=0 if index == 0 else 10 * index, enero_ext=0,
                               febrero_nac=10 + index, febrero_ext="" if index == 1 else 2,
                               marzo_nac=20 + index, marzo_ext=3)
                    writer.writerow(row)
    for month, measure in ((1, 0), (2, 55)):
        path = raw_hotel / f"2025-MES_{month:02}_Publico.zip"
        stable_zip(path, [(path.stem + ".xlsx", workbook_bytes(month, measure))])
    return raw_inah, raw_hotel


def configure_demo(pipeline, out, inputs):
    """Use historical transformation functions with explicit fictional scope."""
    pipeline.ROOT = out / "adapter_metadata"
    pipeline.PRIVATE = PRIVATE
    pipeline.WINDOW = date(2025, 1, 1), date(2025, 2, 1)
    pipeline.CENTER, pipeline.LABEL = CENTER_ID, CENTER_NAME
    pipeline.compare_history = lambda db, inputs: {"status": "[SIMULADO]", "comparacion": "No aplica al ensayo didáctico"}
    rows = []
    for path in sorted(inputs.glob("*.zip")):
        row = [None] * 17
        row[0] = f"SIMULADO_MONITOR_2025_{path.name[9:11]}"
        row[3], row[6], row[7] = path.name, path.stat().st_size, sha256(path.read_bytes()).hexdigest()
        row[8], row[9], row[13], row[16] = None, None, None, "Generado para demostración"
        rows.append(row)
    original_read = pipeline.read_archive

    def read_simulated(path):
        edition, bronze, silver, quarantine = original_read(path)
        code = f"SIMULADO_MONITOR_{edition:%Y_%m}"
        return edition, [(code, *r[1:]) for r in bronze], [
            (*r[:8], code, *r[9:]) for r in silver], [(code, *r[1:]) for r in quarantine]

    pipeline.read_archive = read_simulated
    projected_catalog(pipeline.ROOT, rows)
    original = HERE / "bigdata03"
    pipeline.HERE = out / "adapter_sql"
    pipeline.HERE.mkdir()
    for filename in ("queries.sql", "requirements.txt", "contract.json", "pipeline.py"):
        copyfile(original / filename, pipeline.HERE / filename)
    for filename in ("model.sql", "quality.sql"):
        source = (original / filename).read_text(encoding="utf-8")
        source = source.replace("datatur:slp-selected-hotel-center", CENTER_ID)
        for _, real, fake, _ in SITES:
            source = source.replace(real, fake)
        source = (source.replace("DATE '2015-01-01',DATE '2026-08-01'", "DATE '2025-01-01',DATE '2025-03-01'")
                  .replace("https://www.datos.inah.gob.mx/datos-abiertos", "[SIMULADO]")
                  .replace("Museo Regional Potosino; Tamohí; Tamtoc, 2015-01 through 2026-08", "Recintos ficticios [SIMULADO]")
                  .replace("DataTur monitored center; snapshot 2024-01 through 2026-07", "Centro ficticio [SIMULADO]; 2025-01 a 2025-02")
                  .replace("DataTur monitored hotel-center sample; month-specific reporting coverage", "Centro ficticio [SIMULADO]"))
        (pipeline.HERE / filename).write_text(source, encoding="utf-8")
