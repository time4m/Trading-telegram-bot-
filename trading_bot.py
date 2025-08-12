# trading_bot.py
import os
import yfinance as yf
import pandas as pd
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from datetime import datetime
import asyncio
from telegram import Bot
from telegram.constants import ParseMode

# === CONFIG - read from environment variables (safer) ===
SYMBOL = os.environ.get("SYMBOL", "AAPL")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise SystemExit("Error: TELEGRAM_TOKEN and TELEGRAM_CHAT_ID must be set as environment secrets.")

# === FUNCTIONS ===
def fetch_data(symbol: str) -> pd.DataFrame:
    # download with auto_adjust True to avoid later adjustments confusion
    data = yf.download(symbol, start="2022-01-01", end=datetime.today().strftime("%Y-%m-%d"), auto_adjust=True)
    if data.empty:
        raise ValueError(f"No data returned for {symbol}")

    # Ensure 'Close' is a 1D Series
    close = pd.Series(data["Close"].values, index=data.index)

    # Compute indicators and coerce to 1D Series (safe)
    sma10 = SMAIndicator(close=close, window=10).sma_indicator()
    sma50 = SMAIndicator(close=close, window=50).sma_indicator()
    rsi = RSIIndicator(close=close, window=14).rsi()

    macd_obj = MACD(close=close)
    macd_raw = macd_obj.macd()
    macd_signal_raw = macd_obj.macd_signal()

    # Force all indicator outputs to Series with the same index
    data["SMA_10"] = pd.Series(sma10.squeeze(), index=close.index)
    data["SMA_50"] = pd.Series(sma50.squeeze(), index=close.index)
    data["RSI"] = pd.Series(rsi.squeeze(), index=close.index)
    data["MACD"] = pd.Series(macd_raw.squeeze(), index=close.index)
    data["MACD_signal"] = pd.Series(macd_signal_raw.squeeze(), index=close.index)

    # Drop rows with NaN (indicator warm-up)
    data.dropna(inplace=True)
    return data

def generate_signal(data: pd.DataFrame) -> str:
    # use last row (single timestamp) for decision
    latest = data.iloc[-1]
    sma10 = float(latest["SMA_10"])
    sma50 = float(latest["SMA_50"])
    macd = float(latest["MACD"])
    macd_signal = float(latest["MACD_signal"])

    # simple rule-based signal
    if sma10 > sma50 and macd > macd_signal:
        return "BUY 📈"
    if sma10 < sma50 and macd < macd_signal:
        return "SELL 📉"
    return "HOLD ⏸️"

async def send_telegram(text: str):
    bot = Bot(token=TELEGRAM_TOKEN)
    # using .send_message is async in python-telegram-bot v20+
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode=ParseMode.MARKDOWN)

async def main():
    data = fetch_data(SYMBOL)
    signal = generate_signal(data)
    latest_date = data.index[-1].strftime("%Y-%m-%d")
    latest_close = float(data["Close"].iloc[-1])
    message = (
        f"💹 *{SYMBOL} Trading Signal*\n\n"
        f"Date: *{latest_date}*\n"
        f"Close: *{latest_close:.2f}*\n"
        f"Signal: *{signal}*\n"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    await send_telegram(message)

if __name__ == "__main__":
    asyncio.run(main())
