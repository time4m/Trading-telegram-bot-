import yfinance as yf
import yfinance as yf
import requests
import asyncio
from datetime import datetime

# ===== SETTINGS =====
SYMBOL = "META"  # Fixed stock symbol
USD_INR = 84.2   # Update with current USD to INR rate
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

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
async def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as resp:
            return await resp.text()

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
