import json
import os
from flask import current_app

def get_data_path(filename):
    return os.path.join(current_app.config['DATA_DIR'], filename)

def load_json(filename, default=None):
    path = get_data_path(filename)
    if not os.path.exists(path):
        return default if default is not None else {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return default if default is not None else {}

def save_json(filename, data):
    path = get_data_path(filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
