import yfinance as yf
import asyncio
import aiohttp
from datetime import datetime
import pytz
import os
import sys

SYMBOL = os.getenv("SYMBOL", "").strip()
if not SYMBOL:
    print("❌ ERROR: SYMBOL environment variable is not set.")
    sys.exit(1)  # Stop the bot so you see the error in logs
    
# ==== CONFIG ====
SYMBOL = "META"  # Change to any stock symbol
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
USD_INR = 84.25  # Update with latest rate

# ==== FETCH DATA ====
def fetch_data(symbol):
    data = yf.download(symbol.strip(), period="3mo", interval="1d")
    if data.empty:
        print(f"⚠ No data found for {symbol}")
        return None
    return data

# ==== STRATEGY (Simple Moving Average Crossover) ====
def generate_signal(data):
    data["SMA_5"] = data["Close"].rolling(window=5).mean()
    data["SMA_20"] = data["Close"].rolling(window=20).mean()
    if data["SMA_5"].iloc[-1] > data["SMA_20"].iloc[-1]:
        return "BUY"
    elif data["SMA_5"].iloc[-1] < data["SMA_20"].iloc[-1]:
        return "SELL"
    else:
        return None

# ==== SEND TO TELEGRAM ====
async def send_telegram_message(message):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        async with session.post(url, data=payload) as resp:
            print("✅ Telegram sent:", await resp.text())

# ==== MAIN ====
async def main():
    data = fetch_data(SYMBOL)
    if data is None:
        return  # Skip if no data

    signal = generate_signal(data)
    if signal is None:
        print("ℹ No clear BUY/SELL signal today.")
        return

    # Get last row values as floats
    last_price = float(data["Close"].iloc[-1])
    last_price_inr = float(last_price * USD_INR)


    # Get emoji
    emoji = "📈" if signal == "BUY" else "📉"

    # Time in IST
    ist_time = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")

    # Vested Link
    vested_link = f"https://app.vested.co.in/explore/{SYMBOL}"

    # Final message format
    message = (
        f"{emoji} {signal} {SYMBOL}\n"
        f"Price: ${last_price:.2f} (₹{last_price_inr:,.2f})\n"
        f"Time: {ist_time}\n"
        f"Link: {vested_link}"
    )

    await send_telegram_message(message)
