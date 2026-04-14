# SKU Handling

All SKUs are prefixed with `P7-` to namespace Point-7 products within Shopify and avoid collisions with other vendors.

## Existing SKUs

Original SKUs from the source data are simply prefixed:

```
VARIOTOPPIN  ->  P7-VARIOTOPPIN
23ACIVZM     ->  P7-23ACIVZM
```

## Auto-Generated SKUs

Some product entries (63 out of 382 in the current dataset) are missing SKUs. The script generates **deterministic** SKUs using SHA-256 hashing.

### Format

```
P7-XXXXXXXX
```

Where `XXXXXXXX` is the first 8 characters of the SHA-256 hash in uppercase hexadecimal.

### Hash Input

The hash is computed from the string `{product_id}:{type}`:

| Component | Source | Purpose |
|---|---|---|
| `product_id` | `id` field from JSON | Groups variants of the same product |
| `type` | `type` field | Differentiates variants within a product |

If `type` is empty, the variant's index position within the group is used instead.

### Determinism

The same input always produces the same SKU. Running the converter multiple times on unchanged data generates identical SKUs, ensuring Shopify can match products on re-import without creating duplicates.

### Example

```
Input:  "1956:m"
SHA-256: a3b2c1d4e5f67890...
SKU:    P7-A3B2C1D4
```

## Products Without Source SKUs

The main product groups missing SKUs in the current dataset:

| Group | Description |
|---|---|
| Qbond sail variants | SALTpro, Slash variants not yet assigned codes |
| Boom clips | 9 variants across different sizes and materials |
| Sail+mast bundles | Combination products without dedicated SKUs |
| Miscellaneous | Some secondary variants of parts and accessories |
