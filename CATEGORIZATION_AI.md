# AI Categorization API for Third-Party Products

Categorize any products using the AI categorization engine (Gemini 2.5 Flash) against your existing category sets -- without importing them into the system.

## Endpoint

```
POST /api/export/webhooks/categorize
```

### Authentication

Requires the `x-api-key` header with your `WEBHOOK_API_KEY`.

```
x-api-key: your-webhook-api-key
```

---

## Request

### Headers

| Header       | Required | Description               |
|--------------|----------|---------------------------|
| Content-Type | Yes      | `application/json`        |
| x-api-key    | Yes      | Your `WEBHOOK_API_KEY`    |

### Body

```json
{
  "exportId": "tris",
  "products": [
    {
      "code": "SKU-001",
      "name": "Wireless Bluetooth Headphones",
      "description": "Over-ear noise cancelling headphones with 30h battery",
      "brand": "SoundMax",
      "tags": ["audio", "wireless"]
    },
    {
      "code": "SKU-002",
      "name": "USB-C Charging Cable 2m",
      "description": "Braided nylon fast-charging cable"
    }
  ]
}
```

### Field Reference

| Field           | Type     | Required | Description |
|-----------------|----------|----------|-------------|
| `exportId`      | string   | Yes      | The ID of an existing export whose category set should be used. This is the `_id` of a document in the `exports` collection (or whatever string you used as `exportId` when creating categories). |
| `products`      | array    | Yes      | Array of product objects to categorize (max **300** per request). |
| `products[].code` | string | Yes      | A unique identifier for the product (used to match results back). |
| `products[].name` | string | Yes      | The product name -- this is the primary text the AI uses. |
| `products[].description` | string | No | Product description -- strongly recommended for better accuracy. |
| `products[].brand` | string | No | Brand name. |
| `products[].tags` | array | No | Tags or keywords. |
| `products[].price` | number | No | Price (can help disambiguate categories). |
| `products[].child_products` | array | No | Variants of this product. The AI reads them for extra context but only categorizes the parent. |

You can include **any additional fields** on each product object. The AI receives the full object, so more context = better categorization. Only `code` and `name` are strictly required.

---

## Response

### 200 OK

```json
{
  "results": [
    {
      "code": "SKU-001",
      "categoryId": "683a1f2e4b5c6d7e8f901234",
      "categoryName": "Electronics / Audio"
    },
    {
      "code": "SKU-002",
      "categoryId": "683a1f2e4b5c6d7e8f905678",
      "categoryName": "Accessories / Cables"
    }
  ]
}
```

| Field          | Type   | Description |
|----------------|--------|-------------|
| `results`      | array  | One entry per successfully categorized product. |
| `results[].code` | string | The `code` you sent in the request. |
| `results[].categoryId` | string | The MongoDB `_id` of the matched category. |
| `results[].categoryName` | string | The human-readable category label. |

> Products that the AI could not confidently categorize may be assigned to a fallback category (typically "Ostalo" / "Other") if one exists in your category set.

### Error Responses

| Status | When |
|--------|------|
| 400    | Missing `exportId`, missing/empty `products`, product missing `code` or `name`, or more than 300 products. |
| 401    | Missing or invalid `x-api-key`. |
| 500    | No categories found for the given `exportId`, or an AI processing error. |

---

## How It Works

1. You send your products + an `exportId`.
2. The API fetches all categories from the `categories` collection for that `exportId`.
3. Products are sent to Gemini 2.5 Flash in batches of 30 with the category list as context.
4. The AI maps each product to the best-matching category.
5. Results are returned synchronously. **Nothing is saved to the database** -- your products and the categorization results are not persisted.

---

## Examples

### curl

```bash
curl -X POST https://your-server.com/api/export/webhooks/categorize \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-webhook-api-key" \
  -d '{
    "exportId": "tris",
    "products": [
      { "code": "P1", "name": "Red Running Shoes", "description": "Lightweight mesh running shoes for men" },
      { "code": "P2", "name": "Stainless Steel Water Bottle 750ml" },
      { "code": "P3", "name": "Organic Green Tea 100g", "brand": "TeaHouse", "tags": ["organic", "tea", "beverages"] }
    ]
  }'
```

### JavaScript (fetch)

```javascript
const response = await fetch('https://your-server.com/api/export/webhooks/categorize', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': 'your-webhook-api-key',
  },
  body: JSON.stringify({
    exportId: 'tris',
    products: [
      { code: 'P1', name: 'Red Running Shoes', description: 'Lightweight running shoes' },
      { code: 'P2', name: 'Stainless Steel Water Bottle 750ml' },
    ],
  }),
});

const { results } = await response.json();
// results = [{ code: 'P1', categoryId: '...', categoryName: '...' }, ...]
```

### Python (requests)

```python
import requests

resp = requests.post(
    "https://your-server.com/api/export/webhooks/categorize",
    headers={"x-api-key": "your-webhook-api-key"},
    json={
        "exportId": "tris",
        "products": [
            {"code": "P1", "name": "Red Running Shoes", "description": "Lightweight running shoes"},
            {"code": "P2", "name": "Stainless Steel Water Bottle 750ml"},
        ],
    },
)

results = resp.json()["results"]
```

---

## Prerequisites

Before calling this endpoint you need:

1. **An export with categories** -- create an export via `POST /api/export/exports` and add categories to it via `POST /api/export/categories` or `POST /api/export/categories/import`. The `exportId` you pass to the categorize endpoint is the `_id` of that export (or the string you used as `exportId` when bulk-importing categories).

2. **A valid `WEBHOOK_API_KEY`** -- set in the server's environment variables and passed via `x-api-key` header.

---

## Limits

| Constraint | Value |
|------------|-------|
| Max products per request | 300 |
| Batch size (internal) | 30 products per AI call |
| Rate limiting | None (be reasonable -- each request costs Gemini API tokens) |

For larger datasets, split into multiple requests of up to 300 products each.
