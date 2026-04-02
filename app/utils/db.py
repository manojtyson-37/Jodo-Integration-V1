import os
import json
import sqlite3
from datetime import datetime

# Database Connection Helper
def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    
    if db_url:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(db_url)
        return conn
    else:
        db_path = os.path.join(os.path.dirname(__file__), '../../data/sandbox.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
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
    
    # Users Table (Expanded)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            password TEXT,
            sandbox_key TEXT,
            sandbox_secret TEXT,
            webhooks TEXT,
            activated INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')
    
    # Manual Migration check for webhooks/activated columns
    # This ensures old SQLite databases are updated without re-creation
    columns = []
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'webhooks' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN webhooks TEXT")
        if 'activated' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN activated INTEGER DEFAULT 0")
    
    conn.commit()
    conn.close()

def save_order_db(order_id, order_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    db_url = os.getenv('DATABASE_URL')
    placeholder = "%s" if db_url else "?"
    
    if db_url:
        sql = '''
            INSERT INTO orders (id, user_email, amount, currency, status, pg, 
                                customer_name, customer_email, customer_phone, 
                                callback_url, details, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, updated_at = EXCLUDED.updated_at
        '''
    else:
        sql = f'INSERT OR REPLACE INTO orders VALUES ({", ".join([placeholder]*13)})'

    cursor.execute(sql, (
        order_id, order_data.get('user_email'), order_data.get('amount'), order_data.get('currency', 'INR'),
        order_data.get('status', 'created'), order_data.get('pg'),
        order_data.get('customer', {}).get('name'), order_data.get('customer', {}).get('email'),
        order_data.get('customer', {}).get('phone'), order_data.get('callback_url'),
        json.dumps(order_data.get('details', [])), order_data.get('created_at'), order_data.get('updated_at')
    ))
    conn.commit()
    conn.close()

def get_order_db(order_id):
    conn = get_db_connection()
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        from psycopg2.extras import RealDictCursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        placeholder = "%s"
    else:
        cursor = conn.cursor()
        placeholder = "?"
    cursor.execute(f'SELECT * FROM orders WHERE id = {placeholder}', (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        order = dict(row)
        order['customer'] = {'name': order.pop('customer_name'), 'email': order.pop('customer_email'), 'phone': order.pop('customer_phone')}
        order['details'] = json.loads(order.pop('details'))
        return order
    return None

def list_orders_db(user_email):
    conn = get_db_connection()
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        from psycopg2.extras import RealDictCursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        placeholder = "%s"
    else:
        cursor = conn.cursor()
        placeholder = "?"
    cursor.execute(f'SELECT * FROM orders WHERE user_email = {placeholder}', (user_email,))
    rows = cursor.fetchall()
    conn.close()
    orders = []
    for row in rows:
        order = dict(row)
        order['customer'] = {'name': order.pop('customer_name'), 'email': order.pop('customer_email'), 'phone': order.pop('customer_phone')}
        order['details'] = json.loads(order.pop('details'))
        orders.append(order)
    return orders

def save_user_db(user_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    db_url = os.getenv('DATABASE_URL')
    
    if db_url:
        sql = '''
            INSERT INTO users (email, name, password, sandbox_key, sandbox_secret, webhooks, activated, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET 
                name = EXCLUDED.name, password = EXCLUDED.password,
                sandbox_key = EXCLUDED.sandbox_key, sandbox_secret = EXCLUDED.sandbox_secret,
                webhooks = EXCLUDED.webhooks, activated = EXCLUDED.activated
        '''
    else:
        sql = 'INSERT OR REPLACE INTO users (email, name, password, sandbox_key, sandbox_secret, webhooks, activated, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
        
    cursor.execute(sql, (
        user_data['email'], user_data['name'], user_data['password'],
        user_data['sandbox_key'], user_data['sandbox_secret'],
        json.dumps(user_data.get('webhooks', [])),
        1 if user_data.get('activated', False) else 0,
        user_data.get('created_at', datetime.now().isoformat())
    ))
    conn.commit()
    conn.close()

def get_user_db(email):
    conn = get_db_connection()
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        from psycopg2.extras import RealDictCursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        placeholder = "%s"
    else:
        cursor = conn.cursor()
        placeholder = "?"
    cursor.execute(f'SELECT * FROM users WHERE email = {placeholder}', (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        user = dict(row)
        user['webhooks'] = json.loads(user.pop('webhooks') or '[]')
        user['activated'] = bool(user['activated'])
        return user
    return None

def get_user_by_key_db(sandbox_key):
    conn = get_db_connection()
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        from psycopg2.extras import RealDictCursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        placeholder = "%s"
    else:
        cursor = conn.cursor()
        placeholder = "?"
    cursor.execute(f'SELECT * FROM users WHERE sandbox_key = {placeholder}', (sandbox_key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        user = dict(row)
        user['webhooks'] = json.loads(user.pop('webhooks') or '[]')
        user['activated'] = bool(user['activated'])
        return user
    return None
