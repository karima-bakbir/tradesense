from flask import Blueprint, request, jsonify
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import threading
import time
from datetime import datetime
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from services.news_service import news_service

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


def get_moroccan_price(symbol):
    """
    Get real-time price for Moroccan stocks (IAM, ATW) using web scraping
    """
    try:
        if symbol.upper() == 'IAM':
            return scrape_iam_price()
        elif symbol.upper() == 'ATW':
            return scrape_atw_price()
        else:
            return {
                'symbol': symbol.upper(),
                'price': 0,
                'timestamp': datetime.now().isoformat(),
                'source': 'moroccan',
                'error': f'Symbol {symbol} not supported'
            }
    except Exception as e:
        logger.error(f"Error fetching moroccan price for {symbol}: {str(e)}")
        return {
            'symbol': symbol.upper(),
            'price': 0,
            'timestamp': datetime.now().isoformat(),
            'source': 'moroccan',
            'error': str(e)
        }


def scrape_iam_price():
    """
    Scrape IAM (Maroc Telecom) price from a financial website
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Attempt to get price from known financial websites
    urls_to_try = [
        'https://www.investing.com/equities/maroc-telecom',
        'https://markets.businessinsider.com/stocks/iam-stock',
    ]
    
    for url in urls_to_try:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for common patterns in financial websites
                price_selectors = [
                    '[data-test="instrument-price-last"]',
                    '.price',
                    '.last-price',
                    '.stock-price',
                    '.financial-data',
                    'span[data-symbol="IAM"]',
                    '.quote',
                    '.value'
                ]
                
                for selector in price_selectors:
                    element = soup.select_one(selector)
                    if element:
                        try:
                            price_text = element.get_text(strip=True)
                            # Clean the price text
                            price_text = ''.join(c for c in price_text if c.isdigit() or c in '.-')
                            if price_text and price_text != '.':
                                price = float(price_text)
                                if price > 0:  # Valid price found
                                    return {
                                        'symbol': 'IAM',
                                        'price': price,
                                        'timestamp': datetime.now().isoformat(),
                                        'source': 'moroccan'
                                    }
                        except ValueError:
                            continue  # If conversion fails, try next selector
                
        except Exception as e:
            logger.debug(f"Failed to scrape from {url}: {str(e)}")
            continue  # Try next URL
    
    # If all attempts fail, return a reasonable default
    return {
        'symbol': 'IAM',
        'price': 78.50,  # Default mock price
        'timestamp': datetime.now().isoformat(),
        'source': 'moroccan',
        'note': 'Using default price - unable to fetch from financial sources'
    }


def scrape_atw_price():
    """
    Scrape ATW (Attijariwafa Bank) price from a financial website
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Attempt to get price from known financial websites
    urls_to_try = [
        'https://www.investing.com/equities/attijariwafa-bank',
        'https://markets.businessinsider.com/stocks/atw-stock',
    ]
    
    for url in urls_to_try:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for common patterns in financial websites
                price_selectors = [
                    '[data-test="instrument-price-last"]',
                    '.price',
                    '.last-price',
                    '.stock-price',
                    '.financial-data',
                    'span[data-symbol="ATW"]',
                    '.quote',
                    '.value'
                ]
                
                for selector in price_selectors:
                    element = soup.select_one(selector)
                    if element:
                        try:
                            price_text = element.get_text(strip=True)
                            # Clean the price text
                            price_text = ''.join(c for c in price_text if c.isdigit() or c in '.-')
                            if price_text and price_text != '.':
                                price = float(price_text)
                                if price > 0:  # Valid price found
                                    return {
                                        'symbol': 'ATW',
                                        'price': price,
                                        'timestamp': datetime.now().isoformat(),
                                        'source': 'moroccan'
                                    }
                        except ValueError:
                            continue  # If conversion fails, try next selector
                
        except Exception as e:
            logger.debug(f"Failed to scrape from {url}: {str(e)}")
            continue  # Try next URL
    
    # If all attempts fail, return a reasonable default
    return {
        'symbol': 'ATW',
        'price': 1250.00,  # Default mock price
        'timestamp': datetime.now().isoformat(),
        'source': 'moroccan',
        'note': 'Using default price - unable to fetch from financial sources'
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

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


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