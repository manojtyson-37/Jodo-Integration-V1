import sqlite3
import os
import json
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../../data/sandbox.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database schema for orders and users.
    """
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Orders Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            user_email TEXT,
            amount REAL,
            currency TEXT,
            status TEXT,
            pg TEXT,
            customer_name TEXT,
            customer_email TEXT,
            customer_phone TEXT,
            callback_url TEXT,
            details TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            password TEXT,
            sandbox_key TEXT,
            sandbox_secret TEXT,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_order_db(order_id, order_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO orders (
            id, user_email, amount, currency, status, pg, 
            customer_name, customer_email, customer_phone, 
            callback_url, details, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        order_id,
        order_data.get('user_email'),
        order_data.get('amount'),
        order_data.get('currency', 'INR'),
        order_data.get('status', 'created'),
        order_data.get('pg'),
        order_data.get('customer', {}).get('name'),
        order_data.get('customer', {}).get('email'),
        order_data.get('customer', {}).get('phone'),
        order_data.get('callback_url'),
        json.dumps(order_data.get('details', [])),
        order_data.get('created_at'),
        order_data.get('updated_at')
    ))
    
    conn.commit()
    conn.close()

def get_order_db(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        order = dict(row)
        order['customer'] = {
            'name': order.pop('customer_name'),
            'email': order.pop('customer_email'),
            'phone': order.pop('customer_phone')
        }
        order['details'] = json.loads(order.pop('details'))
        return order
    return None

def list_orders_db(user_email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE user_email = ?', (user_email,))
    rows = cursor.fetchall()
    conn.close()
    
    orders = []
    for row in rows:
        order = dict(row)
        order['customer'] = {
            'name': order.pop('customer_name'),
            'email': order.pop('customer_email'),
            'phone': order.pop('customer_phone')
        }
        order['details'] = json.loads(order.pop('details'))
        orders.append(order)
    return orders
