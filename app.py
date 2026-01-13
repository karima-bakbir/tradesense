from flask import Flask
from flask_cors import CORS
from models import db
from routes.users import users_bp
from routes.challenges import challenges_bp
from routes.trades import trades_bp
from routes.real_time_data import real_time_data_bp
from routes.ai_signals import ai_signals_bp


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tradesense.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key-here'

    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)  # Enable CORS for all origins during development
    
    # Register blueprints
    app.register_blueprint(users_bp)
    app.register_blueprint(challenges_bp)
    app.register_blueprint(trades_bp)
    app.register_blueprint(real_time_data_bp)
    app.register_blueprint(ai_signals_bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)