from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db

# Extensions are imported from models module
# db is defined in models.py

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions with app
    db.init_app(app)
    CORS(app)  # Enable CORS for all routes
    
    # Import and register blueprints
    try:
        from routes.users import users_bp
        from routes.challenges import challenges_bp
        from routes.trades import trades_bp
        from routes.real_time_data import real_time_data_bp
        from routes.leaderboard import leaderboard_bp
        from routes.admin import admin_bp
        
        app.register_blueprint(users_bp)
        app.register_blueprint(challenges_bp)
        app.register_blueprint(trades_bp)
        app.register_blueprint(real_time_data_bp)
        app.register_blueprint(leaderboard_bp)
        app.register_blueprint(admin_bp)
    except ImportError as e:
        print(f"Error importing blueprints: {e}")
    
    # Test route
    @app.route('/')
    def home():
        return jsonify({
            "message": "TradeSense API v1.0",
            "status": "running"
        })
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)