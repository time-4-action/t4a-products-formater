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
import os
import hashlib
import urllib.request
import urllib.error
from collections import OrderedDict


# ── AI Categorization ────────────────────────────────────────────────────────

API_URL = "https://api.time-4-action.com/api/export/webhooks/categorize"
EXPORT_ID = None  # loaded from .env
BATCH_LIMIT = 30  # products per API request (API processes 30 internally, avoid timeouts)
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "category_cache.json")


def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def load_env() -> dict:
    """Load key=value pairs from .env file in the same directory as the script."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    env = {}
    if not os.path.exists(env_path):
        return env
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip()
    return env


def explode_category_tags(category_name: str) -> str:
    """
    Explode 'Windsurfing / Boards' into 'Windsurfing, Windsurfing / Boards'.
    Explode 'A / B / C' into 'A, A / B, A / B / C'.
    """
    parts = [p.strip() for p in category_name.split("/")]
    tags = []
    for i in range(1, len(parts) + 1):
        tags.append(" / ".join(parts[:i]))
    return ", ".join(tags)


def categorize_products(unique_products: list[dict], api_key: str, export_id: str = "") -> dict:
    """
    Call the AI categorization API and return a mapping of product code -> exploded tags string.
    unique_products: list of dicts with at least 'code' and 'name'.
    Returns: {code: "Tag1, Tag1 / Tag2, ..."}
    """
    category_map = {}

    for batch_start in range(0, len(unique_products), BATCH_LIMIT):
        batch = unique_products[batch_start:batch_start + BATCH_LIMIT]

        payload = json.dumps({
            "exportId": export_id,
            "products": batch,
        }).encode("utf-8")

        req = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"  [WARN] Categorization API error {e.code}: {body}")
            continue
        except Exception as e:
            print(f"  [WARN] Categorization API request failed: {e}")
            continue

        for result in data.get("results", []):
            code = result["code"]
            cat_name = result.get("categoryName", "")
            if cat_name:
                category_map[code] = explode_category_tags(cat_name)

    return category_map


# ── Category → Shopify tag mapping (fallback) ────────────────────────────────

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

def generate_sku(product_id, type_val: str) -> str:
    """Generate a deterministic SKU from product id + TypeURLA. Same input = same output every run."""
    key = f"{product_id}:{type_val}".encode("utf-8")
    h = hashlib.sha256(key).hexdigest()[:8].upper()
    return f"P7-{h}"


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

def build_rows(products: list, category: str, category_map: dict = None) -> list[dict]:
    fallback_tag = CATEGORY_TAG.get(category, category.capitalize())

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

            sku = v.get("sku", "").strip()
            if not sku:
                sku = generate_sku(pid, type_val or str(i))
            elif not sku.startswith("P7-"):
                sku = f"P7-{sku}"

            row = {col: "" for col in COLUMNS}
            row["Handle"] = handle
            row["Variant SKU"] = sku
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
                row["Vendor"] = "POINT-7"
                # Use AI-categorized tags if available, otherwise fallback
                ai_tag = category_map.get(str(pid), "") if category_map else ""
                row["Tags"] = ai_tag if ai_tag else fallback_tag
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

def collect_unique_products(data) -> list[dict]:
    """
    Collect one representative product per unique id across all categories,
    formatted for the categorization API (code, name, description, brand).
    """
    seen = {}
    items_list = []

    if isinstance(data, list):
        items_list = [("", data)]
    elif isinstance(data, dict):
        items_list = list(data.items())

    for _category, items in items_list:
        if not isinstance(items, list):
            continue
        for p in items:
            pid = str(p.get("id", ""))
            if pid and pid not in seen:
                entry = {
                    "code": pid,
                    "name": p.get("name", ""),
                }
                desc = p.get("description", "")
                if desc:
                    entry["description"] = desc
                entry["brand"] = "POINT-7"
                seen[pid] = entry

    return list(seen.values())


def main():
    if len(sys.argv) < 2:
        print("Usage: python point7-to-shopify.py products.json [output.csv]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "shopify_import.csv"

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ── AI Categorization step ────────────────────────────────────────────
    env = load_env()
    api_key = env.get("WEBHOOK_API_KEY", "")
    export_id = env.get("EXPORT_ID", "")
    category_map = {}

    if api_key and export_id:
        unique = collect_unique_products(data)
        cache = load_cache()

        # Split into cached and uncached
        uncached = [p for p in unique if p["code"] not in cache]
        for p in unique:
            if p["code"] in cache:
                category_map[p["code"]] = cache[p["code"]]

        print(f"  {len(unique)} unique products: {len(unique) - len(uncached)} cached, {len(uncached)} to categorize")

        if uncached:
            print(f"  Calling AI categorization API (exportId: {export_id})...")
            new_categories = categorize_products(uncached, api_key, export_id)
            category_map.update(new_categories)
            cache.update(new_categories)
            save_cache(cache)
            print(f"  [OK] Got {len(new_categories)} new categories from API")
        else:
            print(f"  [OK] All products served from cache")
    else:
        print("  [WARN] Missing WEBHOOK_API_KEY or EXPORT_ID in .env -- skipping AI categorization, using fallback tags")

    # ── Build CSV rows ────────────────────────────────────────────────────
    if isinstance(data, list):
        all_rows = build_rows(data, "", category_map)
        total_products = len(set(p.get("id") for p in data))
    elif isinstance(data, dict):
        all_rows = []
        total_products = 0
        for category, items in data.items():
            if not isinstance(items, list) or not items:
                continue
            cat_label = CATEGORY_TAG.get(category, repr(category))
            rows = build_rows(items, category, category_map)
            unique = len(set(p.get("id") for p in items))
            print(f"  [{cat_label}] {len(items)} entries -> {unique} products, {len(rows)} rows")
            all_rows.extend(rows)
            total_products += unique
    else:
        print("Unexpected JSON structure")
        sys.exit(1)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n[OK] Wrote {len(all_rows)} rows -> {output_file}")
    print(f"  Total unique products: {total_products}")

    # ── Inventory CSV ─────────────────────────────────────────────────────
    inventory_file = output_file.replace(".csv", "_inventory.csv")
    inv_columns = [
        "Handle", "Title",
        "Option1 Name", "Option1 Value",
        "Option2 Name", "Option2 Value",
        "Option3 Name", "Option3 Value",
        "SKU", "HS Code", "COO", "POINT-7",
    ]
    inv_rows = []
    for row in all_rows:
        # Skip image-only rows (no SKU, no Option1 Value)
        if not row.get("Variant SKU") and not row.get("Option1 Value"):
            continue
        inv_rows.append({
            "Handle": row["Handle"],
            "Title": row.get("Title", ""),
            "Option1 Name": row.get("Option1 Name", ""),
            "Option1 Value": row.get("Option1 Value", ""),
            "Option2 Name": "",
            "Option2 Value": "",
            "Option3 Name": "",
            "Option3 Value": "",
            "SKU": row.get("Variant SKU", ""),
            "HS Code": "",
            "COO": "",
            "POINT-7": row.get("Variant Inventory Qty", "0"),
        })

    with open(inventory_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=inv_columns)
        writer.writeheader()
        writer.writerows(inv_rows)

    print(f"[OK] Wrote {len(inv_rows)} rows -> {inventory_file}")


if __name__ == "__main__":
    main()