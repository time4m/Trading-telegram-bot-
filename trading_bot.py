import yfinance as yf
import pandas as pd
from datetime import datetime
import asyncio
import os
import telegram

# Telegram bot setup
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Safe, Vested-supported US stock symbols
SYMBOLS = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOGL", # Alphabet
    "AMZN",  # Amazon
    "NVDA",  # NVIDIA
    "META"   # Meta Platforms
]

# Fetch data safely
def fetch_data(symbol):
    data = yf.download(symbol, start="2022-01-01", end=datetime.today().strftime("%Y-%m-%d"), auto_adjust=True)
    if data.empty:
        print(f"No data for {symbol}, skipping.")
        return None
    return data

# Simple strategy
def simple_strategy(data):
    data["MA50"] = data["Close"].rolling(window=50).mean()
    data["MA200"] = data["Close"].rolling(window=200).mean()
    if data["MA50"].iloc[-1] > data["MA200"].iloc[-1]:
        return "BUY"
    elif data["MA50"].iloc[-1] < data["MA200"].iloc[-1]:
        return "SELL"
    else:
        return "HOLD"

# Main
async def main():
    messages = []
    for symbol in SYMBOLS:
        data = fetch_data(symbol)
        if data is not None:
            signal = simple_strategy(data)
            messages.append(f"{symbol}: {signal}")

    if messages:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="\n".join(messages))

if __name__ == "__main__":
    asyncio.run(main())
