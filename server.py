from app import create_app
import os

# App Factory for production WSGI (Gunicorn)
app = create_app()

if __name__ == '__main__':
    # Ensure data dir exists locally
    os.makedirs('data', exist_ok=True)
    
    # Support dynamic PORT from environment (required for Digital Ocean/Heroku)
    port = int(os.environ.get('PORT', 5001))
    
    print("\n" + "="*50)
    print("🚀 Jodo Sandbox Evolution V5 (Cloud-Ready)")
    print("="*50)
    print(f"➜ Local Access: http://localhost:{port}/")
    print(f"➜ Port Binding: {port}")
    print("="*50 + "\n")
    
    # Run server (Production apps use Procfile + Gunicorn)
    app.run(debug=True, host='0.0.0.0', port=port)
