from flask import Blueprint, request, jsonify
from backend.models import db, UserChallenge, Trade

trades_bp = Blueprint('trades', __name__)

@trades_bp.route('/trade/create', methods=['POST'])
def create_trade():
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('challenge_id', 'asset_name', 'entry_price', 'type')):
            return jsonify({'error': 'Challenge ID, asset name, entry price, and type are required'}), 400
        
        challenge_id = data['challenge_id']
        asset_name = data['asset_name']
        entry_price = data['entry_price']
        trade_type = data['type'].lower()  # Convert to lowercase for consistency
        
        # Validate trade type
        if trade_type not in ['buy', 'sell']:
            return jsonify({'error': 'Trade type must be either "buy" or "sell"'}), 400
        
        # Check if challenge exists
        challenge = UserChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404
        
        # Check if challenge is active
        if challenge.status != 'active':
            return jsonify({'error': 'Cannot create trade for inactive challenge'}), 400
        
        # Create new trade
        trade = Trade(
            challenge_id=challenge_id,
            asset_name=asset_name,
            entry_price=float(entry_price),
            type=trade_type
        )
        
        db.session.add(trade)
        db.session.commit()
        
        return jsonify({
            'message': 'Trade created successfully',
            'trade_id': trade.id,
            'challenge_id': trade.challenge_id,
            'asset_name': trade.asset_name,
            'entry_price': trade.entry_price,
            'type': trade.type,
            'timestamp': trade.timestamp.isoformat()
        }), 201
        
    except ValueError:
        return jsonify({'error': 'Entry price must be a valid number'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@trades_bp.route('/trade/<int:trade_id>', methods=['GET'])
def get_trade(trade_id):
    try:
        trade = Trade.query.get(trade_id)
        
        if not trade:
            return jsonify({'error': 'Trade not found'}), 404
        
        return jsonify({
            'trade_id': trade.id,
            'challenge_id': trade.challenge_id,
            'asset_name': trade.asset_name,
            'entry_price': trade.entry_price,
            'type': trade.type,
            'timestamp': trade.timestamp.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trades_bp.route('/challenge/<int:challenge_id>/trades', methods=['GET'])
def get_challenge_trades(challenge_id):
    try:
        # Check if challenge exists
        challenge = UserChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404
        
        # Get all trades for this challenge
        trades = Trade.query.filter_by(challenge_id=challenge_id).order_by(Trade.timestamp.desc()).all()
        
        trades_list = []
        for trade in trades:
            trades_list.append({
                'trade_id': trade.id,
                'asset_name': trade.asset_name,
                'entry_price': trade.entry_price,
                'type': trade.type,
                'timestamp': trade.timestamp.isoformat()
            })
        
        return jsonify({
            'challenge_id': challenge_id,
            'trades_count': len(trades_list),
            'trades': trades_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trades_bp.route('/trade/<int:trade_id>', methods=['DELETE'])
def delete_trade(trade_id):
    try:
        trade = Trade.query.get(trade_id)
        
        if not trade:
            return jsonify({'error': 'Trade not found'}), 404
        
        challenge_id = trade.challenge_id
        
        db.session.delete(trade)
        db.session.commit()
        
        return jsonify({
            'message': 'Trade deleted successfully',
            'trade_id': trade_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500