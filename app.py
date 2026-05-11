from flask import Flask
from flask_cors import CORS
from routes.auth import auth_bp
from routes.admin import admin_bp

# Serve the frontend files from the project root and allow CORS for local requests.
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Register blueprints for auth and admin routes
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
