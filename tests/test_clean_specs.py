import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.clean import clean_specs


class CleanSpecsTests(unittest.TestCase):
    def test_clean_specs_preserves_existing_values_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw = tmp_path / "specs.csv"
            cleaned = tmp_path / "cleaned.csv"

            pd.DataFrame([{"Title": "Example Laptop"}]).to_csv(raw, index=False, encoding="utf-8-sig")
            pd.DataFrame([{"Title": "Example Laptop", "Product condition": "Manual Override"}]).to_csv(
                cleaned,
                index=False,
                encoding="utf-8-sig",
            )

            clean_specs(raw, cleaned)

            result = pd.read_csv(cleaned, encoding="utf-8-sig")
            self.assertEqual(result.loc[0, "Product condition"], "Manual Override")
            self.assertFalse(result.loc[0, "is_new"])

    def test_clean_specs_can_reclean_existing_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw = tmp_path / "specs.csv"
            cleaned = tmp_path / "cleaned.csv"

            pd.DataFrame([{"Title": "Example Renewed Laptop"}]).to_csv(raw, index=False, encoding="utf-8-sig")
            pd.DataFrame([{"Title": "Example Renewed Laptop", "Product condition": "Manual Override"}]).to_csv(
                cleaned,
                index=False,
                encoding="utf-8-sig",
            )

            clean_specs(raw, cleaned, keep_existing_values=False)

            result = pd.read_csv(cleaned, encoding="utf-8-sig")
            self.assertEqual(result.loc[0, "Product condition"], "Renewed")
            self.assertTrue(result.loc[0, "is_new"])


if __name__ == "__main__":
    unittest.main()
