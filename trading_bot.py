import yfinance as yf
import pandas as pd
import asyncio
import os
from datetime import datetime
import pytz
import requests

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Symbols you want to track
SYMBOLS = ["META", "AAPL", "GOOG"]

# Fetch USD to INR exchange rate
def get_usd_to_inr():
    try:
        url = "https://api.exchangerate.host/latest?base=USD&symbols=INR"
        r = requests.get(url)
        data = r.json()
        return float(data["rates"]["INR"])
    except:
        return 83.0  # fallback value

# Fetch stock data
def fetch_data(symbol):
    data = yf.download(symbol, start="2022-01-01", end=datetime.today().strftime("%Y-%m-%d"), auto_adjust=True)
    if data.empty:
        return None
    data["SMA_10"] = data["Close"].rolling(window=10).mean()
    data["SMA_50"] = data["Close"].rolling(window=50).mean()
    data["EMA_12"] = data["Close"].ewm(span=12, adjust=False).mean()
    data["EMA_26"] = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = data["EMA_12"] - data["EMA_26"]
    data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
    return data

# Generate buy/sell/hold signal
def generate_signal(data):
    latest = data.iloc[-1]
    if latest["SMA_10"] > latest["SMA_50"] and latest["MACD"] > latest["Signal"]:
        return "BUY"
    elif latest["SMA_10"] < latest["SMA_50"] and latest["MACD"] < latest["Signal"]:
        return "SELL"
    else:
        return "HOLD"

# Send message to Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload)

async def main():
    usd_to_inr = get_usd_to_inr()
    ist = pytz.timezone("Asia/Kolkata")

    for symbol in SYMBOLS:
        data = fetch_data(symbol)
        if data is None:
            continue

        signal = generate_signal(data)
        price_usd = round(data["Close"].iloc[-1], 2)
        price_inr = round(price_usd * usd_to_inr, 2)

        time_now = datetime.now(ist).strftime("%Y-%m-%d %H:%M")

        vested_link = f"https://app.vested.co.in/explore/{symbol}"

        message = f"{signal} {symbol} at ${price_usd} (₹{price_inr})\nTime: {time_now} IST\nLink: {vested_link}"
        send_telegram_message(message)

if __name__ == "__main__":
    asyncio.run(main())
