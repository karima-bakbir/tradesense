from flask import Blueprint, request, jsonify
import random
from datetime import datetime
from real_time_data import get_cached_price

ai_signals_bp = Blueprint('ai_signals', __name__)

# Mock AI signals data - in a real application, this would connect to an ML model
AI_SIGNALS_DB = {}

def generate_ai_signal(symbol, current_price):
    """
    Generate AI-based trading signals for a given symbol
    """
    # Possible signal types
    signal_types = ['buy', 'sell', 'hold']
    
    # Calculate some mock indicators based on price
    volatility = random.uniform(0.5, 3.0)  # Volatility percentage
    momentum = random.uniform(-2.0, 2.0)   # Momentum indicator
    
    # Determine signal based on mock analysis
    if momentum > 1.0 and volatility < 2.0:
        signal = 'buy'
        confidence = round(random.uniform(70, 95), 2)
        recommendation = 'Strong buy opportunity based on positive momentum and manageable volatility'
    elif momentum < -1.0 and volatility > 1.5:
        signal = 'sell'
        confidence = round(random.uniform(70, 95), 2)
        recommendation = 'Potential downturn detected with high volatility'
    elif abs(momentum) < 0.5:
        signal = 'hold'
        confidence = round(random.uniform(60, 85), 2)
        recommendation = 'Market appears stable, hold position'
    else:
        signal = random.choice(signal_types)
        confidence = round(random.uniform(50, 80), 2)
        recommendation = 'Mixed signals detected, exercise caution'
    
    # Special handling for Bitcoin
    if 'BTC' in symbol.upper():
        # Bitcoin tends to be more volatile
        volatility = random.uniform(2.0, 5.0)
        if signal == 'hold' and random.random() > 0.3:
            signal = random.choice(['buy', 'sell'])
            confidence = round(confidence * 0.9, 2)  # Slightly lower confidence for crypto
    
    return {
        'symbol': symbol,
        'signal': signal,
        'confidence': confidence,
        'recommendation': recommendation,
        'indicators': {
            'volatility': round(volatility, 2),
            'momentum': round(momentum, 2),
            'rsi': round(random.uniform(30, 70), 2),  # Random RSI between 30-70
            'macd': round(random.uniform(-1, 1), 2),  # Random MACD value
        },
        'timestamp': datetime.now().isoformat(),
        'price': current_price
    }

@ai_signals_bp.route('/ai/signals/<ticker>', methods=['GET'])
def get_ai_signal(ticker):
    """
    Get AI-generated trading signal for a specific ticker
    """
    try:
        # Get current price for the ticker
        price_data = get_cached_price(ticker)
        
        if 'error' in price_data:
            return jsonify({
                'error': f'Could not fetch price data for {ticker}',
                'symbol': ticker
            }), 400
        
        # Generate AI signal based on current price
        ai_signal = generate_ai_signal(ticker, price_data['price'])
        
        return jsonify(ai_signal), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'symbol': ticker
        }), 500

@ai_signals_bp.route('/ai/signals', methods=['POST'])
def get_multiple_ai_signals():
    """
    Get AI-generated trading signals for multiple tickers
    Request body should contain: {"tickers": ["AAPL", "TSLA", "BTC-USD"]}
    """
    try:
        data = request.get_json()
        
        if not data or 'tickers' not in data:
            return jsonify({'error': 'Tickers list is required'}), 400
        
        tickers = data['tickers']
        results = {}
        
        for ticker in tickers:
            # Get current price for the ticker
            price_data = get_cached_price(ticker)
            
            if 'error' not in price_data:
                # Generate AI signal based on current price
                ai_signal = generate_ai_signal(ticker, price_data['price'])
                results[ticker] = ai_signal
            else:
                results[ticker] = {
                    'symbol': ticker,
                    'error': price_data['error'],
                    'timestamp': datetime.now().isoformat()
                }
        
        return jsonify({
            'signals': results,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_signals_bp.route('/ai/signals/popular', methods=['GET'])
def get_popular_signals():
    """
    Get AI signals for popular tickers
    """
    try:
        popular_tickers = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'BTC-USD', 'ETH-USD', 'IAM', 'ATW']
        results = {}
        
        for ticker in popular_tickers:
            # Get current price for the ticker
            price_data = get_cached_price(ticker)
            
            if 'error' not in price_data:
                # Generate AI signal based on current price
                ai_signal = generate_ai_signal(ticker, price_data['price'])
                results[ticker] = ai_signal
            else:
                results[ticker] = {
                    'symbol': ticker,
                    'error': price_data['error'],
                    'timestamp': datetime.now().isoformat()
                }
        
        return jsonify({
            'popular_signals': results,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_signals_bp.route('/ai/recommendations/<ticker>', methods=['GET'])
def get_detailed_recommendation(ticker):
    """
    Get detailed AI recommendation for a specific ticker
    """
    try:
        # Get current price for the ticker
        price_data = get_cached_price(ticker)
        
        if 'error' in price_data:
            return jsonify({
                'error': f'Could not fetch price data for {ticker}',
                'symbol': ticker
            }), 400
        
        # Generate AI signal based on current price
        ai_signal = generate_ai_signal(ticker, price_data['price'])
        
        # Enhance with more detailed recommendation
        detailed_recommendation = {
            'symbol': ai_signal['symbol'],
            'current_price': ai_signal['price'],
            'signal': ai_signal['signal'],
            'confidence': ai_signal['confidence'],
            'short_term_outlook': 'bullish' if ai_signal['signal'] == 'buy' else 'bearish' if ai_signal['signal'] == 'sell' else 'neutral',
            'target_price': round(
                ai_signal['price'] * (1 + (random.uniform(2, 8) / 100)) if ai_signal['signal'] == 'buy' 
                else ai_signal['price'] * (1 - (random.uniform(2, 6) / 100)) if ai_signal['signal'] == 'sell' 
                else ai_signal['price'], 2
            ),
            'stop_loss': round(
                ai_signal['price'] * (1 - (random.uniform(3, 7) / 100)) if ai_signal['signal'] == 'buy'
                else ai_signal['price'] * (1 + (random.uniform(3, 7) / 100)) if ai_signal['signal'] == 'sell'
                else ai_signal['price'], 2
            ),
            'timeframe': 'short-term' if random.random() > 0.5 else 'medium-term',
            'risk_level': 'medium' if ai_signal['indicators']['volatility'] < 2.5 else 'high',
            'technical_analysis': ai_signal['recommendation'],
            'fundamental_factors': [
                'Market sentiment is positive' if ai_signal['signal'] == 'buy' else 
                'Market sentiment is negative' if ai_signal['signal'] == 'sell' else 
                'Market sentiment is neutral'
            ],
            'timestamp': ai_signal['timestamp']
        }
        
        return jsonify(detailed_recommendation), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'symbol': ticker
        }), 500