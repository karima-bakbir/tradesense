"""
Challenge Engine Service
=======================

This module contains the core business logic for managing trading challenges.
It handles the evaluation of challenge performance against defined thresholds.

Key Functions:
- update_challenge_status: Evaluates and updates challenge status based on performance
- calculate_daily_change: Calculates daily performance metrics
- calculate_total_change: Calculates overall challenge performance

Business Rules:
- Daily loss > 5% → Challenge status becomes 'failed'
- Total loss > 10% → Challenge status becomes 'failed' 
- Profit ≥ 20% → Challenge status becomes 'funded'
- Otherwise → Status remains 'active'
"""

from datetime import datetime, timedelta
from models import UserChallenge, Trade, db


def update_challenge_status(challenge_id):
    """
    Evaluates and updates the status of a challenge based on performance metrics.
    
    Args:
        challenge_id (int): The ID of the challenge to evaluate
        
    Returns:
        bool: True if status was updated, False otherwise
    """
    # Get the challenge from the database
    challenge = UserChallenge.query.get(challenge_id)
    if not challenge:
        print(f"DEBUG: Challenge {challenge_id} not found")
        return False
    
    # Calculate total change percentage from initial balance
    total_change_percentage = calculate_total_change(challenge)
    
    # Calculate daily change percentage (performance since start of day)
    daily_loss_percentage = calculate_daily_change(challenge)
    
    print(f"DEBUG: Challenge {challenge_id} - Current balance: {challenge.current_balance}, Initial balance: {challenge.initial_balance}")
    print(f"DEBUG: Total change percentage: {total_change_percentage}, Max total loss: {challenge.max_total_loss}")
    print(f"DEBUG: Daily loss percentage: {daily_loss_percentage}, Max daily loss: {challenge.max_daily_loss}")
    
    # Apply the rules based on challenge parameters
    if daily_loss_percentage < -challenge.max_daily_loss:  # Daily loss > max_daily_loss%
        challenge.status = 'failed'
        challenge.end_date = datetime.utcnow()
        print(f"DEBUG: Challenge {challenge_id} failed due to daily loss")
    elif total_change_percentage < -challenge.max_total_loss:  # Total loss > max_total_loss%
        challenge.status = 'failed'
        challenge.end_date = datetime.utcnow()
        print(f"DEBUG: Challenge {challenge_id} failed due to total loss")
    elif total_change_percentage >= challenge.profit_target:  # Profit reaches profit_target%
        challenge.status = 'funded'
        challenge.end_date = datetime.utcnow()
        print(f"DEBUG: Challenge {challenge_id} funded due to profit target")
    # Otherwise, status remains 'active'
    else:
        print(f"DEBUG: Challenge {challenge_id} status remains active")
    
    # Commit the changes to the database
    db.session.commit()
    
    return True


def calculate_daily_change(challenge):
    """
    Calculates the daily change percentage for a challenge.
    
    Args:
        challenge (UserChallenge): The challenge object
        
    Returns:
        float: Daily change percentage (positive for gain, negative for loss)
    """
    # Get today's trades for this challenge
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    
    # Get all trades for this challenge from the start of today
    daily_trades = Trade.query.filter(
        Trade.challenge_id == challenge.id,
        Trade.timestamp >= start_of_day
    ).order_by(Trade.timestamp.asc()).all()
    
    # If no trades today, daily change is 0
    if not daily_trades:
        return 0.0
    
    # Calculate the opening balance at the start of the day
    # We need to find the balance at the start of the day
    # For simplicity, we'll calculate based on the current balance and today's trades
    opening_balance = challenge.current_balance
    
    # Calculate the impact of today's trades to get the opening balance
    for trade in daily_trades:
        # Find the most recent opposite trade for the same asset to calculate P&L
        if trade.type == 'sell':
            # Find the most recent buy for the same asset
            prev_buy = Trade.query.filter(
                Trade.challenge_id == challenge.id,
                Trade.asset_name == trade.asset_name,
                Trade.type == 'buy',
                Trade.timestamp < trade.timestamp
            ).order_by(Trade.timestamp.desc()).first()
            
            if prev_buy:
                # Subtract the P&L of this trade from the balance to get previous balance
                pnl = (trade.entry_price - prev_buy.entry_price) * 10  # Assuming default quantity of 10
                opening_balance -= pnl
        elif trade.type == 'buy':
            # Find the most recent sell for the same asset
            prev_sell = Trade.query.filter(
                Trade.challenge_id == challenge.id,
                Trade.asset_name == trade.asset_name,
                Trade.type == 'sell',
                Trade.timestamp < trade.timestamp
            ).order_by(Trade.timestamp.desc()).first()
            
            if prev_sell:
                # Subtract the P&L of this trade from the balance to get previous balance
                pnl = (prev_sell.entry_price - trade.entry_price) * 10  # Assuming default quantity of 10
                opening_balance -= pnl
    
    # Calculate daily change percentage
    if opening_balance == 0:
        return 0.0
    
    daily_change = ((challenge.current_balance - opening_balance) / opening_balance) * 100
    return daily_change


def calculate_total_change(challenge):
    """
    Calculates the total change percentage from initial balance.
    
    Args:
        challenge (UserChallenge): The challenge object
        
    Returns:
        float: Total change percentage (positive for gain, negative for loss)
    """
    if challenge.initial_balance == 0:
        return 0.0
    
    total_change = ((challenge.current_balance - challenge.initial_balance) / challenge.initial_balance) * 100
    return total_change


def get_challenge_performance_metrics(challenge_id):
    """
    Gets detailed performance metrics for a challenge.
    
    Args:
        challenge_id (int): The ID of the challenge
        
    Returns:
        dict: Dictionary containing various performance metrics
    """
    challenge = UserChallenge.query.get(challenge_id)
    if not challenge:
        return None
    
    total_change = calculate_total_change(challenge)
    daily_change = calculate_daily_change(challenge)
    
    # Count total trades
    total_trades = Trade.query.filter_by(challenge_id=challenge.id).count()
    
    # Count winning trades (simplified calculation)
    winning_trades = 0
    trades = Trade.query.filter_by(challenge_id=challenge.id).order_by(Trade.timestamp.asc()).all()
    
    for i, trade in enumerate(trades):
        if trade.type == 'sell':
            # Find the most recent buy for the same asset
            prev_buy = None
            for j in range(i-1, -1, -1):
                if trades[j].asset_name == trade.asset_name and trades[j].type == 'buy':
                    prev_buy = trades[j]
                    break
            
            if prev_buy and trade.entry_price > prev_buy.entry_price:
                winning_trades += 1
        elif trade.type == 'buy':
            # Find the most recent sell for the same asset
            prev_sell = None
            for j in range(i-1, -1, -1):
                if trades[j].asset_name == trade.asset_name and trades[j].type == 'sell':
                    prev_sell = trades[j]
                    break
            
            if prev_sell and prev_sell.entry_price > trade.entry_price:
                winning_trades += 1
    
    return {
        'challenge_id': challenge.id,
        'user_id': challenge.user_id,
        'status': challenge.status,
        'initial_balance': challenge.initial_balance,
        'current_balance': challenge.current_balance,
        'total_change_percentage': total_change,
        'daily_change_percentage': daily_change,
        'max_daily_loss_threshold': challenge.max_daily_loss,
        'max_total_loss_threshold': challenge.max_total_loss,
        'profit_target_threshold': challenge.profit_target,
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
        'start_date': challenge.start_date,
        'end_date': challenge.end_date
    }