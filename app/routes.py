import json, secrets, time
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_db
from .data import PRODUCTS
from .algorithms.knapsack import zero_one_knapsack, brute_force, benchmark

api = Blueprint('api', __name__)

def now_iso(): return datetime.now(timezone.utc).isoformat()
def current_user(): return session.get('user')
def require_user():
    if not current_user(): return jsonify({'message':'Login required'}), 401
    return None

def product(pid):
    return next((p for p in PRODUCTS if int(p['id']) == int(pid)), None)

def clean_address(a):
    return {k: str(a.get(k,'')).strip() for k in ['fullName','phone','line1','line2','city','state','pincode','landmark']}

def valid_address(a):
    return bool(a['fullName'] and a['phone'].isdigit() and len(a['phone'])==10 and a['line1'] and a['city'] and a['state'] and a['pincode'].isdigit() and len(a['pincode'])==6)

@api.get('/health')
def health(): return jsonify({'ok':True,'service':'SmartCart Python API'})

@api.post('/auth/register')
def register():
    data=request.get_json(silent=True) or {}; name=str(data.get('name','')).strip(); email=str(data.get('email','')).strip().lower(); password=str(data.get('password',''))
    if not name or '@' not in email or len(password)<6: return jsonify({'message':'Name, valid email and password (6+ characters) are required.'}),400
    db=get_db()
    if db.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone(): return jsonify({'message':'Email already registered.'}),409
    cur=db.execute('INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)',(name,email,generate_password_hash(password),now_iso())); uid=cur.lastrowid
    db.execute('INSERT INTO preferences(user_id) VALUES(?)',(uid,)); db.commit()
    session['user']={'id':uid,'name':name,'email':email}; return jsonify({'user':session['user']})

@api.post('/auth/login')
def login():
    data=request.get_json(silent=True) or {}; email=str(data.get('email','')).strip().lower(); password=str(data.get('password',''))
    row=get_db().execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
    if not row or not check_password_hash(row['password_hash'],password): return jsonify({'message':'Invalid email or password.'}),401
    session['user']={'id':row['id'],'name':row['name'],'email':row['email']}; return jsonify({'user':session['user']})

@api.post('/auth/logout')
def logout(): session.clear(); return jsonify({'ok':True})

@api.get('/auth/me')
def me():
    err=require_user()
    if err:return err
    return jsonify({'user':current_user()})

@api.get('/products')
def products():
    err=require_user()
    if err:return err
    a=PRODUCTS[:]; q=request.args.get('q','').lower().strip(); cat=request.args.get('category','All'); brand=request.args.get('brand','All')
    if q: a=[p for p in a if q in f"{p['name']} {p['brand']} {p['description']}".lower()]
    if cat!='All': a=[p for p in a if p['category']==cat]
    if brand!='All': a=[p for p in a if p['brand']==brand]
    if request.args.get('minPrice'): a=[p for p in a if p['price']>=float(request.args['minPrice'])]
    if request.args.get('maxPrice'): a=[p for p in a if p['price']<=float(request.args['maxPrice'])]
    if request.args.get('minRating'): a=[p for p in a if p['rating']>=float(request.args['minRating'])]
    if request.args.get('minUtility'): a=[p for p in a if p['utility']>=float(request.args['minUtility'])]
    return jsonify({'products':a,'total':len(a)})

@api.get('/products/<int:pid>')
def product_details(pid):
    err=require_user()
    if err:return err
    p=product(pid)
    return jsonify(p) if p else (jsonify({'message':'Product not found'}),404)

@api.get('/categories')
def categories():
    err=require_user()
    if err:return err
    return jsonify(sorted({p['category'] for p in PRODUCTS}))

@api.get('/brands')
def brands():
    err=require_user()
    if err:return err
    return jsonify(sorted({p['brand'] for p in PRODUCTS}))

@api.get('/cart')
def get_cart():
    err=require_user()
    if err:return err
    rows=get_db().execute('SELECT product_id,quantity FROM carts WHERE user_id=?',(current_user()['id'],)).fetchall()
    return jsonify({'items':[{'productId':r['product_id'],'quantity':r['quantity']} for r in rows]})

@api.put('/cart')
def put_cart():
    err=require_user()
    if err:return err
    items=(request.get_json(silent=True) or {}).get('items',[]); db=get_db(); uid=current_user()['id']; db.execute('DELETE FROM carts WHERE user_id=?',(uid,))
    for x in items:
        p=product(x.get('productId')); q=max(1,min(99,int(x.get('quantity',1)))) if p else 0
        if p and q: db.execute('INSERT INTO carts(user_id,product_id,quantity) VALUES(?,?,?)',(uid,p['id'],q))
    db.commit(); return get_cart()

@api.get('/preferences')
def get_preferences():
    err=require_user()
    if err:return err
    r=get_db().execute('SELECT * FROM preferences WHERE user_id=?',(current_user()['id'],)).fetchone()
    return jsonify(dict(r) if r else {'budget':10000,'category':'All','min_rating':0,'desired_quantity':1,'importance':1})

@api.put('/preferences')
def put_preferences():
    err=require_user()
    if err:return err
    d=request.get_json(silent=True) or {}; budget=int(float(d.get('budget',10000)))
    if budget<0 or budget>1000000:return jsonify({'message':'Budget must be between ₹0 and ₹10,00,000.'}),400
    db=get_db(); uid=current_user()['id']; db.execute('INSERT INTO preferences(user_id,budget,category,min_rating,desired_quantity,importance) VALUES(?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET budget=excluded.budget,category=excluded.category,min_rating=excluded.min_rating,desired_quantity=excluded.desired_quantity,importance=excluded.importance',(uid,budget,d.get('category','All'),float(d.get('min_rating',0)),int(d.get('desired_quantity',1)),float(d.get('importance',1))));db.commit(); return get_preferences()

@api.post('/optimize')
def optimize():
    err=require_user()
    if err:return err
    d=request.get_json(silent=True) or {}; budget=int(float(d.get('budget',0)))
    if budget<0 or budget>100000:return jsonify({'message':'For the interactive DP demo, budget must be between ₹0 and ₹1,00,000.'}),400
    ids=d.get('productIds') or []
    pool=[product(i) for i in ids if product(i)]
    if not pool:
        rows=get_db().execute('SELECT product_id FROM carts WHERE user_id=?',(current_user()['id'],)).fetchall(); pool=[product(r['product_id']) for r in rows if product(r['product_id'])]
    if not pool:return jsonify({'message':'Select at least one product or add products to the cart.'}),400
    min_rating=float(d.get('minRating',0)); pool=[p for p in pool if p['rating']>=min_rating]
    importance=float(d.get('importance',1)); pool=[dict(p,utility=round(p['utility']*importance)) for p in pool]
    result=zero_one_knapsack(pool,budget,build_table=True)
    db=get_db(); db.execute('INSERT INTO results(user_id,payload,created_at) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload,created_at=excluded.created_at',(current_user()['id'],json.dumps(result),now_iso())); db.commit(); return jsonify(result)

@api.get('/results/latest')
def latest():
    err=require_user()
    if err:return err
    r=get_db().execute('SELECT payload FROM results WHERE user_id=?',(current_user()['id'],)).fetchone(); return jsonify(json.loads(r['payload']) if r else None)

@api.post('/demo')
def demo():
    err=require_user()
    if err:return err
    return jsonify({'budget':10000,'result':zero_one_knapsack(PRODUCTS[:40],10000,build_table=True)})

@api.get('/algorithm/benchmark')
def algo_benchmark():
    err=require_user()
    if err:return err
    return jsonify({'budget':10000,'samples':benchmark(PRODUCTS,10000),'models':{'bruteForce':'O(2^n)','greedy':'O(n log n)','dynamicProgramming':'O(n × B)','spaceOptimized':'O(B)'}})

@api.post('/algorithm/bruteforce')
def algo_bruteforce():
    err=require_user()
    if err:return err
    d=request.get_json(silent=True) or {}; ids=d.get('productIds',[])[:22]; budget=int(d.get('budget',10000)); pool=[product(i) for i in ids if product(i)]
    return jsonify(brute_force(pool,budget,max_items=22))

@api.post('/orders')
def create_order():
    err=require_user()
    if err:return err
    d=request.get_json(silent=True) or {}
    address=clean_address(d.get('address',{}))
    if not valid_address(address):
        return jsonify({'message':'Enter a valid name, 10-digit mobile number, address, city, state and 6-digit PIN code.'}),400
    db=get_db(); result_row=db.execute('SELECT payload FROM results WHERE user_id=?',(current_user()['id'],)).fetchone()
    if not result_row:return jsonify({'message':'Run Optimize My Cart first.'}),400
    result=json.loads(result_row['payload'])
    order_id=f"SC-{int(time.time()):x}-{secrets.token_hex(2).upper()}"
    order={'orderId':order_id,'address':address,'items':[{'productId':p['id'],'name':p['name'],'price':p['price'],'quantity':1,'imageUrl':p.get('imageUrl')} for p in result['selectedProducts']],'totalCost':result['totalCost'],'totalUtility':result['totalUtility'],'budget':result['budget'],'createdAt':now_iso(),'status':'Confirmed','paymentStatus':'Cash on Delivery'}
    db.execute('INSERT INTO orders(user_id,order_id,payload,created_at) VALUES(?,?,?,?)',(current_user()['id'],order_id,json.dumps(order),now_iso()));db.commit();return jsonify({'order':order})

@api.get('/orders')
def orders():
    err=require_user()
    if err:return err
    rows=get_db().execute('SELECT payload FROM orders WHERE user_id=? ORDER BY id DESC',(current_user()['id'],)); return jsonify({'orders':[json.loads(r['payload']) for r in rows]})
