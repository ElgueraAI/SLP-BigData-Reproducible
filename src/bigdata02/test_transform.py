import importlib.util
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock


spec = importlib.util.spec_from_file_location("cultural_visits", Path(__file__).with_name("profile-cultural-visits.py"))
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


def row(year="2026", state="SAN LUIS POTOSÍ", code="001", national="0", foreign=""):
    result = dict(zip(pipeline.KEYS, (year, state, code, "Recinto de prueba")))
    for month in pipeline.MONTHS:
        result[month + "_nac"] = national
        result[month + "_ext"] = foreign
    return result


class TransformTest(unittest.TestCase):
    def test_months_are_inclusive_and_cross_calendar_year(self):
        self.assertEqual(pipeline.inclusive_months(date(2025, 12, 1), date(2026, 2, 1)),
                         [date(2025, 12, 1), date(2026, 1, 1), date(2026, 2, 1)])

    def test_zero_missing_and_invalid_integer_are_distinct(self):
        self.assertEqual(pipeline.measure("0"), 0)
        self.assertEqual(pipeline.measure(" 0002 "), 2)
        for value in ("", "ND", "N/D", "-", "—"):
            self.assertIsNone(pipeline.measure(value))
        for value in ("-1", "5.5", "?", "1,500"):
            with self.assertRaises(ValueError):
                pipeline.measure(value)

    def test_municipal_scope_source_row_and_missing_pairs(self):
        input_rows = [row(state="Jalisco"), row(), row(code="002", national="ND", foreign="0")]
        bronze, silver, held, sites, profile = pipeline.curate(
            {"museo": input_rows}, [date(2026, 1, 1)], "edition")
        self.assertEqual(len(bronze), 3)
        self.assertEqual(len(sites), 2)
        self.assertEqual(len(held), 0)
        self.assertEqual(len(silver), 2)
        self.assertEqual(silver[0][8:15], (0, None, None, "partial_pair", pipeline.INPUTS["museo"], "edition", 2))
        self.assertEqual(profile["museo"]["row_disposition"]["fuera_de_slp"], 1)

    def test_all_rows_for_a_conflicting_key_are_quarantined(self):
        inputs = [row(foreign="1"), row(foreign="2"), row(code="002", foreign="0")]
        bronze, silver, held, _, profile = pipeline.curate(
            {"museo": inputs}, [date(2026, 1, 1)], "edition")
        self.assertEqual(len(bronze), 3)
        self.assertEqual([record[2] for record in held], [1, 2])
        self.assertEqual(len(silver), 1)
        self.assertEqual(silver[0][8:12], (0, 0, 0, "reported"))
        self.assertEqual(profile["museo"]["row_disposition"]["recinto_anio_duplicado"], 2)

    def test_invalid_date_and_value_are_quarantined(self):
        inputs = [row(year="0"), row(code="002", national="-1")]
        _, silver, held, _, _ = pipeline.curate({"museo": inputs}, [date(2026, 1, 1)], "edition")
        self.assertEqual(silver, [])
        self.assertEqual({entry[4] for entry in held},
                         {"identidad_o_anio_invalido", "conteo_no_entero_o_negativo"})

    def test_preserve_original_utf8_bom_and_empty_string(self):
        path = Mock()
        path.name = "sample.csv"
        path.read_bytes.return_value = b"\xef\xbb\xbfkey,text\r\n1,\r\n"
        rows, metadata = pipeline.load_csv(path)
        self.assertEqual(rows, [{"key": "1", "text": ""}])
        self.assertEqual(metadata["encoding"], "utf-8-sig")
        self.assertEqual(metadata["rows"], 1)


if __name__ == "__main__":
    unittest.main()
