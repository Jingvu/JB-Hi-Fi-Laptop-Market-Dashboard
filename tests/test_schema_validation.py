import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.clean import clean_specs, tag_discontinued_products
from src.ingest import ingest_daily
from src.schema import LISTING_CORE_COLUMNS, missing_columns, require_columns


class SchemaValidationTests(unittest.TestCase):
    def test_missing_columns_reports_required_columns_in_order(self):
        self.assertEqual(
            missing_columns(["Title", "Price"], ["Title", "Link", "Price"]),
            ["Link"],
        )

    def test_require_columns_raises_clear_error(self):
        with self.assertRaisesRegex(ValueError, "sample data is missing required columns"):
            require_columns(["Title"], ["Title", "Link"], "sample data")

    def test_ingest_daily_rejects_missing_listing_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            daily = tmp_path / "daily.csv"
            master = tmp_path / "master.csv"
            backup = tmp_path / "backup"

            pd.DataFrame([{"Title": "Example Laptop"}]).to_csv(daily, index=False, encoding="utf-8-sig")
            pd.DataFrame(columns=LISTING_CORE_COLUMNS).to_csv(master, index=False, encoding="utf-8-sig")

            with self.assertRaisesRegex(ValueError, "daily listings is missing required columns"):
                ingest_daily(daily, master, backup_dir=backup)

            self.assertFalse(backup.exists())

    def test_tag_discontinued_rejects_missing_listing_columns_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.csv"
            output = tmp_path / "tagged.csv"

            pd.DataFrame([{"Title": "Example Laptop"}]).to_csv(source, index=False, encoding="utf-8-sig")

            with self.assertRaisesRegex(ValueError, "historical listings is missing required columns"):
                tag_discontinued_products(source, output)

            self.assertFalse(output.exists())

    def test_clean_specs_rejects_missing_title_column_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "specs.csv"
            output = tmp_path / "cleaned.csv"

            pd.DataFrame([{"Product": "Example Laptop"}]).to_csv(source, index=False, encoding="utf-8-sig")

            with self.assertRaisesRegex(ValueError, "raw specs is missing required columns"):
                clean_specs(source, output)

            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
