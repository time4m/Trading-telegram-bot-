import yfinance as yf
import pandas as pd
import asyncio
import os
import requests
from datetime import datetime

# Load secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Symbols list (Vested-supported)
SYMBOLS = ["META", "AAPL", "MSFT", "GOOG"]

# USD to INR rate
USD_TO_INR = 83.0

def get_signal(symbol):
    data = yf.download(symbol, period="6mo", interval="1d")
    data["SMA_10"] = data["Close"].rolling(10).mean()
    data["SMA_50"] = data["Close"].rolling(50).mean()
    data["MACD"] = data["Close"].ewm(span=12, adjust=False).mean() - data["Close"].ewm(span=26, adjust=False).mean()
    data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()

    if len(data) < 50:
        return None

    latest_price_usd = round(data["Close"].iloc[-1], 2)
    latest_price_inr = round(latest_price_usd * USD_TO_INR, 2)

    latest_sma10 = data["SMA_10"].iloc[-1]
    latest_sma50 = data["SMA_50"].iloc[-1]
    latest_macd = data["MACD"].iloc[-1]
    latest_signal = data["Signal"].iloc[-1]

    if latest_sma10 > latest_sma50 and latest_macd > latest_signal:
        action = "BUY"
        emoji = "📈"
    elif latest_sma10 < latest_sma50 and latest_macd < latest_signal:
        action = "SELL"
        emoji = "📉"
    else:
        return None

    time_now = datetime.now().strftime("%Y-%m-%d %H:%M IST")
    vested_link = f"https://app.vested.co.in/explore/{symbol}"

    return f"{emoji} {action} {symbol} at ${latest_price_usd} (₹{latest_price_inr})\nTime: {time_now}\nLink: {vested_link}"

async def main():
    for symbol in SYMBOLS:
        signal = get_signal(symbol)
        if signal:
            send_telegram(signal)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

if __name__ == "__main__":
    asyncio.run(main())
