from app.algorithms.knapsack import zero_one_knapsack, brute_force

items=[
 {'id':1,'name':'A','price':4,'utility':7,'availability':True},
 {'id':2,'name':'B','price':3,'utility':5,'availability':True},
 {'id':3,'name':'C','price':2,'utility':4,'availability':True},
]

def main():
 r=zero_one_knapsack(items,5,build_table=True)
 b=brute_force(items,5)
 assert r['totalUtility']==b['totalUtility']==9
 assert r['totalCost']<=5
 print('Knapsack correctness test: PASS')
 print('Selected:', [x['name'] for x in r['selectedProducts']])

if __name__=='__main__': main()
