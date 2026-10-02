import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / 'data' / 'products.json'
PRODUCTS = json.loads(DATA.read_text(encoding='utf-8'))

CATEGORIES = ['Electronics','Groceries','Fashion','Home Appliances','Books','Beauty','Sports','Accessories']
CATEGORY_FEATURES = {c: [f'Product category: {c}', 'Budget-aware selection', 'Availability checked', 'Utility score used by optimizer'] for c in CATEGORIES}

for p in PRODUCTS:
    p['reviewCount'] = int(p.get('reviewCount', 0) or 0)
    p['features'] = p.get('features') or CATEGORY_FEATURES.get(p.get('category'), [])
    p['availability'] = bool(p.get('availability', True))
    p['discountPercent'] = int(p.get('discountPercent', 0) or 0)
    p['mrp'] = int(p.get('mrp', round(float(p.get('price', 0)) / max(0.01, 1 - p['discountPercent']/100)))) if p.get('discountPercent') else int(p.get('price', 0))
    # Only the real-photo cache is allowed. The previous generated p1.jpg...p1000.jpg
    # assets are intentionally ignored.
    local = BASE / 'app' / p.get('imageUrl','').lstrip('/') if str(p.get('imageUrl','')).startswith('/static/real_products/') else None
    if not (p.get('realProductImage') and local and local.exists()):
        p['imageUrl'] = '/static/fallback.svg'
        p['image'] = p['imageUrl']
        p['realProductImage'] = False
        p['imageSource'] = 'Real catalog not synced yet — run scripts/sync_real_catalog.py'

EXPECTED_COUNTS = {'Electronics': 121, 'Groceries': 125, 'Fashion': 125, 'Home Appliances': 125, 'Books': 125, 'Beauty': 125, 'Sports': 125, 'Accessories': 125}
if len(PRODUCTS) != 996:
    raise RuntimeError(f'Expected exactly 996 products, found {len(PRODUCTS)}')
counts = {c: sum(1 for p in PRODUCTS if p.get('category') == c) for c in CATEGORIES}
if counts != EXPECTED_COUNTS:
    raise RuntimeError(f'Expected category counts {EXPECTED_COUNTS}, found {counts}')
