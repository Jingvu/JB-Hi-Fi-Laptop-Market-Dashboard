import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.clean import (
    clean_specs,
    clean_specs_dataframe,
    clean_resolution,
    dedupe_specs_by_title,
    infer_display_size_from_title,
    infer_gpu_from_title,
    infer_processor_from_title,
    infer_storage_from_title,
    mark_new_specs_rows,
    normalize_copilot_pc_column,
    normalize_graphics_columns,
    normalize_gpu_text,
    normalize_operating_system_columns,
    normalize_port_count_columns,
    normalize_processor_columns,
    normalize_product_flag_columns,
    normalize_resolution_columns,
    parse_price_series,
    preserve_existing_cleaned_values,
    tag_discontinued_dataframe,
)
from src.schema import LISTING_CORE_COLUMNS


class CleanSpecsTests(unittest.TestCase):
    def test_parse_price_series_preserves_existing_price_behavior(self):
        result = parse_price_series(pd.Series(["$999", "$1,499"]))

        self.assertEqual(result.tolist(), [999.0, 1499.0])
        self.assertEqual(str(result.dtype), "float64")

    def test_dedupe_specs_by_title_keeps_last_case_insensitive_title(self):
        df = pd.DataFrame(
            [
                {"Title": "Example Laptop", "RAM (GB)": "8"},
                {"Title": "example laptop", "RAM (GB)": "16"},
            ]
        )

        result = dedupe_specs_by_title(df)

        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["RAM (GB)"], "16")
        self.assertNotIn("Title_lower", result.columns)

    def test_tag_discontinued_dataframe_preserves_row_count_and_adds_columns(self):
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
        result = tag_discontinued_dataframe(pd.DataFrame([row]))

        self.assertEqual(len(result), 1)
        self.assertEqual(list(result.columns[: len(LISTING_CORE_COLUMNS)]), LISTING_CORE_COLUMNS)
        self.assertIn("Final appear day", result.columns)
        self.assertIn("Discontinued", result.columns)
        self.assertEqual(result.loc[0, "Price"], 999.0)

    def test_clean_specs_dataframe_preserves_existing_values_by_default(self):
        raw = pd.DataFrame([{"Title": "Example Laptop"}])
        old = pd.DataFrame([{"Title": "Example Laptop", "Product condition": "Manual Override"}])

        result = clean_specs_dataframe(raw, old=old)

        self.assertEqual(result.loc[0, "Product condition"], "Manual Override")
        self.assertFalse(result.loc[0, "is_new"])

    def test_clean_specs_dataframe_can_reclean_existing_values(self):
        raw = pd.DataFrame([{"Title": "Example Renewed Laptop"}])
        old = pd.DataFrame([{"Title": "Example Renewed Laptop", "Product condition": "Manual Override"}])

        result = clean_specs_dataframe(raw, old=old, keep_existing_values=False)

        self.assertEqual(result.loc[0, "Product condition"], "Renewed")
        self.assertTrue(result.loc[0, "is_new"])

    def test_clean_specs_dataframe_uses_deduplication_policy(self):
        raw = pd.DataFrame(
            [
                {"Title": "Example Laptop"},
                {"Title": "example laptop"},
            ]
        )

        result = clean_specs_dataframe(raw)

        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["Title"], "example laptop")

    def test_mark_new_specs_rows_uses_existing_cleaned_titles(self):
        df = pd.DataFrame([{"Title": "Example Laptop"}, {"Title": "New Laptop"}])
        old = pd.DataFrame([{"Title": "example laptop"}])

        result = mark_new_specs_rows(df, old=old)

        self.assertEqual(result["is_new"].tolist(), [False, True])

    def test_normalize_copilot_pc_column_preserves_existing_yes_behavior(self):
        df = pd.DataFrame(
            [
                {"Title": "A", "Copilot+ PC": "Yes, Yes"},
                {"Title": "B", "Copilot+ PC": "No"},
                {"Title": "C", "Copilot+ PC": True},
            ]
        )

        result = normalize_copilot_pc_column(df)

        self.assertEqual(result["Copilot+ PC"].tolist(), [True, False, True])

    def test_normalize_product_flag_columns_preserves_existing_buckets(self):
        df = pd.DataFrame(
            [
                {
                    "Title": "Example Refurbished Gaming Laptop",
                    "AI features": "Microsoft Copilot, Copilot keyboard key",
                    "Display type": "IPS-Level",
                }
            ]
        )

        result = normalize_product_flag_columns(df)

        self.assertTrue(result.loc[0, "Gaming PC"])
        self.assertEqual(result.loc[0, "AI features"], "Copilot keyboard key")
        self.assertEqual(result.loc[0, "Product condition"], "Refurbished")
        self.assertEqual(result.loc[0, "Display type"], "IPS")

    def test_normalize_product_flag_columns_maps_approved_display_types(self):
        df = pd.DataFrame(
            [
                {"Title": "A", "Display type": "Liquid Retina"},
                {"Title": "B", "Display type": "Liquid Retina XDR"},
                {"Title": "C", "Display type": "WVA"},
            ]
        )

        result = normalize_product_flag_columns(df)

        self.assertEqual(
            result["Display type"].tolist(),
            ["Liquid Retina", "Liquid Retina XDR", "WVA"],
        )

    def test_normalize_port_count_columns_preserves_missing_as_zero_policy(self):
        df = pd.DataFrame([{"Title": "A", "USB Ports": None, "USB-C Ports": 2.0}])

        result = normalize_port_count_columns(df)

        self.assertEqual(result.loc[0, "USB Ports"], 0)
        self.assertEqual(result.loc[0, "USB-C Ports"], 2)
        self.assertEqual(str(result["USB Ports"].dtype), "Int64")

    def test_normalize_operating_system_columns_preserves_typo_fix(self):
        df = pd.DataFrame([{"Title": "A", "Operating system": "MacOS Sequioa"}])

        result = normalize_operating_system_columns(df)

        self.assertEqual(result.loc[0, "OS_norm"], "macos sequoia")
        self.assertEqual(result.loc[0, "Operating system"], "macOS Sequoia")
        self.assertEqual(result.loc[0, "OS_family"], "macOS")

    def test_normalize_operating_system_columns_maps_approved_macos_variants(self):
        df = pd.DataFrame(
            [
                {"Title": "A", "Operating system": "macOS"},
                {"Title": "B", "Operating system": "macOS Mojave"},
                {"Title": "C", "Operating system": "macOS Catalina"},
                {"Title": "D", "Operating system": "macOS Sierra"},
                {"Title": "E", "Operating system": "macOS Big Sur"},
            ]
        )

        result = normalize_operating_system_columns(df)

        self.assertEqual(
            result["Operating system"].tolist(),
            ["macOS", "macOS Mojave", "macOS Catalina", "macOS Sierra", "macOS Big Sur"],
        )
        self.assertEqual(result["OS_family"].tolist(), ["macOS"] * 5)

    def test_normalize_resolution_columns_preserves_merge_and_drop_policy(self):
        df = pd.DataFrame(
            [
                {
                    "Title": "A",
                    "Monitor resolution": None,
                    "Resolution (Pixels)": "1920x1080",
                }
            ]
        )

        result = normalize_resolution_columns(df)

        self.assertEqual(result.loc[0, "Monitor resolution"], "1920 x 1080")
        self.assertNotIn("Resolution (Pixels)", result.columns)

    def test_clean_resolution_parses_approved_separator_formats(self):
        cases = {
            "2560-by-1664": "2560 x 1664",
            "2560 by 1664": "2560 x 1664",
            "2560*1600": "2560 x 1600",
            "2880 1800": "2880 x 1800",
        }

        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(clean_resolution(raw), expected)

    def test_clean_resolution_preserves_existing_supported_formats(self):
        cases = {
            "1920 x 1080": "1920 x 1080",
            "2880x1800": "2880 x 1800",
            "1920 \u00d7 1200": "1920 x 1200",
        }

        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(clean_resolution(raw), expected)

    def test_normalize_processor_and_graphics_columns_preserve_existing_buckets(self):
        df = pd.DataFrame(
            [
                {
                    "Title": "Example Laptop",
                    "Processor Type": "Intel\u00ae CoreTM Ultra 7",
                    "Graphics processor": "NVIDIA GeForce RTX 4060",
                    "Graphics card series": None,
                }
            ]
        )

        result = normalize_processor_columns(df)
        result = normalize_graphics_columns(result)

        self.assertEqual(result.loc[0, "Processor Type"], "Intel Core Ultra 7")
        self.assertEqual(result.loc[0, "Processor brand"], "Intel")
        self.assertEqual(result.loc[0, "Graphics processor"], "NVIDIA RTX 4060")
        self.assertEqual(result.loc[0, "GPU brand"], "NVIDIA")

    def test_normalize_gpu_text_removes_field_level_trademark_markers(self):
        self.assertEqual(
            normalize_gpu_text("NVIDIA\u00ae GeForce\u00ae RTXTM 4070"),
            "nvidia geforce rtx 4070",
        )

    def test_normalize_graphics_columns_maps_identified_field_level_gpu_patterns(self):
        df = pd.DataFrame(
            [
                {
                    "Title": "Alienware gaming laptop",
                    "Graphics processor": "NVIDIA\u00ae GeForce\u00ae RTXTM 4070",
                    "Graphics card series": None,
                },
                {
                    "Title": "ASUS gaming laptop",
                    "Graphics processor": "Nvidia GeForce 4060",
                    "Graphics card series": None,
                },
            ]
        )

        result = normalize_graphics_columns(df)

        self.assertEqual(result.loc[0, "Graphics processor"], "NVIDIA RTX 4070")
        self.assertEqual(result.loc[0, "GPU brand"], "NVIDIA")
        self.assertEqual(result.loc[1, "Graphics processor"], "NVIDIA GeForce 4060")
        self.assertEqual(result.loc[1, "GPU brand"], "NVIDIA")

    def test_normalize_graphics_columns_preserves_existing_non_nvidia_mappings(self):
        df = pd.DataFrame(
            [
                {"Title": "Intel Laptop", "Graphics processor": "Intel Iris Xe Graphics"},
                {"Title": "AMD Laptop", "Graphics processor": "AMD Radeon Graphics"},
                {"Title": "Apple Laptop", "Graphics processor": "10 core GPU"},
            ]
        )

        result = normalize_graphics_columns(df)

        self.assertEqual(result["Graphics processor"].tolist(), ["Intel Iris Xe", "AMD Radeon", "Apple GPU"])
        self.assertEqual(result["GPU brand"].tolist(), ["Intel", "AMD", "Apple"])

    def test_infer_gpu_from_title_maps_approved_rtx_patterns(self):
        cases = {
            "Gigabyte Aero X16 RTX 5070 gaming laptop": "NVIDIA RTX 5070",
            "HP Victus RTX5070Ti gaming laptop": "NVIDIA RTX 5070 Ti",
            "ASUS ProArt [GeForce RTX 5070] laptop": "NVIDIA RTX 5070",
            "Dell Precision RTX A1000 workstation laptop": "NVIDIA RTX A1000",
        }

        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(infer_gpu_from_title(title), expected)

    def test_infer_gpu_from_title_rejects_ambiguous_title_patterns(self):
        cases = [
            "Lenovo ThinkBook business laptop - arctic grey",
            "Example gaming laptop 5070",
            "Example gaming laptop with 16GB RAM",
        ]

        for title in cases:
            with self.subTest(title=title):
                self.assertIsNone(infer_gpu_from_title(title))

    def test_normalize_graphics_columns_infers_gpu_only_when_existing_fields_are_unusable(self):
        df = pd.DataFrame(
            [
                {
                    "Title": "Gigabyte Aero X16 RTX 5070 gaming laptop",
                    "Graphics processor": None,
                    "Graphics card series": None,
                },
                {
                    "Title": "Example RTX 5070 laptop",
                    "Graphics processor": "Intel Iris Xe Graphics",
                    "Graphics card series": None,
                },
                {
                    "Title": "Example RTX 5070 laptop",
                    "Graphics processor": None,
                    "Graphics card series": "NVIDIA GeForce RTX 4060",
                },
            ]
        )

        result = normalize_graphics_columns(df)

        self.assertEqual(result.loc[0, "Graphics processor"], "NVIDIA RTX 5070")
        self.assertEqual(result.loc[0, "GPU brand"], "NVIDIA")
        self.assertEqual(result.loc[1, "Graphics processor"], "Intel Iris Xe")
        self.assertEqual(result.loc[1, "GPU brand"], "Intel")
        self.assertEqual(result.loc[2, "Graphics processor"], "NVIDIA GeForce RTX 4060")
        self.assertEqual(result.loc[2, "GPU brand"], "NVIDIA")

    def test_normalize_processor_columns_maps_approved_apple_a_series(self):
        df = pd.DataFrame([{"Title": "Example Tablet", "Processor Type": "Apple A18 Pro"}])

        result = normalize_processor_columns(df)

        self.assertEqual(result.loc[0, "Processor Type"], "Apple A18 Pro")
        self.assertEqual(result.loc[0, "Processor brand"], "Apple A")

    def test_preserve_existing_cleaned_values_keeps_old_values_for_existing_rows(self):
        df = pd.DataFrame(
            [
                {"Title": "Example Laptop", "is_new": False, "Product condition": "Other"},
                {"Title": "New Laptop", "is_new": True, "Product condition": "Renewed"},
            ]
        )
        old = pd.DataFrame([{"Title": "Example Laptop", "Product condition": "Manual Override"}])

        result = preserve_existing_cleaned_values(df, old=old)

        self.assertEqual(result.loc[0, "Product condition"], "Manual Override")
        self.assertEqual(result.loc[1, "Product condition"], "Renewed")
        self.assertEqual(list(result.columns), list(df.columns))

    def test_title_spec_fallbacks_populate_example_missing_values(self):
        raw = pd.DataFrame(
            [
                {
                    "Title": 'lenovo ideapad slim 5 16" 3k 120hz laptop (intel core ultra 7)[1tb]',
                    "Display size (inches)": None,
                    "Processor Type": None,
                    "SSD storage": None,
                    "Total Storage": None,
                }
            ]
        )

        result = clean_specs_dataframe(raw)

        self.assertEqual(result.loc[0, "Display size (inches)"], 16)
        self.assertEqual(result.loc[0, "Processor Type"], "Intel Core Ultra 7")
        self.assertEqual(result.loc[0, "Processor brand"], "Intel")
        self.assertEqual(result.loc[0, "SSD storage"], "1TB")
        self.assertEqual(result.loc[0, "Total Storage"], "1TB")

    def test_title_spec_fallbacks_do_not_overwrite_existing_values(self):
        raw = pd.DataFrame(
            [
                {
                    "Title": 'example 16" laptop (intel core ultra 7)[1tb]',
                    "Display size (inches)": 14,
                    "Processor Type": "AMD Ryzen 7",
                    "SSD storage": "512GB",
                    "Total Storage": "512GB",
                }
            ]
        )

        result = clean_specs_dataframe(raw)

        self.assertEqual(result.loc[0, "Display size (inches)"], 14)
        self.assertEqual(result.loc[0, "Processor Type"], "AMD Ryzen 7")
        self.assertEqual(result.loc[0, "SSD storage"], "512GB")
        self.assertEqual(result.loc[0, "Total Storage"], "512GB")

    def test_title_spec_fallbacks_reject_ambiguous_title_values(self):
        title = "example 3k 120hz gaming laptop model 512 16gb ram"

        self.assertTrue(pd.isna(infer_display_size_from_title(title)))
        self.assertTrue(pd.isna(infer_processor_from_title(title)))
        self.assertTrue(pd.isna(infer_storage_from_title(title)))

    def test_title_spec_fallbacks_reject_unsupported_processor_names(self):
        title = 'example 16" laptop (intel pentium silver)[256gb]'

        self.assertTrue(pd.isna(infer_processor_from_title(title)))
        self.assertEqual(infer_display_size_from_title(title), 16)
        self.assertEqual(infer_storage_from_title(title), "256GB")

    def test_title_spec_fallbacks_do_not_create_new_storage_categories(self):
        self.assertTrue(pd.isna(infer_storage_from_title("example laptop with 500GB SSD")))

    def test_title_spec_fallbacks_leave_titles_without_patterns_unchanged(self):
        raw = pd.DataFrame(
            [
                {
                    "Title": "plain laptop with no supported fallback values",
                    "Display size (inches)": None,
                    "Processor Type": None,
                    "SSD storage": None,
                    "Total Storage": None,
                }
            ]
        )

        result = clean_specs_dataframe(raw)

        self.assertTrue(pd.isna(result.loc[0, "Display size (inches)"]))
        self.assertTrue(pd.isna(result.loc[0, "Processor Type"]))
        self.assertTrue(pd.isna(result.loc[0, "SSD storage"]))
        self.assertTrue(pd.isna(result.loc[0, "Total Storage"]))

    def test_clean_specs_dataframe_preserves_row_count_columns_order_and_values(self):
        raw = pd.DataFrame(
            [
                {
                    "Title": "Example Renewed Gaming Laptop",
                    "Copilot+ PC": "Yes",
                    "AI features": "Microsoft Copilot|Copilot keyboard key",
                    "Display type": "OLED",
                    "USB Ports": None,
                    "USB-C Ports": 2.0,
                    "Operating system": "Windows 11 Home",
                    "Monitor resolution": None,
                    "Resolution (Pixels)": "2560 x 1600",
                    "Processor Type": "AMD Ryzen 7",
                    "Graphics processor": "AMD Radeon Graphics",
                    "Graphics card series": None,
                },
                {
                    "Title": "example renewed gaming laptop",
                    "Copilot+ PC": "No",
                    "AI features": "Built for Apple Intelligence",
                    "Display type": "Liquid Retina",
                    "USB Ports": 1.0,
                    "USB-C Ports": None,
                    "Operating system": "macOS",
                    "Monitor resolution": "2880 x 1800",
                    "Resolution (Pixels)": "1920 x 1080",
                    "Processor Type": "Apple M4",
                    "Graphics processor": "10 core GPU",
                    "Graphics card series": None,
                },
            ]
        )

        result = clean_specs_dataframe(raw)

        self.assertEqual(len(result), 1)
        self.assertEqual(
            list(result.columns),
            [
                "Title",
                "Copilot+ PC",
                "AI features",
                "Display type",
                "USB Ports",
                "USB-C Ports",
                "Operating system",
                "Monitor resolution",
                "Processor Type",
                "Graphics processor",
                "Graphics card series",
                "is_new",
                "Gaming PC",
                "Product condition",
                "OS_norm",
                "OS_family",
                "Processor brand",
                "GPU brand",
            ],
        )
        row = result.iloc[0]
        self.assertEqual(row["Title"], "example renewed gaming laptop")
        self.assertFalse(row["Copilot+ PC"])
        self.assertTrue(pd.isna(row["AI features"]))
        self.assertEqual(row["Display type"], "Liquid Retina")
        self.assertEqual(row["USB Ports"], 1)
        self.assertEqual(row["USB-C Ports"], 0)
        self.assertEqual(row["Operating system"], "macOS")
        self.assertEqual(row["OS_family"], "macOS")
        self.assertEqual(row["Monitor resolution"], "2880 x 1800")
        self.assertEqual(row["Processor Type"], "Apple M4")
        self.assertEqual(row["Processor brand"], "Apple M")
        self.assertEqual(row["Graphics processor"], "Apple GPU")
        self.assertEqual(row["GPU brand"], "Apple")

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
