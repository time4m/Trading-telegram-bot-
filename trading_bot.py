import yfinance as yf
import requests
import asyncio
import aiohttp
import pytz
from datetime import datetime

# ===== SETTINGS =====
SYMBOL = "META"  # Fixed stock symbol
USD_INR = 84.2   # Update with current USD to INR rate
BOT_TOKEN = "8493905949:AAGQ6HwbiCTfD06Qyi3BzbEU2mOknvQT1Ts"
CHAT_ID = "5570545756"

# ==== FETCH DATA ====
def fetch_data(symbol):
    data = yf.download(symbol.strip(), period="3mo", interval="1d")
    if data.empty:
        print(f"⚠ No data found for {symbol}")
        return None
    return data

# ==== STRATEGY ====
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
        return

    signal = generate_signal(data)
    if signal is None:
        print("ℹ No clear BUY/SELL signal today.")
        return

    last_price = float(data["Close"].iloc[-1])
    last_price_inr = float(last_price * USD_INR)

    emoji = "📈" if signal == "BUY" else "📉"
    ist_time = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")
    vested_link = f"https://app.vested.co.in/explore/{SYMBOL}"

    message = (
        f"{emoji} {signal} {SYMBOL}\n"
        f"Price: ${last_price:.2f} (₹{last_price_inr:,.2f})\n"
        f"Time: {ist_time}\n"
        f"Link: {vested_link}"
    )

    await send_telegram_message(message)

if __name__ == "__main__":
    asyncio.run(main())
