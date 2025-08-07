import yfinance as yf
import pandas as pd
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from sklearn.ensemble import RandomForestClassifier
import telegram
from telegram.constants import ParseMode
from datetime import datetime
import asyncio

# === CONFIGURATION ===
TOKEN = "8493905949:AAGQ6HwbiCTfD06Qyi3BzbEU2mOknvQT1Ts"
CHAT_ID = "5570545756"
SYMBOL = "AAPL"

def fetch_data(symbol):
    data = yf.download(symbol, start="2022-01-01", end=datetime.today().strftime("%Y-%m-%d"))
    close = data['Close']
    data['SMA_10'] = SMAIndicator(close=close).sma_indicator()
    data['SMA_50'] = SMAIndicator(close=close, window=50).sma_indicator()
    data['RSI'] = RSIIndicator(close=close).rsi()
    data['MACD'] = MACD(close=close).macd()
    data.dropna(inplace=True)
    return data

def add_target(data):
    data['Target'] = 0
    data.loc[data['Close'].shift(-1) > data['Close'], 'Target'] = 1
    data.loc[data['Close'].shift(-1) < data['Close'], 'Target'] = -1
    return data

def train_model(data):
    features = ['SMA_10', 'SMA_50', 'RSI', 'MACD']
    X = data[features]
    y = data['Target']
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X[:-1], y[:-1])
    return model

async def send_signal(prediction, symbol):
    signal = "📈 BUY" if prediction == 1 else "📉 SELL" if prediction == -1 else "⏸ HOLD"
    message = f"💹 *{symbol} Trading Signal*\n\nSignal: *{signal}*\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.MARKDOWN)

async def main():
    data = fetch_data(SYMBOL)
    data = add_target(data)
    model = train_model(data)
    X_last = data[['SMA_10', 'SMA_50', 'RSI', 'MACD']].iloc[-1:]
    prediction = model.predict(X_last)[0]
    await send_signal(prediction, SYMBOL)

if __name__ == "__main__":
    asyncio.run(main())
