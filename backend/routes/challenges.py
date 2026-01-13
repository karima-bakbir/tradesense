from flask import Blueprint, request, jsonify
from backend.models import db, User, UserChallenge

challenges_bp = Blueprint('challenges', __name__)

@challenges_bp.route('/challenge/create', methods=['POST'])
def create_challenge():
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({'error': 'User ID is required'}), 400
        
        user_id = data['user_id']
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user already has an active challenge
        existing_active_challenge = UserChallenge.query.filter_by(
            user_id=user_id,
            status='active'
        ).first()
        
        if existing_active_challenge:
            return jsonify({'error': 'User already has an active challenge'}), 409
        
        # Extract challenge parameters from request, with defaults
        initial_balance = data.get('initial_balance', 5000.0)
        max_daily_loss = data.get('max_daily_loss', 5.0)
        max_total_loss = data.get('max_total_loss', 10.0)
        profit_target = data.get('profit_target', 10.0)
        challenge_type = data.get('challenge_type', 'standard')
        
        # Create new challenge with specified parameters
        challenge = UserChallenge(
            user_id=user_id,
            initial_balance=initial_balance,
            current_balance=initial_balance,
            status='active',
            max_daily_loss=max_daily_loss,
            max_total_loss=max_total_loss,
            profit_target=profit_target,
            challenge_type=challenge_type
        )
        
        db.session.add(challenge)
        db.session.commit()
        
        return jsonify({
            'message': 'Challenge created successfully',
            'challenge_id': challenge.id,
            'initial_balance': challenge.initial_balance,
            'current_balance': challenge.current_balance,
            'status': challenge.status,
            'start_date': challenge.start_date.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@challenges_bp.route('/challenge/<int:challenge_id>', methods=['GET'])
def get_challenge(challenge_id):
    try:
        challenge = UserChallenge.query.get(challenge_id)
        
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404
        
        # Prepare response with trades
        trades_list = []
        for trade in challenge.trades:
            trades_list.append({
                'trade_id': trade.id,
                'asset_name': trade.asset_name,
                'entry_price': trade.entry_price,
                'type': trade.type,
                'timestamp': trade.timestamp.isoformat()
            })
        
        return jsonify({
            'challenge_id': challenge.id,
            'user_id': challenge.user_id,
            'initial_balance': challenge.initial_balance,
            'current_balance': challenge.current_balance,
            'status': challenge.status,
            'start_date': challenge.start_date.isoformat(),
            'end_date': challenge.end_date.isoformat() if challenge.end_date else None,
            'max_daily_loss': challenge.max_daily_loss,
            'max_total_loss': challenge.max_total_loss,
            'profit_target': challenge.profit_target,
            'challenge_type': challenge.challenge_type,
            'trades': trades_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@challenges_bp.route('/challenge/<int:challenge_id>/update-balance', methods=['PUT'])
def update_challenge_balance(challenge_id):
    try:
        data = request.get_json()
        
        if not data or 'new_balance' not in data:
            return jsonify({'error': 'New balance is required'}), 400
        
        new_balance = data['new_balance']
        
        challenge = UserChallenge.query.get(challenge_id)
        
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404
        
        # Update the balance
        challenge.current_balance = float(new_balance)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Balance updated successfully',
            'challenge_id': challenge.id,
            'current_balance': challenge.current_balance,
            'status': challenge.status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@challenges_bp.route('/user/<int:user_id>/challenges', methods=['GET'])
def get_user_challenges(user_id):
    try:
        challenges = UserChallenge.query.filter_by(user_id=user_id).all()
        
        challenges_list = []
        for challenge in challenges:
            challenges_list.append({
                'challenge_id': challenge.id,
                'initial_balance': challenge.initial_balance,
                'current_balance': challenge.current_balance,
                'status': challenge.status,
                'start_date': challenge.start_date.isoformat(),
                'end_date': challenge.end_date.isoformat() if challenge.end_date else None,
                'max_daily_loss': challenge.max_daily_loss,
                'max_total_loss': challenge.max_total_loss,
                'profit_target': challenge.profit_target,
                'challenge_type': challenge.challenge_type
            })
        
        return jsonify({
            'user_id': user_id,
            'challenges': challenges_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500