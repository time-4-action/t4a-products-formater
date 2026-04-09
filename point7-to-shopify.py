#!/usr/bin/env python3
"""
point7-to-shopify.py

Converts a Point-7 products.json to a Shopify-compatible product import CSV.

Usage:
    python point7-to-shopify.py products.json [output.csv]

JSON structure expected:
    {
        "parts":      [...],
        "components": [...],
        "apparel":    [...],
        "bags":       [...],
        "":           [...],   ← unnamed category, tagged as "Boards & Sails"
        "sails":      [...]
    }

Grouping logic:
    - Products are grouped by `id`. Same id = one Shopify product with multiple variants.
    - Option1 Name = "Title", Option1 Value = entry["type"] (for multi-variant products).
    - Single-entry groups get Option1 = "Title" / "Default Title".

Title stripping:
    - For categories like parts/components/apparel/bags, the type is often appended to
      the name as a suffix: "Impact Vest Zipped - M" → "Impact Vest Zipped".
    - For sails / unnamed category, the name is already clean (no suffix to strip).

Tags:
    - Each product gets a tag matching its source category key.
    - The empty-string key is tagged as "boards-sails".

Pricing:
    - Variant Price  ← "eu rrp +vat"  (comma → dot)
    - Compare At     ← "eu rrp"       (only set if different from price)
"""

import json
import csv
import sys
import re
from collections import OrderedDict


# ── Category → Shopify tag mapping ───────────────────────────────────────────

CATEGORY_TAG = {
    "parts":      "Parts",
    "components": "Components",
    "apparel":    "Apparel",
    "bags":       "Bags",
    "":           "Boards & Sails",
    "sails":      "Sails",
}

# Categories where the type is NOT a suffix in the name (no stripping needed)
NO_STRIP_CATEGORIES = {"", "sails"}


# ── helpers ───────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def parse_price(raw) -> str:
    """Turn '105,74' or '129' or [105.74] into '105.74'."""
    if not raw:
        return ""
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    if not raw:
        return ""
    return str(raw).replace(",", ".").strip()


def base_name(name: str, type_val: str, category: str) -> str:
    """
    Strip the type suffix from the product name when relevant.
    e.g. "Impact Vest Zipped - M" with type "m" → "Impact Vest Zipped"
    For sails/boards the name is already clean, so return as-is.
    """
    if category in NO_STRIP_CATEGORIES or not type_val:
        return name.strip()
    pattern = re.compile(r"\s*[-–]\s*" + re.escape(type_val) + r"\s*$", re.IGNORECASE)
    stripped = pattern.sub("", name).strip()
    return stripped if stripped else name.strip()


def clean_description(desc: str) -> str:
    """
    Remove WP shortcodes, then convert plain-text newlines to HTML.
    Blank lines (double newline) become paragraph breaks <p>...</p>.
    Single newlines become <br>. Result is a single-line HTML string.
    """
    # Strip WP shortcodes
    desc = re.sub(r"\[xyz-ihs[^\]]*\]", "", desc)

    # Normalise line endings
    desc = desc.replace("\r\n", "\n").replace("\r", "\n")

    # Split on blank lines into paragraphs
    paragraphs = re.split(r"\n{2,}", desc)

    html_parts = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Single newlines within a paragraph become <br>
        para = para.replace("\n", "<br>")
        html_parts.append(f"<p>{para}</p>")

    return "".join(html_parts)


# ── Shopify CSV columns ───────────────────────────────────────────────────────

COLUMNS = [
    "Handle",
    "Title",
    "Body (HTML)",
    "Vendor",
    "Tags",
    "Published",
    "Option1 Name",
    "Option1 Value",
    "Variant SKU",
    "Variant Price",
    "Variant Compare At Price",
    "Variant Inventory Tracker",
    "Variant Inventory Qty",
    "Variant Inventory Policy",
    "Variant Fulfillment Service",
    "Variant Barcode",
    "Image Src",
    "Variant Image",
    "Variant Requires Shipping",
    "Variant Taxable",
]


# ── core builder ──────────────────────────────────────────────────────────────

def build_rows(products: list, category: str) -> list[dict]:
    tag = CATEGORY_TAG.get(category, category.capitalize())

    # Group by id, preserving order
    groups: OrderedDict = OrderedDict()
    for p in products:
        pid = p.get("id")
        groups.setdefault(pid, []).append(p)

    rows = []

    for pid, variants in groups.items():
        is_multi = len(variants) > 1

        first = variants[0]
        title = base_name(first["name"], first.get("type", ""), category)
        handle = slugify(title)
        body = clean_description(first.get("description", ""))

        # Collect unique full-res images across all variants for extra image rows
        seen_images = set()

        for i, v in enumerate(variants):
            is_first_row = i == 0

            price = parse_price(v.get("eu rrp +vat", ""))
            compare_price = ""

            try:
                inventory_qty = str(int(float(str(v.get("inventory", "0")))))
            except (ValueError, TypeError):
                inventory_qty = "0"

            variant_image = v.get("image", "")
            if variant_image:
                seen_images.add(variant_image)

            type_val = (v.get("type") or "").strip()

            row = {col: "" for col in COLUMNS}
            row["Handle"] = handle
            row["Variant SKU"] = v.get("sku", "")
            row["Variant Price"] = price
            row["Variant Compare At Price"] = compare_price
            row["Variant Inventory Tracker"] = "shopify"
            row["Variant Inventory Qty"] = inventory_qty
            row["Variant Inventory Policy"] = "deny"
            row["Variant Fulfillment Service"] = "manual"
            row["Variant Barcode"] = v.get("ean", "")
            row["Variant Requires Shipping"] = "TRUE"
            row["Variant Taxable"] = "TRUE"
            row["Image Src"] = variant_image
            row["Variant Image"] = variant_image if is_multi else ""

            if is_multi:
                row["Option1 Name"] = "Title"
                row["Option1 Value"] = type_val if type_val else f"Variant {i+1}"
            else:
                row["Option1 Name"] = "Title"
                row["Option1 Value"] = "Default Title"

            if is_first_row:
                row["Title"] = title
                row["Body (HTML)"] = body
                row["Vendor"] = "Point-7"
                row["Tags"] = tag
                row["Published"] = "TRUE"

            rows.append(row)

        # Extra image rows for medium images not already added
        for v in variants:
            medium = v.get("image medium", "")
            full = v.get("image", "")
            if medium and medium not in seen_images and medium != full:
                img_row = {col: "" for col in COLUMNS}
                img_row["Handle"] = handle
                img_row["Image Src"] = medium
                rows.append(img_row)
                seen_images.add(medium)

    return rows


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python point7-to-shopify.py products.json [output.csv]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "shopify_import.csv"

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        # Single flat list — no category info
        all_rows = build_rows(data, "")
        total_products = len(set(p.get("id") for p in data))
    elif isinstance(data, dict):
        all_rows = []
        total_products = 0
        for category, items in data.items():
            if not isinstance(items, list) or not items:
                continue
            cat_label = CATEGORY_TAG.get(category, repr(category))
            rows = build_rows(items, category)
            unique = len(set(p.get("id") for p in items))
            print(f"  [{cat_label}] {len(items)} entries → {unique} products, {len(rows)} rows")
            all_rows.extend(rows)
            total_products += unique
    else:
        print("Unexpected JSON structure")
        sys.exit(1)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n✓ Wrote {len(all_rows)} rows → {output_file}")
    print(f"  Total unique products: {total_products}")


if __name__ == "__main__":
    main()