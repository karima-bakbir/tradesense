from flask import Blueprint, request, jsonify
from real_time_data import get_cached_price, get_international_price
from services.morocco_scraper import get_morocco_stock_price
# Import news service
try:
    # Try importing from backend services
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_services_path = os.path.join(current_dir, '..', '..', 'backend', 'services')
    sys.path.insert(0, backend_services_path)
    from news_service import news_service
except ImportError:
    # If backend import fails, try root services
    try:
        from services.news_service import news_service
    except ImportError:
        # Define a fallback news service if the service is not available
        class NewsService:
            def get_financial_news(self):
                # Return mock news data as fallback
                return [
                    {
                        'id': 1,
                        'title': 'Markets show resilience amid economic uncertainty',
                        'description': 'Global markets demonstrate stability despite ongoing challenges.',
                        'source': 'Financial News',
                        'time': 'Il y a 15 minutes',
                        'type': 'general',
                        'priority': 'medium'
                    },
                    {
                        'id': 2,
                        'title': 'Federal Reserve maintains cautious stance',
                        'description': 'Central bank signals potential pause in rate hikes.',
                        'source': 'Reuters',
                        'time': 'Il y a 45 minutes',
                        'type': 'economic',
                        'priority': 'high'
                    }
                ]
        
        news_service = NewsService()

# Alias the new function to maintain compatibility
get_moroccan_price = get_morocco_stock_price

real_time_data_bp = Blueprint('real_time_data', __name__)


@real_time_data_bp.route('/api/price/<ticker>', methods=['GET'])
def get_price(ticker):
    """
    Get real-time price for a given ticker symbol
    Supports both international (AAPL, TSLA, BTC-USD) and Moroccan (IAM, ATW) symbols
    """
    try:
        # Get price from cache or fetch fresh data
        price_data = get_cached_price(ticker)
        
        if 'error' in price_data:
            return jsonify({
                'error': price_data['error'],
                'symbol': ticker
            }), 500
        
        return jsonify({
            'symbol': price_data['symbol'],
            'price': price_data['price'],
            'timestamp': price_data['timestamp'],
            'source': price_data['source']
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'symbol': ticker
        }), 500


@real_time_data_bp.route('/api/prices', methods=['POST'])
def get_multiple_prices():
    """
    Get real-time prices for multiple tickers in a single request
    Request body should contain: {"tickers": ["AAPL", "TSLA", "IAM"]}
    """
    try:
        data = request.get_json()
        
        if not data or 'tickers' not in data:
            return jsonify({'error': 'Tickers list is required'}), 400
        
        tickers = data['tickers']
        results = {}
        
        for ticker in tickers:
            price_data = get_cached_price(ticker)
            results[ticker] = price_data
        
        return jsonify({
            'prices': results,
            'timestamp': get_cached_price(list(tickers)[0])['timestamp'] if tickers else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@real_time_data_bp.route('/api/news/financial', methods=['GET'])
def get_financial_news():
    """
    Get the latest financial news
    """
    try:
        news_items = news_service.get_financial_news()
        return jsonify(news_items), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@real_time_data_bp.route('/api/price/<ticker>/info', methods=['GET'])
def get_price_info(ticker):
    """
    Get detailed information about a specific ticker
    """
    try:
        # Get the price data
        if ticker.upper() in ['IAM', 'ATW']:
            price_data = get_moroccan_price(ticker)
        else:
            price_data = get_international_price(ticker)
        
        if 'error' in price_data:
            return jsonify({
                'error': price_data['error'],
                'symbol': ticker
            }), 500
        
        # Enhance with additional information based on the symbol
        info_data = {
            'symbol': price_data['symbol'],
            'price': price_data['price'],
            'timestamp': price_data['timestamp'],
            'source': price_data['source']
        }
        
        # Add specific details based on the stock
        if ticker.upper() == 'AAPL':
            info_data.update({
                'company_name': 'Apple Inc.',
                'exchange': 'NASDAQ',
                'currency': 'USD',
                'sector': 'Technology'
            })
        elif ticker.upper() == 'TSLA':
            info_data.update({
                'company_name': 'Tesla, Inc.',
                'exchange': 'NASDAQ',
                'currency': 'USD',
                'sector': 'Automotive'
            })
        elif ticker.upper() == 'BTC-USD':
            info_data.update({
                'asset_name': 'Bitcoin',
                'type': 'Cryptocurrency',
                'currency': 'USD',
                'market_cap_category': 'Crypto'
            })
        elif ticker.upper() == 'IAM':
            info_data.update({
                'company_name': 'Maroc Telecom',
                'exchange': 'Casablanca Stock Exchange',
                'currency': 'MAD',
                'sector': 'Telecommunications'
            })
        elif ticker.upper() == 'ATW':
            info_data.update({
                'company_name': 'Attijariwafa Bank',
                'exchange': 'Casablanca Stock Exchange',
                'currency': 'MAD',
                'sector': 'Banking'
            })
        else:
            # Generic information
            info_data.update({
                'exchange': 'Unknown',
                'currency': 'USD',
                'sector': 'General'
            })
        
        return jsonify(info_data), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'symbol': ticker
        }), 500