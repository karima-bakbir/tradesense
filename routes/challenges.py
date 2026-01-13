from flask import Blueprint, request, jsonify
from models import User, UserChallenge, db
from challenge_logic import update_challenge_status

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
        
        # Create new challenge with default values
        challenge = UserChallenge(
            user_id=user_id,
            initial_balance=5000.0,
            current_balance=5000.0,
            status='active',
            max_daily_loss=5.0,  # Demo: maximum 5% daily loss (more lenient for demo)
            max_total_loss=10.0,  # Default: maximum 10% total loss
            profit_target=20.0  # Default: 20% profit target to become funded
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
        
        # Check and update the challenge status based on the new balance
        update_challenge_status(challenge_id)
        
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
                'profit_target': challenge.profit_target
            })
        
        return jsonify({
            'user_id': user_id,
            'challenges': challenges_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@challenges_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        # SQL aggregation to get top 10 traders by profit percentage
        from sqlalchemy import func
        
        # Calculate profit percentage for each user challenge
        leaderboard_data = db.session.query(
            User.username,
            UserChallenge.initial_balance,
            UserChallenge.current_balance,
            UserChallenge.status,
            func.count(Trade.id).label('trade_count'),
            ((UserChallenge.current_balance - UserChallenge.initial_balance) / UserChallenge.initial_balance * 100).label('profit_percentage')
        ).join(UserChallenge, User.id == UserChallenge.user_id) \
         .outerjoin(Trade, UserChallenge.id == Trade.challenge_id) \
         .filter(UserChallenge.status.in_(['funded', 'failed'])) \
         .group_by(User.id, UserChallenge.id) \
         .order_by(((UserChallenge.current_balance - UserChallenge.initial_balance) / UserChallenge.initial_balance * 100).desc()) \
         .limit(10).all()
        
        leaderboard_list = []
        for idx, (username, initial_balance, current_balance, status, trade_count, profit_percentage) in enumerate(leaderboard_data, 1):
            total_profit = current_balance - initial_balance
            leaderboard_list.append({
                'rank': idx,
                'username': username,
                'profit_percentage': round(profit_percentage, 2),
                'total_profit': round(total_profit, 2),
                'challenge_status': status,
                'trades': trade_count or 0
            })
        
        # If we have less than 10, add some active challenges
        if len(leaderboard_list) < 10:
            remaining_spots = 10 - len(leaderboard_list)
            active_challenges = db.session.query(
                User.username,
                UserChallenge.initial_balance,
                UserChallenge.current_balance,
                UserChallenge.status,
                func.count(Trade.id).label('trade_count'),
                ((UserChallenge.current_balance - UserChallenge.initial_balance) / UserChallenge.initial_balance * 100).label('profit_percentage')
            ).join(UserChallenge, User.id == UserChallenge.user_id) \
             .outerjoin(Trade, UserChallenge.id == Trade.challenge_id) \
             .filter(UserChallenge.status == 'active') \
             .group_by(User.id, UserChallenge.id) \
             .order_by(((UserChallenge.current_balance - UserChallenge.initial_balance) / UserChallenge.initial_balance * 100).desc()) \
             .limit(remaining_spots).all()
            
            for idx, (username, initial_balance, current_balance, status, trade_count, profit_percentage) in enumerate(active_challenges, len(leaderboard_list)+1):
                total_profit = current_balance - initial_balance
                leaderboard_list.append({
                    'rank': idx,
                    'username': username,
                    'profit_percentage': round(profit_percentage, 2),
                    'total_profit': round(total_profit, 2),
                    'challenge_status': status,
                    'trades': trade_count or 0
                })
        
        return jsonify({
            'leaderboard': leaderboard_list,
            'total_ranked': len(leaderboard_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Endpoint to get all challenges for admin/debug purposes
@challenges_bp.route('/challenges', methods=['GET'])
def get_all_challenges():
    try:
        challenges = UserChallenge.query.all()
        
        challenges_list = []
        for challenge in challenges:
            trades_count = len(challenge.trades)
            challenges_list.append({
                'id': challenge.id,
                'user_id': challenge.user_id,
                'initial_balance': challenge.initial_balance,
                'current_balance': challenge.current_balance,
                'status': challenge.status,
                'start_date': challenge.start_date.isoformat(),
                'end_date': challenge.end_date.isoformat() if challenge.end_date else None,
                'max_daily_loss': challenge.max_daily_loss,
                'max_total_loss': challenge.max_total_loss,
                'profit_target': challenge.profit_target,
                'trades_count': trades_count
            })
        
        return jsonify({
            'challenges': challenges_list,
            'total_challenges': len(challenges_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@challenges_bp.route('/challenges/purchase', methods=['POST'])
def purchase_challenge():
    try:
        data = request.get_json()
        
        if not data or 'plan_id' not in data:
            return jsonify({'error': 'Plan ID is required'}), 400
        
        # Map plan_id to challenge configuration
        plan_config = {
            1: {  # Starter plan
                'initial_balance': 5000.0,
                'max_daily_loss': 5.0,  # Demo: more lenient for demo
                'max_total_loss': 10.0,
                'profit_target': 20.0
            },
            2: {  # Pro plan
                'initial_balance': 10000.0,
                'max_daily_loss': 5.0,  # Demo: more lenient for demo
                'max_total_loss': 10.0,
                'profit_target': 20.0
            },
            3: {  # Elite plan
                'initial_balance': 20000.0,
                'max_daily_loss': 5.0,  # Demo: more lenient for demo
                'max_total_loss': 10.0,
                'profit_target': 20.0
            }
        }
        
        plan_id = data['plan_id']
        if plan_id not in plan_config:
            return jsonify({'error': 'Invalid plan ID'}), 400
        
        # Get user_id from token or request data
        user_id = data.get('user_id')
        if not user_id:
            # In a real app, you'd extract user_id from JWT token
            # For demo purposes, we'll allow passing user_id in request
            return jsonify({'error': 'User ID is required'}), 400
        
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
        
        # Get plan configuration
        config = plan_config[plan_id]
        
        # Create new challenge with plan-specific values
        challenge = UserChallenge(
            user_id=user_id,
            initial_balance=config['initial_balance'],
            current_balance=config['initial_balance'],
            status='active',
            max_daily_loss=config['max_daily_loss'],
            max_total_loss=config['max_total_loss'],
            profit_target=config['profit_target']
        )
        
        db.session.add(challenge)
        db.session.commit()
        
        return jsonify({
            'message': 'Challenge purchased successfully',
            'challenge_id': challenge.id,
            'initial_balance': challenge.initial_balance,
            'current_balance': challenge.current_balance,
            'status': challenge.status,
            'start_date': challenge.start_date.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500