from flask import Flask
import os

def create_app():
    # Root of the workspace project
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    app = Flask(__name__, 
                static_url_path='/dashboard', 
                static_folder=os.path.join(ROOT_DIR, 'dashboard'), 
                template_folder=ROOT_DIR)
    
    # Configuration
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['DATA_DIR'] = os.path.join(ROOT_DIR, 'data')
    app.config['ROOT_DIR'] = ROOT_DIR # Store for blueprints
    
    # Ensure data directory exists
    if not os.path.exists(app.config['DATA_DIR']):
        os.makedirs(app.config['DATA_DIR'])
    
    with app.app_context():
        from .auth.routes import auth_bp
        from .orders.routes import orders_bp
        from .webhooks.routes import webhooks_bp
        from .simulation.routes import sim_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(orders_bp, url_prefix='/api/v1/integrations/pay/orders')
        app.register_blueprint(webhooks_bp, url_prefix='/api/v1/webhooks')
        app.register_blueprint(sim_bp, url_prefix='/pay')
        
    return app
