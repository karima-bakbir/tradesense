from models import UserChallenge, Trade, db
from datetime import datetime, timedelta
from sqlalchemy import and_

# Import the new challenge engine service
from services.challenge_engine import update_challenge_status, calculate_daily_change, calculate_total_change, get_challenge_performance_metrics


def calculate_daily_loss(challenge_id):
    """
    Calculate the daily loss for a challenge by comparing the opening balance 
    (first trade of the day) with the closing balance (last trade of the day)
    """
    # Get all trades for this challenge ordered by timestamp
    trades = Trade.query.filter_by(challenge_id=challenge_id).order_by(Trade.timestamp).all()
    
    if not trades:
        return 0.0
    
    # Group trades by date
    trades_by_date = {}
    for trade in trades:
        date = trade.timestamp.date()
        if date not in trades_by_date:
            trades_by_date[date] = []
        trades_by_date[date].append(trade)
    
    # Get today's trades to calculate daily P&L
    today = datetime.utcnow().date()
    if today in trades_by_date:
        today_trades = trades_by_date[today]
        
        # Find opening balance (balance before first trade of the day)
        # We need to look at the balance at the start of the day
        challenge = UserChallenge.query.get(challenge_id)
        
        # Calculate the opening balance for today based on previous day's close
        # For simplicity, we'll calculate based on the first trade of the day vs last trade of the day
        first_trade = today_trades[0]
        last_trade = today_trades[-1]
        
        # This is a simplified calculation - in reality you'd need to track P&L more precisely
        # For now, let's calculate based on current balance vs what the balance was at start of day
        
        # We'll calculate based on current balance vs initial balance adjusted for today's activity
        # More precise calculation would require tracking running balances
        start_of_day_balance = get_start_of_day_balance(challenge_id, today)
        current_balance = challenge.current_balance
        
        daily_change = current_balance - start_of_day_balance
        daily_change_percentage = (daily_change / start_of_day_balance) * 100
        
        return daily_change_percentage
    
    return 0.0


def get_start_of_day_balance(challenge_id, date):
    """
    Calculate the balance at the start of the given day
    """
    challenge = UserChallenge.query.get(challenge_id)
    
    # Get all trades before the given date
    trades_before_date = Trade.query.filter(
        and_(
            Trade.challenge_id == challenge_id,
            Trade.timestamp < datetime.combine(date, datetime.min.time())
        )
    ).order_by(Trade.timestamp).all()
    
    if not trades_before_date:
        # If no trades before this date, return the initial balance
        return challenge.initial_balance
    
    # In a real implementation, you'd need to track the running balance
    # For now, returning initial balance as placeholder
    return challenge.initial_balance


def update_challenge_status(challenge_id):
    """
    Check the challenge status based on the rules:
    - Daily loss > max_daily_loss -> Status = 'FAILED'
    - Total loss > max_total_loss -> Status = 'FAILED'
    - Profit reaches profit_target -> Status = 'FUNDED'
    """
    challenge = UserChallenge.query.get(challenge_id)
    if not challenge:
        return False
    
    # Calculate total percentage change
    total_change_percentage = ((challenge.current_balance - challenge.initial_balance) / challenge.initial_balance) * 100
    
    # Calculate daily loss
    daily_loss_percentage = calculate_daily_loss(challenge_id)
    
    # Apply the rules based on challenge parameters
    print(f"DEBUG: Challenge {challenge_id} - Current balance: {challenge.current_balance}, Initial balance: {challenge.initial_balance}")
    print(f"DEBUG: Total change percentage: {total_change_percentage}, Max total loss: {challenge.max_total_loss}")
    print(f"DEBUG: Daily loss percentage: {daily_loss_percentage}, Max daily loss: {challenge.max_daily_loss}")
    
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
    
    db.session.commit()
    return True


def check_and_update_after_trade(trade):
    """
    Function to be called after each trade to check and update the challenge status
    """
    challenge_id = trade.challenge_id
    update_challenge_status(challenge_id)