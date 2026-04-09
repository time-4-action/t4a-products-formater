# SKU Handling

All SKUs are prefixed with `P7-` to namespace them within Shopify.

## Existing SKUs

Original SKUs from the source data get the prefix prepended:
- `VARIOTOPPIN` becomes `P7-VARIOTOPPIN`
- `23ACIVZM` becomes `P7-23ACIVZM`

## Auto-Generated SKUs

63 out of 382 product entries are missing SKUs. The script generates deterministic ones using a SHA-256 hash.

### Format

```
P7-XXXXXXXX
```

Where `XXXXXXXX` is the first 8 characters (uppercase hex) of the SHA-256 hash.

### Hash Input

The hash is computed from the string `{product_id}:{type}`:

- `product_id` -- the `id` field from the JSON (groups variants together)
- `type` -- the `type` field (differentiates variants within a product)
- If `type` is empty, the variant's index position is used instead

### Determinism

The same input always produces the same SKU. Running the script multiple times on the same data will generate identical SKUs, so Shopify can match them on re-import.

## Products Missing SKUs

The main groups without SKUs in the source data:

- Qbond sail variants (SALTpro, Slash) -- variants not yet assigned codes
- Boom clips -- 9 variants across different sizes/materials
- Sail+mast bundle combos -- combination products without own SKUs
- Some secondary variants of parts and accessories
