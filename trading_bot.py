iimport yfinance as yf
import pandas as pd
import pytz
from datetime import datetime
import requests
import asyncio

# Telegram bot details
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

# USD to INR conversion rate (can be fetched dynamically if needed)
usd_to_inr = 84.25

# List of stock symbols (Vested supported)
symbols = ["AAPL", "GOOG", "META", "MSFT", "TSLA"]

def fetch_data(symbol):
    data = yf.download(symbol, period="3mo", interval="1d")
    data["SMA_10"] = data["Close"].rolling(window=10).mean()
    data["SMA_50"] = data["Close"].rolling(window=50).mean()
    data["EMA_12"] = data["Close"].ewm(span=12, adjust=False).mean()
    data["EMA_26"] = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = data["EMA_12"] - data["EMA_26"]
    data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
    return data

def generate_signal(data):
    latest = data.iloc[-1]
    if latest["SMA_10"] > latest["SMA_50"] and latest["MACD"] > latest["Signal"]:
        return "BUY", latest["Close"]
    elif latest["SMA_10"] < latest["SMA_50"] and latest["MACD"] < latest["Signal"]:
        return "SELL", latest["Close"]
    else:
        return None, latest["Close"]

async def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

async def main():
    for symbol in symbols:
        data = fetch_data(symbol)
        signal, price = generate_signal(data)
        
        if signal:
            # Emoji
            emoji = "📈" if signal == "BUY" else "📉"
            
            # Price conversion
            inr_price = price * usd_to_inr
            
            # Time in IST
            time_str = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")
            
            # Vested link
            vested_link = f"https://app.vested.co.in/explore/{symbol}"
            
            # Final formatted message
            message = f"""{emoji} {signal} {symbol}
Price: ${price:.2f} (₹{inr_price:,.2f})
Time: {time_str}
Link: {vested_link}"""
            
            await send_telegram_message(message)

if __name__ == "__main__":
    asyncio.run(main())
