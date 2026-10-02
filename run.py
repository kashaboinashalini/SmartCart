from app import create_app
from app.data import PRODUCTS

real_count = sum(1 for p in PRODUCTS if p.get('realProductImage') and str(p.get('imageUrl','')).startswith('/static/real_products/'))
if real_count != 996:
    raise SystemExit(
        f'SmartCart is protected from starting with fake/generated product images. '
        f'Only {real_count}/996 real catalog photos are ready. '
        f'Run: python scripts/sync_real_catalog.py'
    )

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5174, debug=True)
