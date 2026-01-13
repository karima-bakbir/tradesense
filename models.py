from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    # Relationship with UserChallenge
    challenges = db.relationship('UserChallenge', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class UserChallenge(db.Model):
    __tablename__ = 'user_challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    initial_balance = db.Column(db.Float, default=5000.0, nullable=False)
    current_balance = db.Column(db.Float, default=5000.0, nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)  # active, failed, funded
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    
    # Challenge parameters
    max_daily_loss = db.Column(db.Float, default=2.0, nullable=False)  # Maximum daily loss percentage (e.g., 2%)
    max_total_loss = db.Column(db.Float, default=10.0, nullable=False)  # Maximum total loss percentage (e.g., 10%)
    profit_target = db.Column(db.Float, default=20.0, nullable=False)  # Profit target percentage to become funded (e.g., 20%)
    
    # Relationship with Trade
    trades = db.relationship('Trade', backref='challenge', lazy=True)
    
    def __repr__(self):
        return f'<UserChallenge {self.id} - {self.status}>'


class Trade(db.Model):
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('user_challenges.id'), nullable=False)
    asset_name = db.Column(db.String(100), nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # buy/sell
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Trade {self.asset_name} - {self.type}>'