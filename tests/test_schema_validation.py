import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.clean import (
    clean_specs,
    tag_discontinued_products,
    validate_clean_specs_before_write,
    validate_tagged_listings_before_write,
)
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

    def test_validate_tagged_listings_before_write_requires_output_columns(self):
        df = pd.DataFrame(columns=LISTING_CORE_COLUMNS + ["Final appear day"])

        with self.assertRaisesRegex(ValueError, "tagged listings is missing required columns"):
            validate_tagged_listings_before_write(df)

    def test_validate_clean_specs_before_write_requires_title(self):
        with self.assertRaisesRegex(ValueError, "cleaned specs is missing required columns"):
            validate_clean_specs_before_write(pd.DataFrame(columns=["Product"]))

    def test_tag_discontinued_preserves_row_count_and_adds_expected_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.csv"
            output = tmp_path / "tagged.csv"
            row = {
                "DateCollected": "2026-07-10",
                "Brand": "Example",
                "Title": "Example Laptop",
                "Price": "$999",
                "FullPrice": "$1099",
                "Link": "https://example.com/laptop",
                "ImageURL": "https://example.com/image.jpg",
                "Rating": "",
                "NumRating": "",
            }
            pd.DataFrame([row]).to_csv(source, index=False, encoding="utf-8-sig")

            tag_discontinued_products(source, output)

            result = pd.read_csv(output, encoding="utf-8-sig")
            self.assertEqual(len(result), 1)
            self.assertIn("Final appear day", result.columns)
            self.assertIn("Discontinued", result.columns)


if __name__ == "__main__":
    unittest.main()
