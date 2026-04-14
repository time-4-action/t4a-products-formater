# Input Format

The converter expects a JSON file exported from the Point-7 product system.

## Structure

The top-level keys are product categories. Each value is an array of product entries:

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

The empty-string key (`""`) represents boards and sails that don't have a named category. These are tagged as **Boards & Sails** in the output.

## Product Entry Fields

| Field | Type | Example | Description |
|---|---|---|---|
| `name` | string | `"Impact Vest Zipped - M"` | Product name, may include type as suffix |
| `type` | string | `"m"` | Variant type (size, model, etc.) |
| `description` | string | `"Plain text with \\r\\n..."` | Product description with WP shortcodes |
| `image` | string | `"https://point-7.com/.../full.jpg"` | Full-resolution image URL |
| `image medium` | string | `"https://point-7.com/.../full-400x400.jpg"` | Medium-resolution image URL |
| `id` | integer | `1956` | Product ID (shared across variants) |
| `sku` | string | `"23ACIVZM"` | SKU code (may be empty) |
| `ean` | string | `"0782706458544"` | EAN barcode |
| `ex sx3 preorder` | string | `"84"` | Preorder price (not used in output) |
| `sx3 single item` | string | `"84"` | Single item price (not used in output) |
| `eu rrp` | string | `"105,74"` | EU recommended retail price (compare-at price) |
| `eu rrp +vat` | string | `"129"` | EU RRP including VAT (selling price) |
| `inventory` | string | `"1"` | Stock quantity |

## Variant Grouping

Products are grouped by the `id` field. All entries sharing the same `id` become **variants of one Shopify product**, differentiated by their `type` field.

**Example**: three entries with `id: 1956` and types `"s"`, `"m"`, `"l"` become a single product "Impact Vest Zipped" with three size variants.

## Title Stripping

For **parts**, **components**, **apparel**, and **bags** categories, the `type` value appears as a suffix on the `name`. The converter strips this suffix to produce a clean product title:

| Name in JSON | Type | Resulting Title |
|---|---|---|
| `Impact Vest Zipped - M` | `m` | `Impact Vest Zipped` |
| `Boom Clip Carbon 28mm` | `carbon 28mm` | `Boom Clip` |

For **boards/sails** and the unnamed category, names are already clean and no stripping is applied.

## Description Handling

Descriptions may contain:
- **WordPress shortcodes** like `[xyz-ihs snippet="..."]` -- these are stripped
- **`\r\n\r\n`** (double newline) -- converted to paragraph breaks (`<p>...</p>`)
- **`\r\n`** (single newline) -- converted to line breaks (`<br>`)

The output is a single-line HTML string suitable for CSV embedding.
