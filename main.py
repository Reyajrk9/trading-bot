import telebot
import threading
import time
import os
import random
import yfinance as yf
import pandas as pd
import ta
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from flask import Flask

# ================== CONFIG ==================
TOKEN = os.environ.get("BOT_TOKEN")
VIP_INDIAN = os.environ.get("CHANNEL_ID_INDIAN")
VIP_FOREX = os.environ.get("CHANNEL_ID_GLOBAL")

QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"

bot = telebot.TeleBot(TOKEN)

# ================== FLASK SERVER (Railway Keep Alive) ==================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ RK BOT RUNNING"

def run_web():
    app.run(host="0.0.0.0", port=8080)

# ================== AI ENGINE ==================
def train_and_predict(df):
    try:
        close = df['Close'].squeeze()

        df['RSI'] = ta.momentum.RSIIndicator(close).rsi()
        df['Price_Change'] = close.pct_change()
        df['Target'] = np.where(close.shift(-1) > close, 1, 0)

        df = df.dropna()

        if len(df) < 50:
            return None, 0

        X = df[['RSI', 'Price_Change']]
        y = df['Target']

        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X[:-1], y[:-1])

        last_row = X.tail(1)

        prediction = model.predict(last_row)[0]
        probability = model.predict_proba(last_row).max() * 100

        return prediction, probability

    except Exception as e:
        print(f"AI Error: {e}")
        return None, 0

# ================== SIGNAL ==================
def get_ai_signal(asset_list):
    try:
        asset = random.choice(asset_list)
        df = yf.download(asset, period="1d", interval="1m", progress=False)

        if df is None or df.empty or len(df) < 60:
            return None, None, 0

        close = df['Close'].squeeze()

        pred, prob = train_and_predict(df)
        rsi_val = ta.momentum.RSIIndicator(close).rsi().iloc[-1]

        signal = None

        if pred == 1 and rsi_val < 48:
            signal = "CALL 🟢 (AI BUY)"
        elif pred == 0 and rsi_val > 52:
            signal = "PUT 🔴 (AI SELL)"

        return asset, signal, round(prob, 2)

    except Exception as e:
        print(f"Signal Error: {e}")
        return None, None, 0

# ================== SIGNAL LOOP ==================
def signal_loop():
    while True:
        try:
            tasks = [
                (["^NSEI", "^BSESN"], VIP_INDIAN),
                (["EURUSD=X", "GBPUSD=X", "BTC-USD"], VIP_FOREX)
            ]

            for assets, ch_id in tasks:
                a, s, p = get_ai_signal(assets)

                if s and p > 85:
                    msg = (
                        f"🤖 *RK AI-ML PREDICTION* 🤖\n\n"
                        f"🌍 Asset: {a}\n"
                        f"🚦 Action: {s}\n"
                        f"🎯 Confidence: {p}%\n"
                        f"⚡ Strategy: AI + RSI\n\n"
                        f"🚀 [TRADE NOW]({QUOTEX_LINK})"
                    )

                    try:
                        bot.send_message(ch_id, msg, parse_mode="Markdown")
                        print(f"✅ Sent: {a} {s} {p}%")
                    except Exception as e:
                        print(f"Send Error: {e}")

            time.sleep(300)

        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(30)

# ================== MAIN ==================
if __name__ == "__main__":
    try:
        print("🚀 RK BOT STARTED")

        # ✅ FIX 409 ERROR
        bot.remove_webhook()

        # ✅ Flask server thread
        threading.Thread(target=run_web).start()

        # ✅ Signal thread
        threading.Thread(target=signal_loop).start()

        # ✅ Stable polling
        bot.infinity_polling(
            timeout=30,
            long_polling_timeout=30,
            skip_pending=True
        )

    except Exception as e:
        print(f"❌ Fatal Error: {e}")
