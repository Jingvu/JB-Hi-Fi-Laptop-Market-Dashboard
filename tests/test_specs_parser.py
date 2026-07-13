import json
import unittest
from unittest.mock import Mock, patch

from src.specs import fetch_specs, parse_specs_from_html


class SpecsParserTests(unittest.TestCase):
    def test_parse_specs_from_html_extracts_product_metafields(self):
        payload = {
            "online_product": {
                "value": {
                    "Display": {
                        "SpecificationDetails": [
                            {"Name": "RAM (GB)", "Values": [16]},
                            {"Name": "Total Storage", "Values": ["512GB"]},
                            {"Name": "Empty", "Values": []},
                        ]
                    }
                }
            }
        }
        html = f"window.themeConfig('product.metafields', {json.dumps(payload)});"

        self.assertEqual(
            parse_specs_from_html(html),
            {"RAM (GB)": "16", "Total Storage": "512GB"},
        )

    def test_parse_specs_from_html_returns_empty_dict_for_missing_block(self):
        self.assertEqual(parse_specs_from_html("<html></html>"), {})

    @patch("src.specs.requests.get")
    def test_fetch_specs_delegates_response_text_to_parser(self, get):
        response = Mock()
        response.text = "<html></html>"
        response.raise_for_status.return_value = None
        get.return_value = response

        self.assertEqual(fetch_specs("https://example.com/product"), {})
        get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
