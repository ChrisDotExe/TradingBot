import yfinance as yf import pandas_ta as ta from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer import robin_stocks.robinhood as r import requests from bs4 import BeautifulSoup import matplotlib.pyplot as plt import pandas as pd import time

#Initialize sentiment analyzer

analyzer = SentimentIntensityAnalyzer()

#Robinhood login

def robinhood_login(username, password, mfa_code=None): r.login(username, password, mfa_code)

#Function to fetch stock data

def get_stock_data(ticker): data = yf.download(ticker, period='30d', interval='1h') data['RSI'] = ta.rsi(data['Close'], length=14) data['EMA'] = ta.ema(data['Close'], length=20) data['SMA50'] = ta.sma(data['Close'], length=50) data['SMA200'] = ta.sma(data['Close'], length=200) data['MACD'] = ta.macd(data['Close'])['MACD_12_26_9'] data['MACD_signal'] = ta.macd(data['Close'])['MACDs_12_26_9'] return data

#Function to fetch top gainers from Yahoo Finance

def get_top_gainers(): url = 'https://finance.yahoo.com/gainers' headers = {'User-Agent': 'Mozilla/5.0'} response = requests.get(url, headers=headers) soup = BeautifulSoup(response.text, 'html.parser') tickers = [] for row in soup.find_all('tr', attrs={'class': 'simpTblRow'})[:10]: ticker = row.find('td', attrs={'aria-label': 'Symbol'}).text tickers.append(ticker) return tickers

#Yahoo Finance news scraping

def get_yahoo_finance_sentiment(ticker): url = f'https://finance.yahoo.com/quote/{ticker}/news' headers = {'User-Agent': 'Mozilla/5.0'} response = requests.get(url, headers=headers) soup = BeautifulSoup(response.text, 'html.parser') headlines = [h.text for h in soup.find_all('h3')[:5]]

sentiment_score = 0
for headline in headlines:
    score = analyzer.polarity_scores(headline)['compound']
    sentiment_score += score
return sentiment_score / len(headlines) if headlines else 0

#Reddit scraping (WallStreetBets for stocks, crypto subs for crypto)

def get_reddit_sentiment(ticker): url = f'https://www.reddit.com/search/?q={ticker}' headers = {'User-Agent': 'Mozilla/5.0'} response = requests.get(url, headers=headers) soup = BeautifulSoup(response.text, 'html.parser') posts = [p.text for p in soup.find_all('h3')[:5]]

sentiment_score = 0
for post in posts:
    score = analyzer.polarity_scores(post)['compound']
    sentiment_score += score
return sentiment_score / len(posts) if posts else 0

#StockTwits sentiment scraping

def get_stocktwits_sentiment(ticker): url = f'https://stocktwits.com/symbol/{ticker}' headers = {'User-Agent': 'Mozilla/5.0'} response = requests.get(url, headers=headers) soup = BeautifulSoup(response.text, 'html.parser') messages = [m.text for m in soup.find_all('p')[:5]]

sentiment_score = 0
for msg in messages:
    score = analyzer.polarity_scores(msg)['compound']
    sentiment_score += score
return sentiment_score / len(messages) if messages else 0

#CryptoPanic for crypto sentiment

def get_cryptopanic_sentiment(ticker): url = f'https://cryptopanic.com/news/{ticker.lower()}' headers = {'User-Agent': 'Mozilla/5.0'} response = requests.get(url, headers=headers) soup = BeautifulSoup(response.text, 'html.parser') articles = [a.text for a in soup.find_all('h2')[:5]]

sentiment_score = 0
for article in articles:
    score = analyzer.polarity_scores(article)['compound']
    sentiment_score += score
return sentiment_score / len(articles) if articles else 0

Aggregating sentiment from all sources

def get_aggregated_sentiment(ticker, is_crypto=False): yahoo_sentiment = get_yahoo_finance_sentiment(ticker) reddit_sentiment = get_reddit_sentiment(ticker) stocktwits_sentiment = get_stocktwits_sentiment(ticker) if not is_crypto else 0 cryptopanic_sentiment = get_cryptopanic_sentiment(ticker) if is_crypto else 0

sources = [yahoo_sentiment, reddit_sentiment]
if is_crypto:
    sources.append(cryptopanic_sentiment)
else:
    sources.append(stocktwits_sentiment)

return sum(sources) / len(sources)

#Trade decision logic for stocks and crypto

def trade_decision(ticker, is_crypto=False): sentiment = get_aggregated_sentiment(ticker, is_crypto) if is_crypto: crypto_info = r.crypto.get_crypto_quote(ticker) price = float(crypto_info['ask_price']) allocation = 100  # Example allocation in USD quantity = allocation / price

if sentiment > 0.3:
        r.orders.order_buy_crypto_by_price(ticker, allocation)
        print(f"Bought ${allocation} worth of {ticker} at ${price}")
else:
    data = get_stock_data(ticker)
    latest = data.iloc[-1]
    if sentiment > 0.3 and latest['RSI'] < 70 and latest['MACD'] > latest['MACD_signal']:
        profile = r.profiles.load_account_profile()
        available_cash = float(profile['portfolio_cash'])
        allocation = available_cash * 0.05
        shares_to_buy = int(allocation / latest['Close'])

        if shares_to_buy > 0:
            print(f"Buying {shares_to_buy} shares of {ticker}")
            r.orders.order_buy_market(ticker, shares_to_buy)

#Main Execution Loop

mode = 'live'  # Change to 'backtest' for testing

if mode == 'live': username = input("Enter Robinhood Username: ") password = input("Enter Robinhood Password: ") mfa_code = input("Enter MFA Code (if applicable): ") robinhood_login(username, password, mfa_code)

# Get top gainers dynamically
tickers = get_top_gainers()

for ticker in tickers:
    is_crypto = ticker.endswith("-USD")
    trade_decision(ticker, is_crypto=is_crypto)

else: print("Invalid mode. Choose 'backtest' or 'live'.")

