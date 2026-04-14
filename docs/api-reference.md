# API Reference

Full documentation for the Time-4-Action AI categorization endpoint.

## Endpoint

```
POST https://api.time-4-action.com/api/export/webhooks/categorize
```

## Authentication

Requires the `x-api-key` header with your webhook API key.

```
x-api-key: your-webhook-api-key
```

## Request

### Headers

| Header | Required | Value |
|---|---|---|
| `Content-Type` | Yes | `application/json` |
| `x-api-key` | Yes | Your `WEBHOOK_API_KEY` |

### Body

```json
{
  "exportId": "your-export-id",
  "products": [
    {
      "code": "SKU-001",
      "name": "Wireless Bluetooth Headphones",
      "description": "Over-ear noise cancelling headphones with 30h battery",
      "brand": "SoundMax",
      "tags": ["audio", "wireless"]
    }
  ]
}
```

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `exportId` | string | Yes | ID of the export whose category set to use |
| `products` | array | Yes | Products to categorize (max 300 per request) |
| `products[].code` | string | Yes | Unique identifier for matching results back |
| `products[].name` | string | Yes | Product name (primary text for AI) |
| `products[].description` | string | No | Product description (improves accuracy) |
| `products[].brand` | string | No | Brand name |
| `products[].tags` | array | No | Tags or keywords |
| `products[].price` | number | No | Price (helps disambiguate categories) |
| `products[].child_products` | array | No | Variants (AI reads for context, categorizes parent only) |

Additional fields are accepted and passed to the AI for better context.

## Response

### 200 OK

```json
{
  "results": [
    {
      "code": "SKU-001",
      "categoryId": "683a1f2e4b5c6d7e8f901234",
      "categoryName": "Electronics / Audio"
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `results` | array | One entry per categorized product |
| `results[].code` | string | The `code` from the request |
| `results[].categoryId` | string | MongoDB `_id` of the matched category |
| `results[].categoryName` | string | Human-readable category label |

Products that the AI cannot confidently categorize may be assigned to a fallback category (typically "Ostalo" / "Other").

### Error Responses

| Status | Cause |
|---|---|
| 400 | Missing `exportId`, missing/empty `products`, product missing `code` or `name`, or >300 products |
| 401 | Missing or invalid `x-api-key` |
| 500 | No categories found for the `exportId`, or AI processing error |

## How It Works

1. You send products + an `exportId`
2. The API fetches all categories for that export
3. Products are sent to Gemini 2.5 Flash in batches of 30
4. The AI maps each product to the best-matching category
5. Results are returned synchronously -- nothing is persisted

## Examples

### curl

```bash
curl -X POST https://api.time-4-action.com/api/export/webhooks/categorize \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-webhook-api-key" \
  -d '{
    "exportId": "your-export-id",
    "products": [
      {
        "code": "P1",
        "name": "Red Running Shoes",
        "description": "Lightweight mesh running shoes"
      }
    ]
  }'
```

### Python

```python
import urllib.request
import json

data = json.dumps({
    "exportId": "your-export-id",
    "products": [
        {"code": "P1", "name": "Red Running Shoes", "description": "Lightweight running shoes"},
        {"code": "P2", "name": "Stainless Steel Water Bottle 750ml"},
    ],
}).encode()

req = urllib.request.Request(
    "https://api.time-4-action.com/api/export/webhooks/categorize",
    data=data,
    headers={
        "Content-Type": "application/json",
        "x-api-key": "your-webhook-api-key",
    },
)

with urllib.request.urlopen(req) as resp:
    results = json.loads(resp.read())["results"]
```

### JavaScript

```javascript
const response = await fetch(
  "https://api.time-4-action.com/api/export/webhooks/categorize",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": "your-webhook-api-key",
    },
    body: JSON.stringify({
      exportId: "your-export-id",
      products: [
        { code: "P1", name: "Red Running Shoes", description: "Lightweight running shoes" },
      ],
    }),
  }
);

const { results } = await response.json();
```

## Limits

| Constraint | Value |
|---|---|
| Max products per request | 300 |
| Internal batch size | 30 products per AI call |
| Rate limiting | None (be reasonable -- each request costs Gemini API tokens) |

## Prerequisites

1. **An export with categories** -- create via the T4A export API and add categories to it. The `exportId` is the `_id` of that export document.
2. **A valid `WEBHOOK_API_KEY`** -- set in the server environment and passed via `x-api-key` header.
