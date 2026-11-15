"""Portable tests for the adapter and its bundled original suites."""

from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from src import repro


class ReproTest(unittest.TestCase):
    def test_original_transform_suites(self):
        for mission, name in (("bigdata02", "test_transform.py"), ("bigdata03", "test_pipeline.py")):
            with self.subTest(mission=mission):
                path = repro.HERE / mission / name
                subprocess.run([sys.executable, "-B", str(path)], cwd=repro.ROOT, check=True)

    def test_missing_originals_explain_file_scope(self):
        repro.PRIVATE.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=repro.PRIVATE, prefix="test-inputs-") as empty:
            folder = Path(empty)
            with self.assertRaisesRegex(ValueError, "Faltan insumos autorizados.*INAH_"):
                repro.run_original(folder, folder, repro.PRIVATE / "not-materialized")

    def test_public_directory_rejected(self):
        with self.assertRaisesRegex(ValueError, r"\.bigdata-private"):
            repro.run_demo(repro.ROOT / "published-example")

    def test_mode_a_uses_original_queries_and_preserves_missing(self):
        repro.PRIVATE.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=repro.PRIVATE, prefix="test-repro-") as tmp:
            first = repro.run_demo(Path(tmp) / "a")
            second = repro.run_demo(Path(tmp) / "b")
            self.assertEqual(repro.verify(first, second), {"logical_equal": True, "mode": "A", "queries": 8})
            database = first / "warehouse" / "campaign.duckdb"
            checks = repro.query(database, """
                SELECT count(*) AS periods, count(hotel_occupancy_percent) AS hotel_reported,
                       count(*) FILTER (WHERE hotel_occupancy_percent=0) AS hotel_zero,
                       count(*) FILTER (WHERE tamohi_entries IS NULL AND tamohi_status='partial_pair') AS inah_partial
                FROM campaign_calendar
            """)[0]
            self.assertEqual(checks, dict(periods=3, hotel_reported=2, hotel_zero=1, inah_partial=1))
            self.assertEqual(repro.read_report(first / "comparison.json")["classification"], "[SIMULADO]")
            self.assertTrue(all((first / "warehouse" / f"Q{i}.csv").is_file() for i in range(1, 9)))


if __name__ == "__main__":
    unittest.main()
