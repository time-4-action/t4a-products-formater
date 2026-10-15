"""Unit tests for point7-to-shopify.py. Run with: python -m unittest discover -s tests"""

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The script's file name has a hyphen, so it can't be imported by name.
_spec = importlib.util.spec_from_file_location("converter", ROOT / "point7-to-shopify.py")
converter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(converter)


class HelperTests(unittest.TestCase):
    def test_generate_sku_is_deterministic(self):
        self.assertEqual(converter.generate_sku(1956, "m"), converter.generate_sku(1956, "m"))
        self.assertNotEqual(converter.generate_sku(1956, "m"), converter.generate_sku(1956, "l"))
        self.assertRegex(converter.generate_sku(1956, "m"), r"^P7-[0-9A-F]{8}$")

    def test_slugify(self):
        self.assertEqual(converter.slugify("Impact Vest Zipped"), "impact-vest-zipped")
        self.assertEqual(converter.slugify("  AC-1 / Pro  "), "ac-1-pro")

    def test_parse_price(self):
        self.assertEqual(converter.parse_price("105,74"), "105.74")
        self.assertEqual(converter.parse_price("129"), "129")
        self.assertEqual(converter.parse_price([105.74]), "105.74")
        self.assertEqual(converter.parse_price(""), "")
        self.assertEqual(converter.parse_price([]), "")

    def test_base_name_strips_type_suffix(self):
        self.assertEqual(converter.base_name("Impact Vest Zipped - M", "m", "apparel"), "Impact Vest Zipped")
        # Boards and sails names are already clean.
        self.assertEqual(converter.base_name("AC-1 - 5.0", "5.0", "sails"), "AC-1 - 5.0")
        self.assertEqual(converter.base_name("Board - 120", "120", ""), "Board - 120")

    def test_explode_category_tags(self):
        self.assertEqual(
            converter.explode_category_tags("Katalog / Windsurf / Boards"),
            "Katalog, Katalog / Windsurf, Katalog / Windsurf / Boards",
        )

    def test_clean_description(self):
        raw = 'Line one\r\nLine two\r\n\r\nPara two[xyz-ihs snippet="x"]'
        self.assertEqual(converter.clean_description(raw), "<p>Line one<br>Line two</p><p>Para two</p>")


class BuildRowsTests(unittest.TestCase):
    PRODUCTS = [
        {"id": 1, "name": "Vest - M", "type": "m", "sku": "VM", "eu rrp +vat": "129",
         "inventory": "2", "image": "full-m.jpg", "image medium": "med-m.jpg"},
        {"id": 1, "name": "Vest - L", "type": "l", "sku": "", "eu rrp +vat": "129",
         "inventory": "x", "image": "full-l.jpg"},
    ]

    def test_variants_grouped_by_id(self):
        rows = converter.build_rows(self.PRODUCTS, "apparel", {"1": "A, A / B"}, "Variant")
        variant_rows = [r for r in rows if r["Variant SKU"]]
        self.assertEqual(len(variant_rows), 2)
        first, second = variant_rows
        self.assertEqual(first["Title"], "Vest")
        self.assertEqual(first["Handle"], "vest")
        self.assertEqual(first["Tags"], "A, A / B")
        self.assertEqual(first["Variant SKU"], "P7-VM")
        self.assertEqual(second["Variant SKU"], converter.generate_sku(1, "l"))
        self.assertEqual(second["Variant Inventory Qty"], "0")
        self.assertEqual(second["Title"], "")
        self.assertEqual([r["Option1 Value"] for r in variant_rows], ["m", "l"])

    def test_medium_image_gets_image_only_row(self):
        rows = converter.build_rows(self.PRODUCTS, "apparel")
        image_rows = [r for r in rows if not r["Variant SKU"]]
        self.assertEqual([r["Image Src"] for r in image_rows], ["med-m.jpg"])

    def test_fallback_tag_without_categories(self):
        rows = converter.build_rows(self.PRODUCTS, "apparel")
        self.assertEqual(rows[0]["Tags"], "Apparel")


if __name__ == "__main__":
    unittest.main()
