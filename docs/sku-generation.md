# Auto-Generated SKUs

63 out of 382 product entries in the source data are missing SKUs. The script generates deterministic SKUs for these using a SHA-256 hash.

## Format

```
P7-XXXXXXXX
```

Where `XXXXXXXX` is the first 8 characters (uppercase hex) of the SHA-256 hash.

## Hash Input

The hash is computed from the string `{product_id}:{type}`:

- `product_id` -- the `id` field from the JSON (groups variants together)
- `type` -- the `type` field (differentiates variants within a product)
- If `type` is empty, the variant's index position is used instead

## Determinism

The same input always produces the same SKU. Running the script multiple times on the same data will generate identical SKUs, so Shopify can match them on re-import.

## Identifying Generated SKUs

All auto-generated SKUs start with `P7-`, making them easy to distinguish from original Point-7 SKUs (which use codes like `VARIOTOPPIN`, `23ACIVZM`, etc.).

## Products Missing SKUs

The main groups without SKUs in the source data:

- Qbond sail variants (SALTpro, Slash) -- variants not yet assigned codes
- Boom clips -- 9 variants across different sizes/materials
- Sail+mast bundle combos -- combination products without own SKUs
- Some secondary variants of parts and accessories
