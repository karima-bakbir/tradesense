import requests
import os
from datetime import datetime, timedelta
from flask import jsonify
import yfinance as yf
import json

class NewsService:
    def __init__(self):
        # Using environment variable for API key or defaulting to None
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.base_url = 'https://newsapi.org/v2'

    def get_financial_news(self):
        """
        Fetch financial news from NewsAPI or use alternative sources
        """
        try:
            # Try to get news from NewsAPI if available
            if self.news_api_key:
                url = f"{self.base_url}/everything"
                params = {
                    'apiKey': self.news_api_key,
                    'q': 'finance OR stock market OR trading',
                    'sortBy': 'publishedAt',
                    'language': 'en',
                    'pageSize': 10
                }
                
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    
                    # Format articles to match our frontend expectations
                    formatted_articles = []
                    for article in articles[:5]:  # Limit to 5 articles
                        # Safely extract source name
                        source_name = 'Unknown Source'
                        if 'source' in article and article['source']:
                            source_name = article['source'].get('name', 'Unknown Source')
                        
                        formatted_article = {
                            'id': hash(article['title']) % 1000000,  # Generate a simple ID
                            'title': article['title'],
                            'description': article.get('description') or 'No description available',
                            'source': source_name,
                            'time': self._format_time_ago(article.get('publishedAt', '')),
                            'type': self._classify_article_type(article.get('title', '')),
                            'priority': self._determine_priority(article.get('title', ''))
                        }
                        formatted_articles.append(formatted_article)
                    
                    return formatted_articles
            
            
            # Alternative: Try to fetch from free financial news sources
            alt_news = self._fetch_free_financial_news()
            if alt_news:
                return alt_news
            
            # Fallback: Generate mock news with some real market data
            return self._generate_mock_news_with_market_data()
            
        except Exception as e:
            print(f"Error fetching news: {str(e)}")
            # Return mock data if API fails
            return self._generate_mock_news_with_market_data()

    def _format_time_ago(self, published_at):
        """
        Convert ISO format time to 'time ago' format
        """
        try:
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            now = datetime.now(pub_date.tzinfo)
            diff = now - pub_date
            
            if diff.days > 0:
                return f"Il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
            else:
                return "À l'instant"
        except:
            return "Récemment"

    def _classify_article_type(self, title):
        """
        Classify article type based on keywords
        """
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in ['fed', 'federal reserve', 'interest rate', 'monetary policy']):
            return 'economic'
        elif any(keyword in title_lower for keyword in ['bitcoin', 'ethereum', 'cryptocurrency', 'crypto']):
            return 'crypto'
        elif any(keyword in title_lower for keyword in ['oil', 'gold', 'commodity', 'energy']):
            return 'commodity'
        elif any(keyword in title_lower for keyword in ['ai ', 'artificial intelligence', 'tech giant', 'nasdaq']):
            return 'technology'
        else:
            return 'general'

    def _determine_priority(self, title):
        """
        Determine priority based on keywords
        """
        title_lower = title.lower()
        
        high_priority_keywords = [
            'crash', 'crisis', 'volatile', 'emergency', 'shutdown', 
            'ban', 'protest', 'war', 'conflict', 'sanction', 'scandal'
        ]
        
        medium_priority_keywords = [
            'earnings', 'report', 'growth', 'decline', 'rise', 'fall',
            'merge', 'acquire', 'partnership', 'investment'
        ]
        
        if any(keyword in title_lower for keyword in high_priority_keywords):
            return 'high'
        elif any(keyword in title_lower for keyword in medium_priority_keywords):
            return 'medium'
        else:
            return 'low'

    def _generate_mock_news_with_market_data(self):
        """
        Generate mock news with some real market data
        """
        # Get some real market data to make it more realistic
        try:
            # Get data for major indices
            sp500 = yf.Ticker("^GSPC").history(period="1d")
            djia = yf.Ticker("^DJI").history(period="1d")
            nasdaq = yf.Ticker("^IXIC").history(period="1d")
            
            sp500_change = 0
            if len(sp500) > 0 and len(sp500) > 1:
                sp500_change = ((sp500['Close'].iloc[-1] - sp500['Close'].iloc[-2]) / sp500['Close'].iloc[-2]) * 100
            
            # Create mock articles with real market context
            mock_articles = [
                {
                    'id': 1,
                    'title': f'S&P 500 records {"gain" if sp500_change >= 0 else "loss"} as market sentiment shifts',
                    'description': f'The S&P 500 closed {"higher" if sp500_change >= 0 else "lower"} by {abs(sp500_change):.2f}% amid mixed economic signals.',
                    'source': 'MarketWatch',
                    'time': 'Il y a 15 minutes',
                    'type': 'general',
                    'priority': 'medium'
                },
                {
                    'id': 2,
                    'title': 'Federal Reserve maintains cautious stance on interest rates',
                    'description': 'Central bank officials signal potential pause in rate hikes amid inflation concerns and employment data.',
                    'source': 'Reuters',
                    'time': 'Il y a 45 minutes',
                    'type': 'economic',
                    'priority': 'high'
                },
                {
                    'id': 3,
                    'title': 'Technology stocks show resilience despite market volatility',
                    'description': 'Major tech companies demonstrate strong fundamentals as investors seek stable growth prospects.',
                    'source': 'Bloomberg',
                    'time': 'Il y a 2 heures',
                    'type': 'technology',
                    'priority': 'medium'
                },
                {
                    'id': 4,
                    'title': 'Energy sector reacts to latest oil inventory report',
                    'description': 'Crude oil futures adjust following weekly inventory data and geopolitical developments.',
                    'source': 'CNBC',
                    'time': 'Il y a 3 heures',
                    'type': 'commodity',
                    'priority': 'low'
                },
                {
                    'id': 5,
                    'title': 'AI-driven trading algorithms show promising results in Q4',
                    'description': 'Automated trading systems leverage machine learning to adapt to rapidly changing market conditions.',
                    'source': 'AI Analysis',
                    'time': 'Il y a 4 heures',
                    'type': 'analysis',
                    'priority': 'medium'
                }
            ]
            return mock_articles
        except Exception as e:
            # If we can't get real data, return basic mock data
            print(f"Error getting market data: {str(e)}")
            return [
                {
                    'id': 1,
                    'title': 'Market shows resilience amid economic uncertainty',
                    'description': 'Global markets demonstrate stability despite ongoing economic challenges and geopolitical tensions.',
                    'source': 'Financial Times',
                    'time': 'Il y a 15 minutes',
                    'type': 'general',
                    'priority': 'medium'
                },
                {
                    'id': 2,
                    'title': 'Federal Reserve policy outlook influences trading patterns',
                    'description': 'Investors closely monitor central bank communications for clues about future monetary policy.',
                    'source': 'Wall Street Journal',
                    'time': 'Il y a 45 minutes',
                    'type': 'economic',
                    'priority': 'high'
                },
                {
                    'id': 3,
                    'title': 'Technology sector continues to drive innovation',
                    'description': 'Tech companies lead the way in developing new solutions for evolving market needs.',
                    'source': 'TechCrunch',
                    'time': 'Il y a 2 heures',
                    'type': 'technology',
                    'priority': 'medium'
                },
                {
                    'id': 4,
                    'title': 'Commodities market responds to supply chain updates',
                    'description': 'Raw material prices fluctuate based on global supply and demand dynamics.',
                    'source': 'MarketWatch',
                    'time': 'Il y a 3 heures',
                    'type': 'commodity',
                    'priority': 'low'
                },
                {
                    'id': 5,
                    'title': 'AI analysis predicts continued market adaptation',
                    'description': 'Artificial intelligence models suggest potential opportunities in current market conditions.',
                    'source': 'AI Analysis',
                    'time': 'Il y a 4 heures',
                    'type': 'analysis',
                    'priority': 'medium'
                }
            ]


    def _fetch_free_financial_news(self):
        """
        Fetch financial news from free sources
        """
        try:
            # Try different free financial news sources
            sources = [
                'https://www.bloomberg.com/markets/api/bulk-time-series/price/GLOBAL-METALS?timeFrame=1_DAY',
                'https://api.fiscaldata.treasury.gov/services/api/bulk-download/addresses',
                # Using a mock response for demonstration
            ]
            
            # For now, we'll use RSS feeds or alternative sources
            # We'll try to fetch from RSS feeds
            rss_sources = [
                {'url': 'https://feeds.reuters.com/reuters/marketsnews', 'source': 'Reuters'},
                {'url': 'https://www.ft.com/rss/markets', 'source': 'Financial Times'},
                {'url': 'https://feeds.bbci.co.uk/news/business/rss.xml', 'source': 'BBC Business'},
            ]
            
            # Try to fetch from actual free financial news sources
            try:
                # Import feedparser here to parse RSS feeds
                import feedparser
                
                # List of financial RSS feeds
                rss_feeds = [
                    'https://feeds.reuters.com/reuters/businessNews',  # Reuters business
                    'https://feeds.reuters.com/reuters/marketsNews',   # Reuters markets
                    'https://www.ft.com/rss/markets',                # Financial Times markets
                    'https://feeds.bbci.co.uk/news/business/rss.xml', # BBC Business
                ]
                
                for feed_url in rss_feeds:
                    try:
                        # Parse the RSS feed
                        feed = feedparser.parse(feed_url)
                        
                        if feed.entries:
                            # Extract latest news items
                            news_items = []
                            for i, entry in enumerate(feed.entries[:5]):  # Take top 5
                                # Skip entries without titles
                                if not hasattr(entry, 'title'):
                                    continue
                                
                                # Determine article type based on title/content
                                article_type = self._classify_article_type(entry.title)
                                
                                # Safely get description/summary
                                description = getattr(entry, 'summary', 'No description available')
                                if len(description) > 200:
                                    description = description[:200] + '...'
                                
                                title = entry.title[:100] + '...' if len(entry.title) > 100 else entry.title
                                
                                news_item = {
                                    'id': hash(title) % 1000000 + i,
                                    'title': title,
                                    'description': description,
                                    'source': getattr(feed.feed, 'title', feed_url.split('/')[2]),
                                    'time': 'Il y a quelques minutes',  # Approximate time
                                    'type': article_type,
                                    'priority': self._determine_priority(entry.title)
                                }
                                news_items.append(news_item)
                            
                            if news_items:
                                return news_items
                    except Exception as e:
                        print(f"Error parsing RSS feed {feed_url}: {str(e)}")
                        continue  # Try next feed
            except ImportError:
                print("feedparser not installed, using mock data")
            
            # If all RSS feeds fail, return mock data
            mock_alt_news = [
                {
                    'id': 101,
                    'title': 'Global markets show mixed signals as inflation concerns persist',
                    'description': 'Equity markets fluctuated in early trading as investors weigh central bank policies against economic data.',
                    'source': 'Financial News',
                    'time': 'Il y a 10 minutes',
                    'type': 'general',
                    'priority': 'medium'
                },
                {
                    'id': 102,
                    'title': 'Cryptocurrency markets stabilize after recent volatility',
                    'description': 'Major cryptocurrencies show signs of stabilization following regulatory clarity announcements.',
                    'source': 'Crypto Daily',
                    'time': 'Il y a 25 minutes',
                    'type': 'crypto',
                    'priority': 'medium'
                },
                {
                    'id': 103,
                    'title': 'Energy sector gains as oil prices rise amid geopolitical tensions',
                    'description': 'Energy stocks rally on increased crude oil prices driven by supply concerns.',
                    'source': 'Energy Report',
                    'time': 'Il y a 40 minutes',
                    'type': 'commodity',
                    'priority': 'high'
                },
                {
                    'id': 104,
                    'title': 'Tech giants post strong earnings, driving sector optimism',
                    'description': 'Leading technology companies exceed quarterly expectations, boosting investor sentiment.',
                    'source': 'Tech Finance',
                    'time': 'Il y a 1 heure',
                    'type': 'technology',
                    'priority': 'high'
                },
                {
                    'id': 105,
                    'title': 'AI-driven trading platforms gain traction among retail investors',
                    'description': 'Algorithmic trading solutions powered by artificial intelligence see increased adoption.',
                    'source': 'AI Finance',
                    'time': 'Il y a 2 heures',
                    'type': 'analysis',
                    'priority': 'medium'
                }
            ]
            return mock_alt_news
            
        except Exception as e:
            print(f"Error fetching free financial news: {str(e)}")
            return []


# Singleton instance
news_service = NewsService()