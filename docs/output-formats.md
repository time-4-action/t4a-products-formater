# Output File Formats

The script generates two CSV files for Shopify import.

## Product Import (`shopify_import.csv`)

Standard Shopify product import format with these columns:

| Column | Description |
|--------|-------------|
| Handle | Slugified product title |
| Title | Product name (type suffix stripped for parts/components/apparel/bags) |
| Body (HTML) | Description converted to HTML paragraphs |
| Vendor | `POINT-7` |
| Tags | AI-categorized tags (exploded hierarchy) |
| Published | `TRUE` |
| Option1 Name | `Title` |
| Option1 Value | Variant type, or `Default Title` for single-variant products |
| Variant SKU | Original or auto-generated (`P7-XXXXXXXX`) |
| Variant Price | `eu rrp +vat` (comma converted to dot) |
| Variant Compare At Price | `eu rrp` (only if different from price) |
| Variant Inventory Tracker | `shopify` |
| Variant Inventory Qty | `inventory` from source |
| Variant Inventory Policy | `deny` |
| Variant Fulfillment Service | `manual` |
| Variant Barcode | `ean` |
| Image Src | Full-resolution image URL |
| Variant Image | Same as Image Src (multi-variant only) |
| Variant Requires Shipping | `TRUE` |
| Variant Taxable | `TRUE` |

### Row types

- **First variant row**: Contains Title, Body, Vendor, Tags, Published + variant data
- **Additional variant rows**: Handle + variant data only
- **Image-only rows**: Handle + Image Src (for medium-resolution images)

## Inventory Import (`shopify_import_inventory.csv`)

Shopify inventory import format, one row per variant:

| Column | Description |
|--------|-------------|
| Handle | Product handle |
| Title | Product title (first variant row only) |
| Option1 Name | `Title` |
| Option1 Value | Variant type |
| Option2 Name | Empty |
| Option2 Value | Empty |
| Option3 Name | Empty |
| Option3 Value | Empty |
| SKU | Variant SKU |
| HS Code | Empty |
| COO | Empty |
| POINT-7 | Inventory quantity at the POINT-7 location |

The inventory file name is derived from the product file: `shopify_import.csv` produces `shopify_import_inventory.csv`.
