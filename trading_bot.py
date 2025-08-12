import yfinance as yf
import pandas as pd
from ta.trend import SMAIndicator, MACD
from datetime import datetime
import asyncio
import telegram

# ====== CONFIG ======
SYMBOL = "AAPL"  # Change your stock symbol here
BOT_TOKEN = "8493905949:AAGQ6HwbiCTfD06Qyi3BzbEU2mOknvQT1Ts"
CHAT_ID = "5570545756"
# ====================

# Fetch historical stock data
def fetch_data(symbol):
    data = yf.download(symbol, start="2022-01-01", end=datetime.today().strftime("%Y-%m-%d"))

    # Ensure we use a 1D Series for indicators
    close = data["Close"].squeeze()

    # Add indicators
    data["SMA_10"] = SMAIndicator(close=close, window=10).sma_indicator()
    data["SMA_50"] = SMAIndicator(close=close, window=50).sma_indicator()

    macd = MACD(close=close)
    data["MACD"] = macd.macd()
    data["Signal"] = macd.macd_signal()

    return data

# Generate trading signal
def generate_signal(data):
    latest = data.iloc[-1]

    if latest["SMA_10"] > latest["SMA_50"] and latest["MACD"] > latest["Signal"]:
        return "BUY Signal 📈"
    elif latest["SMA_10"] < latest["SMA_50"] and latest["MACD"] < latest["Signal"]:
        return "SELL Signal 📉"
    else:
        return "HOLD Signal ⏸️"

# Send Telegram message
async def send_telegram_message(message):
    bot = telegram.Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=message)

# Main function
async def main():
    data = fetch_data(SYMBOL)
    signal = generate_signal(data)
    await send_telegram_message(f"{SYMBOL}: {signal}")

if __name__ == "__main__":
    asyncio.run(main())
  
