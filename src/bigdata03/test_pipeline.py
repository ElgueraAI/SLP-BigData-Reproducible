from datetime import date
from pathlib import Path
import unittest

from openpyxl import Workbook

from pipeline import LABEL, dates, protected_path, read_sheet, reading


def sheet_for(title, start, end):
    sheet = Workbook().active
    sheet["C2"] = title
    sheet["C3"] = f"Del {start} al {end}"
    for col, label in ((2, "Centro"), (3, "Cuartos disponibles promedio diario"),
                       (10, "Cuartos ocupados"), (17, "Ocupación")):
        sheet.cell(row=6, column=col, value=label)
    for col in (3, 10, 17):
        for offset, year in enumerate((2024, 2025, 2026)):
            sheet.cell(row=7, column=col + offset, value=f"{year}{'*' * (offset + 1)}")
    sheet["B9"] = LABEL
    sheet["E9"] = 100
    sheet["L9"] = 0
    sheet["S9"] = 0
    return sheet


class DataTurTests(unittest.TestCase):
    def test_observed_zero(self):
        self.assertEqual(reading([100, 0, 0]), (100, 0, 0, 0, "reported"))

    def test_missing_is_null(self):
        self.assertEqual(reading([100, "n.d.", None]), (100, None, None, None, "source_missing"))

    def test_invalid_values(self):
        for cells in ([0, 0, 0], [100, -1, 5], [100, 101, 100], [100, 50, 100.1], [100, 50, 52], [100, True, 1]):
            with self.subTest(cells=cells), self.assertRaises(ValueError):
                reading(cells)

    def test_extraction_monthly_and_accumulated(self):
        date_ = date(2026, 7, 1)
        source = sheet_for("Comparativo Mes de julio", "01-julio-2026", "31-julio-2026")
        self.assertEqual(read_sheet(source, date_)[0], "monthly")
        source["C3"] = "Del 01-enero-2026 al 31-julio-2026"
        with self.assertRaises(ValueError):
            read_sheet(source, date_)
        source["C2"] = "Resultados preliminares acumulados al mes de julio"
        self.assertEqual(read_sheet(source, date_)[0], "year_to_date")
        source["C3"] = "Del 01-enero-2025 al 31-julio-2026"
        self.assertEqual(read_sheet(source, date_)[0], "auxiliary_unverified_window")

    def test_duplicate_centers_and_mismatched_vintage(self):
        source = sheet_for("Comparativo Mes de julio", "01-julio-2026", "31-julio-2026")
        source["B10"] = LABEL
        with self.assertRaisesRegex(ValueError, "una fila"):
            read_sheet(source, date(2026, 7, 1))
        source["B10"] = "Otro centro"
        source["E7"] = "2027***"
        with self.assertRaisesRegex(ValueError, "encabezados de año"):
            read_sheet(source, date(2026, 7, 1))

    def test_window_and_private_path(self):
        self.assertEqual(len(list(dates(date(2024, 1, 1), date(2026, 7, 1)))), 31)
        with self.assertRaises(ValueError):
            protected_path(Path(".bigdata-private") / ".." / "src")


if __name__ == "__main__":
    unittest.main()
