# Point-7 to Shopify Converter

Converts a Point-7 products JSON export into Shopify-compatible CSV files for product import and inventory management.

## Quick Start

1. Copy `.env.example` to `.env` and fill in your credentials
2. Run the converter:

```bash
python point7-to-shopify.py products.json shopify_import.csv
```

This generates two files:
- `shopify_import.csv` -- product import file
- `shopify_import_inventory.csv` -- inventory import file

## Requirements

- Python 3.10+
- No external dependencies (uses only standard library)
- A Time-4-Action API key and export ID (for AI categorization)

## Configuration

Environment variables in `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `WEBHOOK_API_KEY` | Yes | API key for the AI categorization endpoint |
| `EXPORT_ID` | Yes | Export ID whose category set to use for categorization |

If either variable is missing, the script falls back to hardcoded category tags based on the JSON structure.
