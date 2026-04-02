import os
import json
import sqlite3
import uuid
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
    db_url = os.getenv('DATABASE_URL')
    
    # 1. Core Orders Table
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
    
    # 3. Webhooks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS webhooks (
            id TEXT PRIMARY KEY,
            user_email TEXT,
            url TEXT,
            events TEXT,
            created_at TEXT
        )
    ''')

    # 4. Webhook Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS webhook_logs (
            id TEXT PRIMARY KEY,
            user_email TEXT,
            event TEXT,
            url TEXT,
            status TEXT,
            attempts INTEGER,
            response_code INTEGER,
            timestamp TEXT,
            payload TEXT
        )
    ''')

    # 5. Dynamic Schema Migrations (Fix for 500 Errors)
    # Detect existing columns to prevent errors on multiple restarts
    columns = []
    if db_url:
        # PostgreSQL Migration
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
        columns = [row[0] for row in cursor.fetchall()]
        
        if 'webhooks' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN webhooks TEXT")
        if 'activated' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN activated INTEGER DEFAULT 0")
    else:
        # SQLite Migration
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
            ON CONFLICT (id) DO UPDATE SET 
                status = EXCLUDED.status, 
                updated_at = EXCLUDED.updated_at
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

# ... (get_order_db and list_orders_db remain identical)
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
    cursor.execute(f'SELECT * FROM orders WHERE user_email = {placeholder} ORDER BY created_at DESC', (user_email,))
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
                name = EXCLUDED.name, 
                password = EXCLUDED.password,
                sandbox_key = EXCLUDED.sandbox_key, 
                sandbox_secret = EXCLUDED.sandbox_secret,
                webhooks = EXCLUDED.webhooks, 
                activated = EXCLUDED.activated
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

# --- Webhook DB Utilities ---

def save_webhook_db(user_email, url, events):
    conn = get_db_connection()
    cursor = conn.cursor()
    db_url = os.getenv('DATABASE_URL')
    
    webhook_id = f"wh_{uuid.uuid4().hex[:10]}"
    
    if db_url:
        sql = "INSERT INTO webhooks (id, user_email, url, events, created_at) VALUES (%s, %s, %s, %s, %s)"
    else:
        sql = "INSERT INTO webhooks VALUES (?, ?, ?, ?, ?)"
        
    cursor.execute(sql, (webhook_id, user_email, url, json.dumps(events), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def list_webhooks_db(user_email):
    conn = get_db_connection()
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        from psycopg2.extras import RealDictCursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        placeholder = "%s"
    else:
        cursor = conn.cursor()
        placeholder = "?"
    cursor.execute(f'SELECT * FROM webhooks WHERE user_email = {placeholder}', (user_email,))
    rows = cursor.fetchall()
    conn.close()
    hooks = []
    for row in rows:
        h = dict(row)
        h['events'] = json.loads(h['events'] or '[]')
        hooks.append(h)
    return hooks

def delete_webhook_db(user_email, url):
    conn = get_db_connection()
    cursor = conn.cursor()
    db_url = os.getenv('DATABASE_URL')
    placeholder = "%s" if db_url else "?"
    cursor.execute(f'DELETE FROM webhooks WHERE user_email = {placeholder} AND url = {placeholder}', (user_email, url))
    conn.commit()
    conn.close()

def save_webhook_log_db(log_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    db_url = os.getenv('DATABASE_URL')
    
    if db_url:
        sql = '''
            INSERT INTO webhook_logs (id, user_email, event, url, status, attempts, response_code, timestamp, payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
    else:
        sql = "INSERT INTO webhook_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        
    cursor.execute(sql, (
        log_data.get('id', str(uuid.uuid4())[:8]),
        log_data['user_email'], log_data['event'], log_data['url'],
        log_data['status'], log_data['attempts'], log_data['response_code'],
        log_data.get('timestamp', datetime.now().isoformat()),
        json.dumps(log_data.get('payload', {}))
    ))
    conn.commit()
    conn.close()

def list_webhook_logs_db(user_email):
    conn = get_db_connection()
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        from psycopg2.extras import RealDictCursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        placeholder = "%s"
    else:
        cursor = conn.cursor()
        placeholder = "?"
    cursor.execute(f'SELECT * FROM webhook_logs WHERE user_email = {placeholder} ORDER BY timestamp DESC LIMIT 50', (user_email,))
    rows = cursor.fetchall()
    conn.close()
    logs = []
    for row in rows:
        l = dict(row)
        l['payload'] = json.loads(l['payload'] or '{}')
        logs.append(l)
    return logs
