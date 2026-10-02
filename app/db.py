import sqlite3
import os
from pathlib import Path
from flask import g

BASE = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv('DATABASE_PATH') or BASE / 'data' / 'smartcart.db')


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS carts (
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY(user_id, product_id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS preferences (
        user_id INTEGER PRIMARY KEY,
        budget INTEGER NOT NULL DEFAULT 10000,
        category TEXT NOT NULL DEFAULT 'All',
        min_rating REAL NOT NULL DEFAULT 0,
        desired_quantity INTEGER NOT NULL DEFAULT 1,
        importance REAL NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS results (
        user_id INTEGER PRIMARY KEY,
        payload TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        order_id TEXT UNIQUE NOT NULL,
        payload TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    ''')
    db.commit(); db.close()
