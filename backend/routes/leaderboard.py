from flask import Blueprint, request, jsonify
from backend.models import db, User, UserChallenge, Trade

leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        # SQL aggregation to get top 10 traders by profit percentage
        
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