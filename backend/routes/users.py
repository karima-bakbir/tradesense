from flask import Blueprint, request, jsonify
from backend.models import db, User, UserChallenge
import re
from werkzeug.security import check_password_hash

users_bp = Blueprint('users', __name__)


@users_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        username = data['username']
        email = data['email']
        password = data['password']
        
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 409
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user.id,
            'username': user.username
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@users_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('username', 'password')):
            return jsonify({'error': 'Username and password are required'}), 400
        
        username = data['username']
        password = data['password']
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'username': user.username
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user_id': user.id,
            'username': user.username,
            'email': user.email
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/admin', methods=['GET'])
def get_admin_panel():
    try:
        # Get all users with their challenge information
        users_data = db.session.query(
            User.id,
            User.username,
            User.email,
            UserChallenge.id.label('challenge_id'),
            UserChallenge.status.label('challenge_status'),
            UserChallenge.current_balance,
            UserChallenge.initial_balance,
        ).outerjoin(UserChallenge, User.id == UserChallenge.user_id).all()
        
        users_list = []
        for user_data in users_data:
            users_list.append({
                'user_id': user_data.id,
                'username': user_data.username,
                'email': user_data.email,
                'challenge_id': user_data.challenge_id,
                'challenge_status': user_data.challenge_status,
                'current_balance': user_data.current_balance,
                'initial_balance': user_data.initial_balance,
            })
        
        return jsonify({
            'users': users_list,
            'total_users': len(users_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/admin/user/<int:user_id>/update-status', methods=['PUT'])
def update_user_status(user_id):
    try:
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        new_status = data['status']
        
        # Validate status
        if new_status not in ['active', 'failed', 'funded']:
            return jsonify({'error': 'Invalid status. Must be active, failed, or funded'}), 400
        
        # Find user's challenge
        challenge = UserChallenge.query.filter_by(user_id=user_id).first()
        
        if not challenge:
            return jsonify({'error': 'User does not have a challenge'}), 404
        
        # Update the challenge status
        challenge.status = new_status
        db.session.commit()
        
        return jsonify({
            'message': 'User status updated successfully',
            'user_id': user_id,
            'new_status': new_status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500