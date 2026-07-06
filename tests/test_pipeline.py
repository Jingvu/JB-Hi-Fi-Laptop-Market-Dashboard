import unittest
from unittest.mock import patch

from src import pipeline


class PipelineTests(unittest.TestCase):
    @patch("src.pipeline.ensure_data_dirs")
    @patch("src.pipeline.tag_discontinued_products")
    @patch("src.pipeline.clean_specs")
    def test_clean_all_preserves_existing_values_by_default(self, clean_specs, tag_discontinued, ensure_dirs):
        pipeline.clean_all()

        clean_specs.assert_called_once_with(
            pipeline.RESULTS_SPECS,
            pipeline.RESULTS_SPECS_CLEANED,
            keep_existing_values=True,
        )

    @patch("src.pipeline.ensure_data_dirs")
    @patch("src.pipeline.tag_discontinued_products")
    @patch("src.pipeline.clean_specs")
    def test_clean_all_can_reclean_existing_values(self, clean_specs, tag_discontinued, ensure_dirs):
        pipeline.clean_all(keep_existing_values=False)

        clean_specs.assert_called_once_with(
            pipeline.RESULTS_SPECS,
            pipeline.RESULTS_SPECS_CLEANED,
            keep_existing_values=False,
        )


if __name__ == "__main__":
    unittest.main()
