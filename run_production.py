from waitress import serve
from app import app
import os

if __name__ == "__main__":
    # Ensure templates and static files are found
    # app.root_path is already set by Flask, but let's be explicit if needed
    
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting MedLink in Production Mode on http://localhost:{port}")
    print("Serving with Waitress...")
    
    # Disable debug mode for production use
    app.config['DEBUG'] = False
    app.config['ENV'] = 'production'
    
    serve(app, host='0.0.0.0', port=port)
