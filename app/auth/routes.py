from flask import Blueprint, request, jsonify, send_from_directory, current_app
from datetime import datetime
import uuid
import os
from ..utils.db import get_user_db, save_user_db, get_user_by_key_db
from ..utils.notifier import notify_new_user, notify_login

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return send_from_directory(current_app.config['ROOT_DIR'], 'login.html')

@auth_bp.route('/console-home')
def dashboard():
    return send_from_directory(os.path.join(current_app.config['ROOT_DIR'], 'dashboard'), 'index.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return send_from_directory(current_app.config['ROOT_DIR'], 'signup.html')
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', 'Developer')
    
    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
    
    if get_user_db(email):
        return jsonify({'status': 'error', 'message': 'User already exists'}), 400
    
    # Create new user with sandbox keys and webhook list
    sandbox_key = f"jodo_sb_{uuid.uuid4().hex[:12]}"
    sandbox_secret = uuid.uuid4().hex
    
    user_data = {
        'email': email,
        'password': password,
        'name': name,
        'sandbox_key': sandbox_key,
        'sandbox_secret': sandbox_secret,
        'webhooks': [],
        'activated': False,
        'created_at': datetime.now().isoformat()
    }
    save_user_db(user_data)
    
    notify_new_user(email, name)
    
    return jsonify({'status': 'success', 'message': 'Account created!', 'user': {
        'name': name,
        'email': email,
        'sandbox_key': sandbox_key,
        'sandbox_secret': sandbox_secret
    }})

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = get_user_db(email)
    
    if user and user['password'] == password:
        notify_login(email)
        return jsonify({
            'status': 'success', 
            'user': {
                'name': user['name'],
                'email': email,
                'sandbox_key': user['sandbox_key'],
                'sandbox_secret': user['sandbox_secret']
            }
        })
    
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@auth_bp.route('/api/v1/auth/keys/rotate', methods=['POST'])
def rotate_keys():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'status': 'error', 'message': 'Email required'}), 400
        
    user = get_user_db(email)
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
    # Generate new keys
    sandbox_key = f"jodo_sb_{uuid.uuid4().hex[:12]}"
    sandbox_secret = uuid.uuid4().hex
    
    user.update({
        'sandbox_key': sandbox_key,
        'sandbox_secret': sandbox_secret
    })
    save_user_db(user)
    
    return jsonify({
        'status': 'success',
        'sandbox_key': sandbox_key,
        'sandbox_secret': sandbox_secret
    })
