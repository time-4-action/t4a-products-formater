# AI Categorization

Products are automatically categorized using the [Time-4-Action AI categorization API](api-reference.md), powered by **Gemini 2.5 Flash**.

## How It Works

```
1. Collect one representative product per unique id
2. Send products to T4A API in batches of 30
3. API matches each product to the best category
4. Cache results locally in category_cache.json
5. Explode category paths into multi-level Shopify tags
```

### Step by step

1. **Collect** -- The script picks one representative entry per unique `id` across all categories
2. **Batch** -- Products are sent in batches of 30 to avoid gateway timeouts
3. **Categorize** -- The API matches each product to a category from your export's category set
4. **Cache** -- Results are stored in `category_cache.json` for future runs
5. **Explode** -- Category paths are split into hierarchical tags

## Tag Exploding

A category path like `Katalog / Windsurf / Boards` is split into tags at every level of the hierarchy:

```
Katalog
Katalog / Windsurf
Katalog / Windsurf / Boards
```

This enables Shopify collection filtering at any depth of the category tree.

## Caching

Results are cached in `category_cache.json` to avoid redundant API calls:

| Scenario | Behavior |
|---|---|
| First run | All products sent to API, results cached |
| Subsequent runs | Only new/uncached products hit the API |
| Force re-categorization | Delete `category_cache.json` |

The cache maps product IDs to their assigned category names.

## Fallback Tags

If the `WEBHOOK_API_KEY` or `EXPORT_ID` environment variables are missing, the script falls back to simple tags based on JSON category keys:

| JSON Key | Fallback Tag |
|---|---|
| `parts` | Parts |
| `components` | Components |
| `apparel` | Apparel |
| `bags` | Bags |
| `""` (empty) | Boards & Sails |
| `sails` | Sails |

No tag exploding is applied in fallback mode -- products receive a single flat tag.

## API Reference

For full API documentation including request/response formats, authentication, and code examples, see [API Reference](api-reference.md).
