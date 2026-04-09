# AI Categorization

Products are automatically categorized using the Time-4-Action AI categorization API powered by Gemini 2.5 Flash.

## How It Works

1. The script collects one representative product per unique `id` across all categories
2. Products are sent in batches of 30 to the API (to avoid gateway timeouts)
3. The API matches each product to the best category from your export's category set
4. Category paths are exploded into multi-level Shopify tags

## Tag Exploding

A category path like `Katalog / Windsurf / Boards` is split into tags at every hierarchy level:

```
Katalog, Katalog / Windsurf, Katalog / Windsurf / Boards
```

This allows Shopify to filter products at any level of the category tree.

## Caching

Results are cached in `category_cache.json` to avoid repeated API calls:

- First run: all products are sent to the API, results are cached
- Subsequent runs: cached products are skipped, only new products hit the API
- To force a full re-categorization, delete `category_cache.json`

## Fallback Tags

If the API key or export ID is missing, the script falls back to hardcoded tags based on the JSON category keys:

| JSON Key | Fallback Tag |
|----------|-------------|
| `parts` | Parts |
| `components` | Components |
| `apparel` | Apparel |
| `bags` | Bags |
| `""` (empty) | Boards & Sails |
| `sails` | Sails |

## API Reference

See [CATEGORIZATION_AI.md](../CATEGORIZATION_AI.md) for full API documentation.
