# Output Formats

The converter generates two CSV files for Shopify import.

## Product Import CSV

**Default filename**: `shopify_import.csv`

Standard Shopify product import format. Each product occupies one or more rows depending on the number of variants and images.

### Columns

| Column | Source | Example |
|---|---|---|
| Handle | Slugified product title | `impact-vest-zipped` |
| Title | Product name (type suffix stripped) | `Impact Vest Zipped` |
| Body (HTML) | Description converted to HTML | `<p>Lightweight vest...</p>` |
| Vendor | Hardcoded | `POINT-7` |
| Tags | AI-categorized or fallback | `Katalog, Katalog / Windsurf` |
| Published | Hardcoded | `TRUE` |
| Option1 Name | Configurable via `--option1-name` | `Variant` |
| Option1 Value | `type` field or `Default Title` | `M` |
| Variant SKU | Prefixed or auto-generated | `P7-23ACIVZM` |
| Variant Price | `eu rrp +vat` (comma to dot) | `129.00` |
| Variant Compare At Price | `eu rrp` (if different from price) | `105.74` |
| Variant Inventory Tracker | Hardcoded | `shopify` |
| Variant Inventory Qty | `inventory` field | `1` |
| Variant Inventory Policy | Hardcoded | `deny` |
| Variant Fulfillment Service | Hardcoded | `manual` |
| Variant Barcode | `ean` field | `0782706458544` |
| Image Src | Full-resolution image URL | `https://point-7.com/.../full.jpg` |
| Variant Image | Same as Image Src (multi-variant only) | `https://point-7.com/.../full.jpg` |
| Variant Requires Shipping | Hardcoded | `TRUE` |
| Variant Taxable | Hardcoded | `TRUE` |

### Row Types

Each product generates multiple row types:

| Row Type | Contains | When |
|---|---|---|
| **First variant** | Title, Body, Vendor, Tags, Published + variant data | Always (one per product) |
| **Additional variants** | Handle + variant data only | Multi-variant products |
| **Image-only** | Handle + Image Src | Medium-resolution images that differ from full-res |

---

## Inventory Import CSV

**Default filename**: `shopify_import_inventory.csv`

Shopify inventory import format with one row per variant.

### Columns

| Column | Description | Example |
|---|---|---|
| Handle | Product handle | `impact-vest-zipped` |
| Title | Product title (first variant only) | `Impact Vest Zipped` |
| Option1 Name | Configurable via `--option1-name` | `Variant` |
| Option1 Value | Variant type | `M` |
| Option2 Name | Empty | |
| Option2 Value | Empty | |
| Option3 Name | Empty | |
| Option3 Value | Empty | |
| SKU | Variant SKU | `P7-23ACIVZM` |
| HS Code | Empty (not provided in source data) | |
| COO | Empty (country of origin) | |
| POINT-7 | Inventory quantity at the POINT-7 location | `1` |

The inventory filename is derived automatically from the product filename:
`shopify_import.csv` produces `shopify_import_inventory.csv`.
