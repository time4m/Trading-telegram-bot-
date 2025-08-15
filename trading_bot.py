import yfinance as yf
import requests
import pytz
import matplotlib.pyplot as plt
from datetime import datetime

# ===== SETTINGS =====
SYMBOL = "META"
USD_INR = 84.2
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

# ==== FETCH DATA ====
def fetch_data(symbol):
    data = yf.download(symbol.strip(), period="3mo", interval="1d")
    if data.empty:
        return None
    return data

# ==== STRATEGY ====
def generate_signal(data):
    data["SMA_5"] = data["Close"].rolling(window=5).mean()
    data["SMA_20"] = data["Close"].rolling(window=20).mean()
    sma_diff = abs(data["SMA_5"].iloc[-1] - data["SMA_20"].iloc[-1]) / data["SMA_20"].iloc[-1] * 100
    if sma_diff < 0.5:
        return None
    if data["SMA_5"].iloc[-1] > data["SMA_20"].iloc[-1]:
        return "BUY"
    elif data["SMA_5"].iloc[-1] < data["SMA_20"].iloc[-1]:
        return "SELL"
    else:
        return None

# ==== PLOT CHART ====
def save_chart(data, signal):
    plt.figure(figsize=(10,5))
    plt.plot(data.index, data["Close"], label="Price")
    plt.plot(data.index, data["SMA_5"], label="SMA 5")
    plt.plot(data.index, data["SMA_20"], label="SMA 20")
    if signal:
        plt.scatter(data.index[-1], data["Close"].iloc[-1],
                    color="green" if signal=="BUY" else "red", s=100, label=signal)
    plt.legend()
    plt.grid(True)
    plt.title(f"{SYMBOL} Price Chart with Signal")
    plt.savefig("chart.png")

# ==== SEND TO TELEGRAM ====
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def send_telegram_photo():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open("chart.png", "rb") as photo:
        files = {"photo": photo}
        data = {"chat_id": CHAT_ID}
        requests.post(url, files=files, data=data)

# ==== MAIN ====
def main():
    data = fetch_data(SYMBOL)
    if data is None:
        return

    signal = generate_signal(data)
    if not signal:
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

    save_chart(data, signal)
    send_telegram_message(message)
    send_telegram_photo()

if __name__ == "__main__":
    main()
