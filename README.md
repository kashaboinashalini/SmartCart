# SmartCart — Python Full-Stack DAA Project

SmartCart is a Python Flask shopping marketplace and 0/1 Knapsack optimization project.

## What is fixed in this edition

### 1. 996 products
- Electronics — 121
- Groceries — 125
- Fashion — 125
- Home Appliances — 125
- Books — 125
- Beauty — 125
- Sports — 125
- Accessories — 125

### 2. REAL PRODUCT PHOTOGRAPHS — NO GENERATED ILLUSTRATIONS

The old `p1.jpg ... p1000.jpg` illustration assets are **not used**.

Run:

```powershell
python scripts/sync_real_catalog.py
```

or double-click:

```text
SETUP_REAL_CATALOG.bat
```

The sync process reads public e-commerce dataset samples that expose actual catalog image URLs, selects source-backed products, downloads the photographs, validates the image files, and stores them under:

```text
app/static/real_products/
```

It stops if it cannot obtain 121 valid Electronics photos and 125 valid photos in each other category. It does **not** create placeholder/generated product art to reach 1,000.

The source catalog can include Amazon, Walmart, Target, Shein, Shopee, Amazon Books, Home Depot, H&M, Myntra and eBay public dataset samples. The Amazon sample, for example, documents fields including `image_url`, product URL, title, brand, rating and price. urlAmazon dataset sample documentationhttps://github.com/luminati-io/Amazon-dataset-samples/blob/main/README.md

This is preferable to blindly copying images from live Amazon/Flipkart/Swiggy/Meesho/Instamart/Purplle pages: the project uses documented public dataset sources and retains the source listing/image URL in each product record.

### 3. OTP REMOVED

There is **no OTP verification** in this edition.

Checkout is simply:

```text
Optimal Cart → Delivery Address → Place Order
```

No Twilio account, SMS service, OTP configuration or OTP endpoint is required.

## DAA implementation

SmartCart models shopping as 0/1 Knapsack:

- product price = weight/cost
- product utility = value
- budget = knapsack capacity
- each product decision `xᵢ ∈ {0,1}`

The application includes:

- exact Dynamic Programming
- solution reconstruction
- greedy ratio heuristic for comparison
- brute-force baseline for small inputs
- DP table visualization
- runtime/complexity analysis

Complexities exposed by the project:

- Greedy: `O(n log n)`
- 0/1 Knapsack DP: `O(n × B)` time
- Space-optimized DP: `O(B)` working space
- Brute force: `O(2ⁿ)`

## Install and run

Open PowerShell inside the project folder.

### Step 1 — install packages

```powershell
python -m pip install -r requirements.txt
```

### Step 2 — download/cache the real product photographs

```powershell
python scripts/sync_real_catalog.py
```

Wait until it says:

```text
SUCCESS: 996 real-photo products written to ...
All 8 categories meet the approved quotas...
```

### Step 3 — start SmartCart

```powershell
python run.py
```

Open:

```text
http://localhost:5174
```

Or use `SETUP_REAL_CATALOG.bat` to perform Steps 2 and 3 together.

## Deploy on Railway

This project uses Flask and SQLite. Railway can run the Flask app as a web service;
attach a persistent volume so account, cart, and order data survive service restarts.

1. Push this project to a GitHub repository. Keep `app/static/real_products/`
   because it contains the locally cached product photos. `.gitignore` excludes
   local environment files and SQLite databases, not the photo assets.
2. In Railway, create a project from that GitHub repository and attach a volume
   mounted at `/data`.
3. Add these service variables:

   ```text
   APP_ENV=production
   DATABASE_PATH=/data/smartcart.db
   SECRET_KEY=<a newly generated, long random value>
   ```

   Generate a value locally with
   `python -c "import secrets; print(secrets.token_urlsafe(48))"` and paste it
   into Railway's variable editor. Do not commit it or put it in this README.
4. Railway installs packages from `requirements.txt` and starts the app using
   the root `Procfile`. Generate a Railway domain and open it in a browser.
5. Check `https://<your-domain>/api/health`; it should return `{"ok":true,...}`.

The volume must be mounted at `/data` for SQLite persistence. Do not use the
ephemeral application filesystem for the database. The product-photo directory
is about 207 MiB, so include it in the GitHub deployment source; its largest
individual image is below GitHub's 100 MiB per-file limit.

## Important

The real-photo sync requires internet access because it downloads the source catalog photographs. If a source is unavailable or a category cannot meet its configured quota (121 Electronics, 125 in each other category), the script stops rather than inserting fake images.

Do not put passwords, API keys or other secrets into the source code.
