import yfinance as yf
import threading
import time
from datetime import datetime
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Import the new morocco scraper service
from services.morocco_scraper import get_morocco_stock_price

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for storing the latest prices
price_cache = {}
cache_lock = threading.Lock()

def get_international_price(ticker):
    """
    Get real-time price for international assets using yfinance
    """
    try:
        # Handle cryptocurrency tickers specially
        if ticker.upper().endswith('-USD') or ticker.upper().endswith('-BTC') or ticker.upper() in ['BTC', 'ETH', 'XRP', 'LTC', 'BCH']:
            # For cryptocurrencies, use a different approach
            return get_crypto_price(ticker)
        
        ticker_obj = yf.Ticker(ticker)
        data = ticker_obj.history(period="1d", interval="1m")  # Get last minute data
        
        if not data.empty:
            latest_price = data['Close'].iloc[-1]
            return {
                'symbol': ticker.upper(),
                'price': round(latest_price, 2),
                'timestamp': datetime.now().isoformat(),
                'source': 'international'
            }
        else:
            # Fallback to fast_info if history doesn't work
            fast_info = ticker_obj.fast_info
            return {
                'symbol': ticker.upper(),
                'price': round(fast_info.get('lastPrice', fast_info.get('previousClose', 0)), 2),
                'timestamp': datetime.now().isoformat(),
                'source': 'international'
            }
    except Exception as e:
        logger.error(f"Error fetching international price for {ticker}: {str(e)}")
        return {
            'symbol': ticker.upper(),
            'price': 0,
            'timestamp': datetime.now().isoformat(),
            'source': 'international',
            'error': str(e)
        }


def get_crypto_price(ticker):
    """
    Get cryptocurrency price using yfinance or alternative methods
    """
    try:
        # Standardize cryptocurrency ticker for yfinance
        crypto_ticker = ticker.upper()
        if not crypto_ticker.endswith('-USD'):
            crypto_ticker = f"{crypto_ticker}-USD"
        
        ticker_obj = yf.Ticker(crypto_ticker)
        data = ticker_obj.history(period="1d", interval="1m")
        
        if not data.empty:
            latest_price = data['Close'].iloc[-1]
            return {
                'symbol': crypto_ticker,
                'price': round(latest_price, 2),
                'timestamp': datetime.now().isoformat(),
                'source': 'cryptocurrency'
            }
        else:
            # Fallback for crypto
            fast_info = ticker_obj.fast_info
            price = fast_info.get('lastPrice', fast_info.get('previousClose', 0))
            if price == 0:
                # Default fallback prices for major cryptocurrencies
                default_prices = {
                    'BTC-USD': 45000.00,
                    'ETH-USD': 2500.00,
                    'XRP-USD': 0.50,
                    'LTC-USD': 70.00,
                    'BCH-USD': 300.00
                }
                price = default_prices.get(crypto_ticker, 100.00)  # Default fallback
            
            return {
                'symbol': crypto_ticker,
                'price': round(price, 2),
                'timestamp': datetime.now().isoformat(),
                'source': 'cryptocurrency'
            }
    except Exception as e:
        logger.error(f"Error fetching cryptocurrency price for {ticker}: {str(e)}")
        # Return a default price for crypto if all methods fail
        crypto_symbol = ticker.upper()
        if not crypto_symbol.endswith('-USD'):
            crypto_symbol = f"{crypto_symbol}-USD"
        
        default_prices = {
            'BTC-USD': 43000.00,
            'ETH-USD': 2300.00,
            'XRP-USD': 0.45,
            'LTC-USD': 65.00,
            'BCH-USD': 280.00
        }
        default_price = default_prices.get(crypto_symbol, 80.00)
        
        return {
            'symbol': crypto_symbol,
            'price': round(default_price, 2),
            'timestamp': datetime.now().isoformat(),
            'source': 'cryptocurrency',
            'note': f'Using default price due to fetch error: {str(e)}'
        }


def get_moroccan_price(symbol):
    """
    Get real-time price for Moroccan stocks (IAM, ATW) using the new morocco scraper service
    """
    try:
        # Use the new morocco scraper service
        result = get_morocco_stock_price(symbol)
        
        # Standardize the result format to match the expected response
        standardized_result = {
            'symbol': result.get('symbol', symbol.upper()),
            'price': result.get('price'),
            'timestamp': result.get('timestamp', datetime.now().isoformat()),
            'source': 'moroccan',
        }
        
        # Add change and change_percent if available
        if result.get('change') is not None:
            standardized_result['change'] = result['change']
        if result.get('change_percent') is not None:
            standardized_result['change_percent'] = result['change_percent']
        if result.get('volume') is not None:
            standardized_result['volume'] = result['volume']
        
        # Add error if present in result
        if result.get('error'):
            standardized_result['error'] = result['error']
            logger.error(f"Error fetching moroccan price for {symbol}: {result['error']}")
        
        return standardized_result
        
    except Exception as e:
        logger.error(f"Error fetching moroccan price for {symbol}: {str(e)}")
        return {
            'symbol': symbol.upper(),
            'price': 0,
            'timestamp': datetime.now().isoformat(),
            'source': 'moroccan',
            'error': str(e)
        }


def get_cached_price(symbol):
    """
    Get price from cache if available, otherwise fetch fresh data
    """
    with cache_lock:
        if symbol in price_cache:
            # Check if cache is still fresh (less than 30 seconds old)
            cached_time = datetime.fromisoformat(price_cache[symbol]['timestamp'])
            if (datetime.now() - cached_time).seconds < 30:
                return price_cache[symbol]
    
    # Fetch fresh data
    ticker_upper = symbol.upper()
    
    # Check if it's a Moroccan stock
    if ticker_upper in ['IAM', 'ATW']:
        data = get_moroccan_price(ticker_upper)
    else:
        # Assume it's an international stock
        data = get_international_price(ticker_upper)
    
    # Update cache
    with cache_lock:
        price_cache[symbol] = data
    
    return data


# The old threading approach is no longer needed since we're using APScheduler
# The functionality is now handled by the scheduler jobs defined above


# Initialize the scheduler for periodic updates
scheduler = BackgroundScheduler()
scheduler.start()

# Schedule periodic updates for common symbols
def update_common_prices():
    common_symbols = ['AAPL', 'TSLA', 'BTC-USD', 'IAM', 'ATW']
    for symbol in common_symbols:
        try:
            price_data = get_cached_price(symbol)
            logger.info(f"Updated cache for {symbol}: {price_data['price']}")
        except Exception as e:
            logger.error(f"Error updating cache for {symbol}: {str(e)}")

# Add job to update prices every 30 seconds
scheduler.add_job(
    func=update_common_prices,
    trigger="interval",
    seconds=30,
    id='price_updates',
    name='Update common stock prices',
    replace_existing=True
)

# Import news service
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

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())