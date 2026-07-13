import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from src import scrape


class ScrapeValidationTests(unittest.TestCase):
    def test_selector_constants_are_named(self):
        self.assertEqual(scrape.LOAD_MORE_BUTTON_CLASS, "load-more-button")
        self.assertEqual(scrape.PRODUCT_CARD_CLASS, "ProductCard")
        self.assertIn("product-card-title", scrape.PRODUCT_TITLE_SELECTOR)
        self.assertIn("PriceTag_actual", scrape.PRICE_AMOUNT_SELECTOR)

    def test_validate_scraped_rows_accepts_valid_rows(self):
        rows = [
            {
                "date": "2026-07-06",
                "title": "Example Laptop",
                "price": "$999",
                "fullprice": "$1199",
                "link": "https://www.jbhifi.com.au/products/example",
                "image": "https://example.com/image.jpg",
                "tags": ["SALE"],
            }
        ]

        self.assertEqual(scrape.validate_scraped_rows(rows), [])

    def test_validate_scraped_rows_reports_empty_result(self):
        self.assertEqual(
            scrape.validate_scraped_rows([], min_rows=1),
            ["Expected at least 1 scraped rows, found 0."],
        )

    def test_validate_scraped_rows_reports_missing_fields_and_bad_tags(self):
        issues = scrape.validate_scraped_rows([{"title": "Example Laptop", "tags": "SALE"}])

        self.assertIn("Row 1 is missing required fields:", issues[0])
        self.assertEqual(issues[1], "Row 1 has non-list tags: str.")

    def test_validate_scraped_rows_before_write_warns_for_empty_result(self):
        with self.assertWarnsRegex(RuntimeWarning, "Expected at least 1 scraped rows"):
            scrape.validate_scraped_rows_before_write([])

    def test_validate_scraped_rows_before_write_rejects_unsafe_rows(self):
        with self.assertRaisesRegex(ValueError, "not safe to write"):
            scrape.validate_scraped_rows_before_write([{"title": "Example Laptop", "tags": "SALE"}])

    def test_extract_product_rows_reports_skipped_cards(self):
        cards = ["valid", "missing", "valid"]

        def extractor(card):
            if card == "missing":
                return None
            return {
                "date": "2026-07-11",
                "title": card,
                "price": "$999",
                "fullprice": "$999",
                "link": f"https://example.com/{card}",
                "image": "https://example.com/image.jpg",
                "tags": [],
            }

        rows, skipped_count = scrape.extract_product_rows(cards, extractor=extractor)

        self.assertEqual(len(rows), 2)
        self.assertEqual(skipped_count, 1)

    @patch("src.scrape.validate_scraped_rows_before_write")
    @patch("src.scrape.extract_product_rows")
    @patch("src.scrape.load_all_products")
    @patch("src.scrape.setup_driver")
    def test_scrape_flow_validates_rows_before_writing(self, setup_driver, load_all, extract_rows, validate_rows):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "results.csv"
            driver = Mock()
            driver.find_elements.return_value = ["card"]
            setup_driver.return_value = driver
            rows = [
                {
                    "date": "2026-07-11",
                    "title": "Example Laptop",
                    "price": "$999",
                    "fullprice": "$999",
                    "link": "https://example.com/laptop",
                    "image": "https://example.com/image.jpg",
                    "rating": None,
                    "num_ratings": None,
                    "tags": [],
                }
            ]
            extract_rows.return_value = (rows, 0)

            scrape.scrape_jbhifi_laptops(output)

            validate_rows.assert_called_once_with(rows)
            self.assertTrue(output.exists())
            driver.quit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
