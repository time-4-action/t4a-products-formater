#!/usr/bin/env bash
# Regenerates the Shopify CSVs from products.json and category_cache.json only,
# without calling the categorization API, into OUT_DIR (default: dist/).
#
#   scripts/build.sh            build into dist/
#   scripts/build.sh --check    also fail if the committed CSVs differ from the build
#
# Runs in a temporary copy, so it never touches your .env or category_cache.json.
# It fails if a product in products.json has no cached category: run the
# converter locally with a real .env first, then commit the updated cache.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT_DIR=${OUT_DIR:-$ROOT/dist}
PYTHON=${PYTHON:-python3}

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
cp "$ROOT/point7-to-shopify.py" "$ROOT/products.json" "$ROOT/category_cache.json" "$WORK/"

# Every product must be in the cache, otherwise the converter would call the API.
"$PYTHON" - "$WORK" <<'PY'
import importlib.util, json, pathlib, sys
work = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("converter", work / "point7-to-shopify.py")
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)
data = json.loads((work / "products.json").read_text(encoding="utf-8"))
cache = json.loads((work / "category_cache.json").read_text(encoding="utf-8"))
missing = [p for p in converter.collect_unique_products(data) if p["code"] not in cache]
for p in missing:
    print(f"::error::product {p['code']} ({p['name']}) has no entry in category_cache.json")
if missing:
    print("Run the converter locally with a real .env to categorize them, then commit category_cache.json.")
    sys.exit(1)
PY

# The converter only reads the cache when both values are set. They are never
# sent anywhere: the check above guarantees every product is cached.
printf 'WEBHOOK_API_KEY=cache-only\nEXPORT_ID=cache-only\n' > "$WORK/.env"
(cd "$WORK" && "$PYTHON" point7-to-shopify.py products.json shopify_import.csv)

mkdir -p "$OUT_DIR"
cp "$WORK/shopify_import.csv" "$WORK/shopify_import_inventory.csv" "$OUT_DIR/"
echo "built into $OUT_DIR"

if [ "${1:-}" = "--check" ]; then
  status=0
  for f in shopify_import.csv shopify_import_inventory.csv; do
    if ! cmp -s "$ROOT/$f" "$OUT_DIR/$f"; then
      echo "::error file=$f::$f is out of date with products.json / point7-to-shopify.py. Run the converter and commit the result."
      diff -u "$ROOT/$f" "$OUT_DIR/$f" | head -40 || true
      status=1
    fi
  done
  [ "$status" = 0 ] && echo "committed CSVs are up to date"
  exit $status
fi
