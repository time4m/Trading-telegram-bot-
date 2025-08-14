import yfinance as yf
import pandas as pd
import asyncio
import os
from datetime import datetime
import pytz
import aiohttp

# Telegram settings from environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SYMBOL = os.getenv("SYMBOL", "META")

# Fetch historical data
def fetch_data(symbol):
    data = yf.download(symbol, period="3mo", interval="1d")
    data["SMA_10"] = data["Close"].rolling(window=10).mean()
    data["SMA_50"] = data["Close"].rolling(window=50).mean()
    data["EMA_12"] = data["Close"].ewm(span=12, adjust=False).mean()
    data["EMA_26"] = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = data["EMA_12"] - data["EMA_26"]
    data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
    return data

# Generate buy/sell signal
def generate_signal(df):
    latest = df.iloc[-1]
    if latest["SMA_10"] > latest["SMA_50"] and latest["MACD"] > latest["Signal"]:
        return "BUY", latest["Close"]
    elif latest["SMA_10"] < latest["SMA_50"] and latest["MACD"] < latest["Signal"]:
        return "SELL", latest["Close"]
    else:
        return None, latest["Close"]

# Convert USD to INR
def usd_to_inr(usd):
    rate = 83.0  # static conversion rate
    return round(usd * rate, 2)

# Send message to Telegram
async def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

# Main process
async def main():
    data = fetch_data(SYMBOL)
    signal, price_usd = generate_signal(data)

    if signal:
        emoji = "📈" if signal == "BUY" else "📉"
        price_inr = usd_to_inr(price_usd)
        ist_time = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")
        vested_link = f"https://app.vested.co.in/explore/{SYMBOL}"

        message = (
            f"{emoji} {signal} {SYMBOL}\n"
            f"Price: ${price_usd:.2f} (₹{price_inr:,.2f})\n"
            f"Time: {ist_time}\n"
            f"Link: {vested_link}"
        )

        await send_telegram_message(message)
    else:
        print("No trading signal generated.")

if __name__ == "__main__":
    asyncio.run(main())
