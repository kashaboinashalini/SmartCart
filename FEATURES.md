# SmartCart Features

## Product catalog
- 996 real-photo products.
- 121 Electronics products and 125 in each of the other 7 categories.
- Real catalog photographs are downloaded and cached locally by `scripts/sync_real_catalog.py`.
- Generated illustration assets from the earlier version are not used.
- Each product stores source name, source listing URL and original image URL when available.
- Search, category filtering, price filtering, rating filtering and brand information.
- Product details modal with photograph, price, rating, utility, description and features.

## DAA
- 0/1 Knapsack Dynamic Programming.
- Exact optimal result for the selected product pool and budget.
- Reconstruction of selected products.
- Greedy ratio heuristic comparison.
- Brute-force correctness baseline for small pools.
- DP state/table visualization.
- Runtime and asymptotic complexity analysis.

## Shopping workflow
- Register/login.
- Browse products.
- Add products to cart.
- Set budget and optimization preferences.
- Run exact 0/1 Knapsack optimization.
- Review optimal cart.
- Enter delivery address.
- Place order directly.
- View order confirmation and order history.

## Checkout
- OTP verification is removed.
- Twilio is not required.
- No OTP endpoint is used.
- Address validation is performed before order placement.
