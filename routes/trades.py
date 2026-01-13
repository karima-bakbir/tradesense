from flask import Blueprint, request, jsonify
from models import UserChallenge, Trade, db
from challenge_logic import check_and_update_after_trade

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
        
        # Get quantity from request, default to 50 for demo purposes
        quantity = data.get('quantity', 50)  # Default to 50 for demo, but allow frontend to override
        
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
        
        # Calculate profit/loss and update challenge balance based on existing open positions
        # For demo purposes, we'll implement a simple system where each trade affects the balance
        # based on a fixed position size and price difference from the previous trade of opposite type
        
        # Get all previous trades for this challenge sorted by timestamp
        previous_trades = Trade.query.filter_by(challenge_id=challenge_id).order_by(Trade.timestamp.desc()).all()
        
        # For demo purposes, we'll implement a simple P&L calculation
        # If this is a sell order, find the most recent buy for the same asset and calculate profit/loss
        if trade_type == 'sell':
            # Find most recent buy for this asset
            for prev_trade in previous_trades:
                if prev_trade.type == 'buy' and prev_trade.asset_name == asset_name:
                    # Calculate profit/loss: (sell_price - buy_price) * quantity
                    # Use the quantity passed from the frontend or the default set above
                    # quantity is already defined above
                    pnl = (float(entry_price) - prev_trade.entry_price) * quantity
                    challenge.current_balance += pnl  # Add profit/loss to balance
                    print(f"DEBUG: Sell trade P&L calculation: ({float(entry_price)} - {prev_trade.entry_price}) * {quantity} = {pnl}")
                    print(f"DEBUG: Updated balance: {challenge.current_balance}")
                    break
        elif trade_type == 'buy':
            # If this is a buy order, find the most recent sell for the same asset and calculate profit/loss
            for prev_trade in previous_trades:
                if prev_trade.type == 'sell' and prev_trade.asset_name == asset_name:
                    # Calculate profit/loss: (buy_price - sell_price) * quantity (negative for loss when buying high after selling low)
                    pnl = (prev_trade.entry_price - float(entry_price)) * quantity
                    challenge.current_balance += pnl  # Add profit/loss to balance
                    print(f"DEBUG: Buy trade P&L calculation: ({prev_trade.entry_price} - {float(entry_price)}) * {quantity} = {pnl}")
                    print(f"DEBUG: Updated balance: {challenge.current_balance}")
                    break
        
        db.session.commit()
        
        # Check and update challenge status after the trade
        check_and_update_after_trade(trade)
        
        return jsonify({
            'message': 'Trade created successfully',
            'trade_id': trade.id,
            'challenge_id': trade.challenge_id,
            'asset_name': trade.asset_name,
            'entry_price': trade.entry_price,
            'type': trade.type,
            'timestamp': trade.timestamp.isoformat(),
            'current_balance': challenge.current_balance,
            'challenge_status': challenge.status
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
        
        # After deleting a trade, we should recalculate the challenge status
        # For simplicity, we'll just update the status based on the remaining trades/balance
        from challenge_logic import update_challenge_status
        update_challenge_status(challenge_id)
        
        return jsonify({
            'message': 'Trade deleted successfully',
            'trade_id': trade_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500