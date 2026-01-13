# TradeSense AI

TradeSense AI is an advanced trading platform that combines artificial intelligence, real-time market analysis, and comprehensive educational resources to empower traders of all levels.

## Features

- **AI-Powered Trading Signals**: Intelligent algorithms that analyze market trends and generate actionable trading signals
- **Real-Time Data**: Live market data for both international assets and Moroccan stocks
- **Multi-Language Support**: Available in French, Arabic, and English
- **Trading Challenges**: Risk-free challenges to test and improve trading skills
- **Educational Resources**: Comprehensive courses and masterclasses
- **Community Features**: Connect with other traders and share strategies
- **Interactive Charts**: Advanced charting tools with technical indicators
- **Portfolio Management**: Track and manage your investments effectively

## Tech Stack

- **Backend**: Python Flask API with SQLAlchemy ORM
- **Frontend**: React.js with Material-UI
- **Real-time Data**: yfinance for international assets, BeautifulSoup for Moroccan stock scraping
- **Database**: SQLite
- **Authentication**: JWT-based authentication system

## Setup Instructions

### Backend Setup
1. Navigate to the project directory
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```bash
   python app.py
   ```
4. The backend server runs on `http://localhost:5000`

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm start
   ```
4. The frontend runs on `http://localhost:3000`

## Data Sources

- International assets (AAPL, TSLA, BTC-USD, etc.) are fetched using yfinance
- Moroccan stocks (IAM, ATW) are scraped from financial websites using BeautifulSoup
- Real-time updates every 10-60 seconds depending on asset type

## Project Structure

```
tradesense/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── real_time_data.py      # Real-time data handler
├── services/              # Business logic services
│   ├── challenge_engine.py  # Challenge evaluation logic
│   └── morocco_scraper.py   # Moroccan stock scraper
├── routes/                # API route definitions
├── frontend/              # React frontend application
└── README.md              # Project documentation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request