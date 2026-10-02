from time import perf_counter


def zero_one_knapsack(items, budget, build_table=False):
    """Exact 0/1 Knapsack using 1-D DP plus predecessor state.

    State: dp[b] = maximum utility achievable with capacity b.
    Transition: dp[b] = max(dp[b], dp[b-w] + value).
    Time: O(n*B), working space O(B), reconstruction metadata O(n*B).
    """
    items = [x for x in items if x.get('availability', True) and int(x.get('price', 0)) > 0]
    B = max(0, int(budget))
    n = len(items)
    dp = [0] * (B + 1)
    # take[i][b] records whether item i was selected to reach state b.
    take = bytearray((n + 1) * (B + 1))
    snapshots = [[0] * (min(B, 100) + 1)] if build_table else None

    for i, item in enumerate(items, 1):
        w = int(item['price']); v = int(round(item['utility']))
        if w > B:
            if snapshots is not None and i <= 30:
                snapshots.append(dp[:min(B, 100)+1])
            continue
        for b in range(B, w - 1, -1):
            candidate = dp[b-w] + v
            if candidate > dp[b]:
                dp[b] = candidate
                take[i*(B+1)+b] = 1
        if snapshots is not None and i <= 30:
            snapshots.append(dp[:min(B, 100)+1])

    selected = []
    b = B
    for i in range(n, 0, -1):
        if take[i*(B+1)+b]:
            item = items[i-1]
            selected.append(item)
            b -= int(item['price'])
    selected.reverse()
    total_cost = sum(float(x['price']) for x in selected)
    total_utility = sum(int(round(x['utility'])) for x in selected)
    greedy = greedy_knapsack(items, B)
    table = snapshots if build_table else []
    return {
        'selectedProducts': selected,
        'totalCost': total_cost,
        'totalUtility': total_utility,
        'remainingBudget': B - total_cost,
        'budget': B,
        'optimizationPercentage': round((total_cost / B * 100), 2) if B else 0,
        'consideredNotSelected': [x for x in items if x not in selected],
        'dpTable': table,
        'dpTableInfo': {'rows': min(n+1, 31), 'columns': min(B,100)+1, 'shownRows': min(n+1,31), 'shownColumns': min(B,100)+1},
        'greedy': greedy,
        'complexity': {'time': 'O(n × B)', 'space': 'O(B) working + O(n × B) reconstruction metadata', 'spaceOptimized': 'O(B)'},
        'steps': [
            f'Initialize DP states for capacities 0..{B}.',
            'Process each product once, treating price as weight and utility as value.',
            'For each capacity, compare excluding the product with including it once.',
            'Traverse capacities in descending order so an item cannot be reused in the same iteration.',
            'Use predecessor decisions to reconstruct the exact selected product set.',
            'Return the maximum-utility feasible cart and compare it with a greedy heuristic.'
        ]
    }


def greedy_knapsack(items, budget):
    ordered = sorted(items, key=lambda x: (float(x.get('utility',0))/max(float(x.get('price',1)),1)), reverse=True)
    remaining = int(budget); chosen=[]
    for item in ordered:
        if int(item['price']) <= remaining:
            chosen.append(item); remaining -= int(item['price'])
    return {'selectedProducts': chosen, 'totalCost': sum(float(x['price']) for x in chosen), 'totalUtility': sum(int(round(x['utility'])) for x in chosen), 'remainingBudget': remaining}


def brute_force(items, budget, max_items=22):
    """Exact exponential baseline for DAA analysis; intentionally capped for safety."""
    items = items[:max_items]
    n=len(items); best_value=0; best_mask=0
    for mask in range(1<<n):
        cost=0; value=0
        for i in range(n):
            if mask>>i & 1:
                cost += int(items[i]['price']); value += int(round(items[i]['utility']))
                if cost > budget: break
        else:
            if value > best_value: best_value=value; best_mask=mask
    chosen=[items[i] for i in range(n) if best_mask>>i & 1]
    return {'selectedProducts':chosen,'totalCost':sum(float(x['price']) for x in chosen),'totalUtility':best_value,'remainingBudget':budget-sum(float(x['price']) for x in chosen),'complexity':'O(2^n)'}


def benchmark(items, budget):
    samples=[]
    for size in (10, 25, 50, 100, 250, 500, min(1000,len(items))):
        subset=items[:size]
        t=perf_counter(); zero_one_knapsack(subset,budget,False); elapsed=(perf_counter()-t)*1000
        samples.append({'n':size,'milliseconds':round(elapsed,3)})
    return samples
