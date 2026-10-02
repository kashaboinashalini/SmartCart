"""Build a real-photo catalog with 996 products.

The script reads public e-commerce dataset samples that expose product image URLs,
selects 121 Electronics products and 125 products in each other SmartCart category, downloads and validates each
photograph locally, then writes data/products.json. It never creates or substitutes
illustrations. If it cannot obtain 125 real-image products for a category, it stops.
"""
import csv, io, json, re, sys, time
from pathlib import Path
from urllib.parse import urlparse
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'products.json'
IMAGE_DIR = ROOT / 'app' / 'static' / 'real_products'
TARGETS = {'Electronics': 121, 'Groceries': 125, 'Fashion': 125, 'Home Appliances': 125, 'Books': 125, 'Beauty': 125, 'Sports': 125, 'Accessories': 125}
CATEGORIES = ['Electronics','Groceries','Fashion','Home Appliances','Books','Beauty','Sports','Accessories']
SOURCES = [
    ('Amazon', 'https://raw.githubusercontent.com/luminati-io/Free-datasets/main/amazon-products.csv', None),
    ('Walmart', 'https://raw.githubusercontent.com/luminati-io/Free-datasets/main/walmart-products.csv', None),
    ('Target', 'https://raw.githubusercontent.com/luminati-io/Free-datasets/main/target-products.csv', None),
    ('Shein', 'https://raw.githubusercontent.com/luminati-io/Free-datasets/main/shein-products.csv', None),
    ('Shopee', 'https://raw.githubusercontent.com/luminati-io/Free-datasets/main/shopee-products.csv', None),
    ('Amazon Books', 'https://raw.githubusercontent.com/luminati-io/Amazon-popular-books-dataset/main/Amazon_popular_books_dataset.csv', 'Books'),
    ('Home Depot', 'https://raw.githubusercontent.com/luminati-io/Home-Depot-dataset-sample/main/Home%20Depot%20US%20.csv', 'Home Appliances'),
    ('H&M', 'https://raw.githubusercontent.com/luminati-io/HM-dataset-sample/main/H%26M-dataset-sample.csv', 'Fashion'),
    ('Myntra', 'https://raw.githubusercontent.com/luminati-io/myntra-dataset-sample/main/Myntra%20products%20.csv', 'Fashion'),
    ('eBay', 'https://raw.githubusercontent.com/luminati-io/eBay-dataset-sample/main/eBay-dataset-sample.csv', None),
]
RULES = {
 'Electronics': r'phone|smartphone|tablet|laptop|computer|monitor|keyboard|mouse|headphone|earbud|speaker|camera|television|tv|router|printer|charger|power bank|ssd|hard drive|usb|gaming|console|smartwatch|bluetooth|projector|microphone|webcam|drone|electronics|electrical|adapter|cable|cord|power strip|extension|battery|batteries|led|bulb|light|resistor|capacitor|transistor|diode|breadboard|arduino|raspberry pi|solder|sensor|relay|switch|component|circuit|voltage|amplifier|receiver|transmitter|wireless',
 'Groceries': r'grocery|groceries|food|snack|cereal|rice|flour|atta|dal|lentil|pasta|noodle|sauce|oil|spice|tea|coffee|juice|drink|beverage|water|chocolate|biscuit|cookie|chips|candy|bread|breakfast|pantry',
 'Fashion': r'clothing|apparel|dress|shirt|t-shirt|jean|pant|trouser|skirt|top|jacket|coat|hoodie|sweater|kurta|saree|legging|shorts|fashion|blouse|underwear|bra|sock|h&m|myntra|shein',
 'Home Appliances': r'appliance|refrigerator|fridge|washing machine|dryer|microwave|oven|air fryer|vacuum|mixer|blender|toaster|kettle|coffee maker|dishwasher|air conditioner|heater|fan|iron|purifier|humidifier|dehumidifier|home appliance|home depot',
 'Books': r'book|books|novel|hardcover|paperback|kindle|textbook|workbook|journal|comic|manga|literature|biography|cookbook|guide book|children.?s book',
 'Beauty': r'beauty|makeup|cosmetic|skincare|skin care|lipstick|foundation|mascara|eyeliner|serum|moisturizer|cream|lotion|shampoo|conditioner|hair care|perfume|fragrance|deodorant|face wash|sunscreen|nail|personal care',
 'Sports': r'sport|sports|fitness|gym|yoga|football|soccer|cricket|bat|ball|tennis|badminton|basketball|volleyball|golf|cycling|bicycle|running|training|exercise|dumbbell|treadmill|outdoor|camping|hiking|swimming',
 'Accessories': r'accessor|bag|backpack|handbag|wallet|purse|belt|cap|hat|sunglass|glasses|watch|jewelry|jewellery|necklace|bracelet|earring|luggage|suitcase|travel pouch|keychain|passport|phone case|card holder|tote|duffel|scarf|shawl|headband|hair clip|scrunchie|ring|brooch|tie|bow tie|crossbody|clutch|fanny pack|ebay',
}

SESSION = requests.Session()
SESSION.headers.update({'User-Agent':'SmartCart-Real-Catalog/3.0 (academic project)'})


def get(row, *keys):
    for k in keys:
        v = row.get(k, '')
        if v is not None and str(v).strip():
            return str(v).strip()
    return ''


def num(v, default=0.0):
    m = re.search(r'\d+(?:[.,]\d+)?', str(v or '').replace(',', ''))
    return float(m.group(0)) if m else default


def image_url(row):
    for k in ('image_url','main_image','image','image_urls','images','imageURL','imageURLHighRes'):
        v = get(row, k)
        # Handles a plain URL as well as JSON/list-like text containing URLs.
        m = re.search(r'https?://[^\s"\'\]\}]+', v)
        if m:
            return m.group(0).replace('\\u0026','&').rstrip(',')
    return ''


def category(row, forced):
    if forced:
        return forced
    text = ' '.join(str(v) for v in row.values()).lower()
    scores = {c: len(re.findall(pattern, text, re.I)) for c, pattern in RULES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else None


def fetch_csv(url):
    r = SESSION.get(url, timeout=60)
    r.raise_for_status()
    return list(csv.DictReader(io.StringIO(r.content.decode('utf-8-sig', errors='replace'))))


def image_type(content, content_type=''):
    c = content[:16]
    if c.startswith(b'\xff\xd8\xff'): return 'jpg'
    if c.startswith(b'\x89PNG\r\n\x1a\n'): return 'png'
    if c.startswith(b'RIFF') and b'WEBP' in content[:16]: return 'webp'
    if c.startswith(b'GIF87a') or c.startswith(b'GIF89a'): return 'gif'
    if content_type.startswith('image/jpeg'): return 'jpg'
    if content_type.startswith('image/png'): return 'png'
    if content_type.startswith('image/webp'): return 'webp'
    return None


def download_image(url, dest_base):
    try:
        r = SESSION.get(url, timeout=30, allow_redirects=True)
        if r.status_code != 200 or not r.content:
            return None
        kind = image_type(r.content, r.headers.get('content-type','').lower())
        if not kind:
            return None
        dest = dest_base.with_suffix('.' + kind)
        dest.write_bytes(r.content)
        return dest
    except requests.RequestException:
        return None


# 1) Gather source-backed candidates.
candidates = []
for source, url, forced in SOURCES:
    try:
        rows = fetch_csv(url)
        print(f'{source}: {len(rows)} rows')
    except Exception as e:
        print(f'WARNING: {source} unavailable: {e}')
        continue
    for row in rows:
        name = get(row, 'title','product_name','name','product_title')
        img = image_url(row)
        if not name or not img:
            continue
        cat = category(row, forced)
        if cat in CATEGORIES:
            candidates.append((source, row, name, img, cat))

buckets = {c: [] for c in CATEGORIES}
seen = set()
for source, row, name, img, cat in candidates:
    key = (name + '|' + get(row,'brand','manufacturer','seller_name')).lower()
    if key in seen:
        continue
    seen.add(key)
    buckets[cat].append((source, row, name, img))

# Rebalance only when a category is short. This is still source-backed: we do not
# invent products or images. A candidate may move from a surplus category to a
# short category when the short category's keyword score is positive and the
# donor category stays at or above 125. This fixes edge cases where a product
# title is ambiguous (for example, a cable/adapter may also score as an
# accessory) while preserving each category's configured quota.
def score_for(cat, row):
    text = ' '.join(str(v) for v in row.values()).lower()
    return len(re.findall(RULES[cat], text, re.I))

for target_cat in CATEGORIES:
    while len(buckets[target_cat]) < TARGETS[target_cat]:
        best = None
        for donor_cat in CATEGORIES:
            if donor_cat == target_cat or len(buckets[donor_cat]) <= TARGETS[donor_cat]:
                continue
            for idx, item in enumerate(buckets[donor_cat]):
                source, row, name, img = item
                score = score_for(target_cat, row)
                if score <= 0:
                    continue
                candidate = (score, -len(str(name)), donor_cat, idx, item)
                if best is None or candidate[0:2] > best[0:2]:
                    best = candidate
        if best is None:
            break
        _, _, donor_cat, idx, item = best
        buckets[donor_cat].pop(idx)
        buckets[target_cat].append(item)

counts = {c: len(buckets[c]) for c in CATEGORIES}
print('Candidate records with image URLs after quota rebalance:', counts)
missing = [f'{c}({counts[c]})' for c in CATEGORIES if counts[c] < TARGETS[c]]
if missing:
    raise SystemExit('STOP: not enough source-backed products with image URLs: ' + ', '.join(missing))

# 2) Remove only the generated/old real-products cache. Never use the old p1.jpg...
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
for f in IMAGE_DIR.iterdir():
    if f.is_file():
        f.unlink()

# 3) Download/validate until every category has exactly 125 real images.
products = []
pid = 1
for cat in CATEGORIES:
    success = 0
    for source, row, name, img in buckets[cat]:
        if success >= TARGETS[cat]:
            break
        base = IMAGE_DIR / f'p{pid}'
        local = download_image(img, base)
        if not local:
            continue
        price = num(get(row,'final_price','price','current_price','sale_price','initial_price'), 1)
        currency = get(row,'currency').upper()
        if currency not in ('INR','₹'):
            price *= 85
        rating = max(1, min(5, num(get(row,'rating','rating_stars','average_rating'), 4)))
        reviews = int(num(get(row,'reviews_count','review_count','ratings_count','reviews'), 0))
        brand = get(row,'brand','manufacturer','seller_name') or source
        description = get(row,'description','product_description','short_description') or f'{name} from {source}.'
        utility = round(min(100, 35 + rating*10 + (reviews+10)**0.5*2))
        rel = '/static/real_products/' + local.name
        products.append({
            'id': pid, 'name': name[:180], 'category': cat, 'brand': brand[:100],
            'price': max(1, round(price)), 'mrp': max(1, round(price)),
            'rating': round(rating,2), 'reviewCount': reviews, 'utility': utility,
            'imageUrl': rel, 'image': rel,
            'description': description[:1500], 'features': [], 'availability': True,
            'source': source, 'sourceUrl': get(row,'url','product_url','page_url'),
            'realProductImage': True, 'imageSource': f'Real catalog image from {source} public dataset',
            'originalImageUrl': img
        })
        pid += 1
        success += 1
        if success % 25 == 0:
            print(f'{cat}: {success}/{TARGETS[cat]} real images downloaded')
    if success != TARGETS[cat]:
        raise SystemExit(f'STOP: only {success}/{TARGETS[cat]} real images downloaded for {cat}. No fake image substitution was made.')

assert len(products) == 996
assert all(sum(1 for p in products if p['category'] == c) == TARGETS[c] for c in CATEGORIES)
assert all(p.get('realProductImage') for p in products)
assert all((ROOT / 'app' / p['image'].lstrip('/')).exists() for p in products)
OUT.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'SUCCESS: {len(products)} real-photo products written to {OUT}')
print('Category quotas:', {c: TARGETS[c] for c in CATEGORIES})
print('All 8 categories have the approved quotas and every record has a locally cached real catalog image.')
