import yfinance as yf
import pandas as pd
import numpy as np
import asyncio
import os
from datetime import datetime
import requests

# Load secrets from GitHub Actions environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Safe, liquid US stocks available on Vested
SYMBOLS = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOGL", # Alphabet (Google)
    "AMZN",  # Amazon
    "NVDA",  # NVIDIA
    "META"   # Meta Platforms (Facebook)
]

def fetch_data(symbol):
    """Fetch historical price data for a symbol."""
    data = yf.download(
        symbol,
        start="2022-01-01",
        end=datetime.today().strftime("%Y-%m-%d"),
        auto_adjust=True
    )
    return data

def generate_signal(data):
    """Simple Moving Average crossover strategy."""
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['SMA200'] = data['Close'].rolling(window=200).mean()

    if data['SMA50'].iloc[-1] > data['SMA200'].iloc[-1]:
        return "BUY"
    elif data['SMA50'].iloc[-1] < data['SMA200'].iloc[-1]:
        return "SELL"
    else:
        return "HOLD"

def send_telegram_message(message):
    """Send message to Telegram bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

async def main():
    for symbol in SYMBOLS:
        data = fetch_data(symbol)
        if data.empty:
            continue  # Skip if no data fetched

        signal = generate_signal(data)
        latest_price = round(data['Close'].iloc[-1], 2)

        if signal in ["BUY", "SELL"]:
            msg = f"{signal} {symbol} at ${latest_price}"
            send_telegram_message(msg)

if __name__ == "__main__":
    asyncio.run(main())
