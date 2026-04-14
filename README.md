# Point-7 to Shopify Converter

> Convert [Point-7](https://point-7.com) product exports into Shopify-ready CSV files with AI-powered categorization.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![No Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)](.)
[![License](https://img.shields.io/badge/license-private-lightgrey)](.)

---

## Overview

This tool takes a **Point-7 products JSON export** and generates two Shopify-compatible CSV files:

| Output File | Purpose |
|---|---|
| `shopify_import.csv` | Full product catalog with variants, images, pricing, and tags |
| `shopify_import_inventory.csv` | Inventory quantities by location |

Products are automatically categorized using the [Time-4-Action AI categorization API](docs/ai-categorization.md) (Gemini 2.5 Flash), with intelligent caching to minimize API calls.

### What it does

- **Groups variants** -- entries sharing the same `id` become one Shopify product with multiple variants
- **AI categorization** -- products are sent to the T4A API for intelligent category assignment
- **Tag hierarchy** -- category paths like `Katalog / Windsurf / Boards` are exploded into multi-level Shopify tags
- **SKU management** -- all SKUs prefixed with `P7-`; missing SKUs are auto-generated via SHA-256 hashing
- **HTML conversion** -- descriptions are cleaned of WordPress shortcodes and converted to HTML
- **Dual image support** -- full-resolution and medium images are included as separate rows

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd t4a-products-formater
cp .env.example .env
```

Edit `.env` with your credentials:

```env
WEBHOOK_API_KEY=your-webhook-api-key-here
EXPORT_ID=your-export-id-here
```

### 2. Run the converter

```bash
python point7-to-shopify.py products.json
```

This generates `shopify_import.csv` and `shopify_import_inventory.csv` in the current directory.

### 3. Import into Shopify

1. Go to **Shopify Admin > Products > Import**
2. Upload `shopify_import.csv`
3. Go to **Settings > Locations > Import inventory**
4. Upload `shopify_import_inventory.csv`

---

## Usage

```
python point7-to-shopify.py <input.json> [output.csv] [--option1-name VALUE]
```

| Argument | Default | Description |
|---|---|---|
| `input.json` | *(required)* | Path to the Point-7 products JSON file |
| `output.csv` | `shopify_import.csv` | Output product CSV path |
| `--option1-name` | `Variant` | Value for the Option1 Name column |

The inventory CSV filename is derived automatically: `output.csv` produces `output_inventory.csv`.

---

## Input Format

The source JSON groups products by category:

```json
{
  "parts":      [ ... ],
  "components": [ ... ],
  "apparel":    [ ... ],
  "bags":       [ ... ],
  "":           [ ... ],
  "sails":      [ ... ]
}
```

Each product entry contains:

```json
{
  "name": "Impact Vest Zipped - M",
  "type": "m",
  "description": "Product description with \\r\\n newlines",
  "image": "https://point-7.com/.../full.jpg",
  "image medium": "https://point-7.com/.../full-400x400.jpg",
  "id": 1956,
  "sku": "23ACIVZM",
  "ean": "0782706458544",
  "eu rrp": "105,74",
  "eu rrp +vat": "129",
  "inventory": "1"
}
```

> See [docs/input-format.md](docs/input-format.md) for the full field reference.

---

## How It Works

```
products.json
     |
     v
 ┌───────────────────┐
 │  Group by id       │  Same id = one product, multiple variants
 └─────────┬─────────┘
           v
 ┌───────────────────┐
 │  AI Categorization │  Batch API calls (30/batch), cached locally
 └─────────┬─────────┘
           v
 ┌───────────────────┐
 │  Transform        │  Title stripping, HTML conversion, SKU generation
 └─────────┬─────────┘
           v
   ┌───────┴───────┐
   v               v
shopify_import   shopify_import
    .csv         _inventory.csv
```

### Key transformations

| Step | Description | Details |
|---|---|---|
| Variant grouping | Entries with the same `id` become variants | Differentiated by `type` field |
| Title stripping | Type suffix removed from product name | `"Impact Vest Zipped - M"` + type `"m"` = `"Impact Vest Zipped"` |
| AI categorization | Products sent to T4A API | Results cached in `category_cache.json` |
| Tag exploding | Category paths split into hierarchy | `A / B / C` becomes tags: `A`, `A / B`, `A / B / C` |
| SKU prefixing | All SKUs get `P7-` prefix | `23ACIVZM` becomes `P7-23ACIVZM` |
| SKU generation | Missing SKUs auto-generated | SHA-256 hash of `{id}:{type}` = `P7-XXXXXXXX` |
| Description cleanup | WP shortcodes stripped, newlines to HTML | `\r\n\r\n` = `<p>`, `\r\n` = `<br>` |

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `WEBHOOK_API_KEY` | For AI categorization | API key for the T4A categorization endpoint |
| `EXPORT_ID` | For AI categorization | Which export's category set to use |

If either is missing, the script falls back to hardcoded category tags based on JSON structure keys.

### Category Cache

AI categorization results are stored in `category_cache.json`:

- **First run**: all products are categorized via the API
- **Subsequent runs**: only new/uncached products hit the API
- **Force re-categorization**: delete `category_cache.json`

---

## Current Dataset Stats

```
Category         Entries   Products   CSV Rows
─────────────────────────────────────────────
Parts                 41        15         55
Components           108        25        133
Apparel                3         2          5
Bags                  11         9         20
Boards & Sails       197        23        220
Sails                 22         3         25
─────────────────────────────────────────────
Total                382        77        458
```

---

## Documentation

| Document | Description |
|---|---|
| [Input Format](docs/input-format.md) | Source JSON structure and field reference |
| [Output Formats](docs/output-formats.md) | Shopify CSV column specifications |
| [AI Categorization](docs/ai-categorization.md) | How the T4A API categorization works |
| [SKU Generation](docs/sku-generation.md) | SKU prefixing and auto-generation logic |
| [API Reference](docs/api-reference.md) | Full T4A categorization API documentation |

---

## Requirements

- **Python 3.10+**
- No external dependencies (standard library only: `json`, `csv`, `hashlib`, `urllib`, `re`, `os`, `argparse`)
- A [Time-4-Action](https://time-4-action.com) API key and export ID (optional -- falls back to hardcoded tags)
