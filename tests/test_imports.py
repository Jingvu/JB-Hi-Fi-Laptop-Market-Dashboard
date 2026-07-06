import unittest
from pathlib import Path


class ImportSmokeTests(unittest.TestCase):
    def test_pipeline_modules_import(self):
        import src.clean
        import src.ingest
        import src.paths
        import src.pipeline
        import src.schema
        import src.scrape
        import src.specs

        self.assertTrue(src.clean)
        self.assertTrue(src.ingest)
        self.assertTrue(src.paths)
        self.assertTrue(src.pipeline)
        self.assertTrue(src.schema)
        self.assertTrue(src.scrape)
        self.assertTrue(src.specs)

    def test_private_data_paths_resolve_outside_repo(self):
        from src import paths

        self.assertEqual(paths.REPO_ROOT.name, "JB-Hi-Fi-Laptop-Market-Dashboard")
        self.assertEqual(paths.DATA_DIR.name, "jb_hifi_private_data")
        self.assertIsInstance(paths.RESULTS_SPECS, Path)
        self.assertIsInstance(paths.RESULTS_WITH_BRAND, Path)

    def test_pipeline_uses_centralized_private_data_paths(self):
        from src import paths
        from src import pipeline

        self.assertIs(pipeline.DAILY_DIR, paths.DAILY_DIR)
        self.assertIs(pipeline.RESULTS_SPECS, paths.RESULTS_SPECS)
        self.assertIs(pipeline.RESULTS_WITH_BRAND, paths.RESULTS_WITH_BRAND)
        self.assertIs(pipeline.RESULTS_TAGGED, paths.RESULTS_TAGGED)
        self.assertIs(pipeline.RESULTS_SPECS_CLEANED, paths.RESULTS_SPECS_CLEANED)

    def test_schema_constants_are_available(self):
        from src import schema

        self.assertIn("Title", schema.LISTING_CORE_COLUMNS)
        self.assertEqual(schema.DAILY_APPEND_KEY_COLUMNS, ["DateCollected", "Title"])
        self.assertEqual(schema.SPECS_TITLE_COLUMN, "Title")


if __name__ == "__main__":
    unittest.main()
