import telebot
import threading
import time
import os
import random
import json
import yfinance as yf
import pandas as pd
import ta
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from flask import Flask, request

# ================== CONFIG ==================
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

VIP_INDIAN = os.environ.get("CHANNEL_ID_INDIAN")
VIP_FOREX = os.environ.get("CHANNEL_ID_GLOBAL")
FREE_CHANNEL = os.environ.get("RK_TRADING_FREE")

QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"

WEBHOOK_URL = os.environ.get("RAILWAY_STATIC_URL") + "/" + TOKEN

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATA_FILE = "data.json"

# ================== DATA ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"vip": [], "signals": [], "referrals": {}, "balance": {}}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# ================== AI ==================
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

        model = RandomForestClassifier(n_estimators=100)
        model.fit(X[:-1], y[:-1])

        pred = model.predict(X.tail(1))[0]
        prob = model.predict_proba(X.tail(1)).max() * 100

        return pred, prob

    except:
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

        rsi = ta.momentum.RSIIndicator(close).rsi().iloc[-1]

        signal = None

        if pred == 1 and rsi < 48:
            signal = "CALL 🟢"
        elif pred == 0 and rsi > 52:
            signal = "PUT 🔴"

        return asset, signal, round(prob, 2)

    except:
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

                if s and p > 80:
                    msg = f"📊 {a}\n🚦 {s}\n🎯 {p}%\n\n🚀 Trade: {QUOTEX_LINK}"

                    # save signal
                    data["signals"].append({
                        "asset": a,
                        "signal": s,
                        "time": time.time()
                    })
                    save_data(data)

                    # VIP channels
                    try:
                        bot.send_message(ch_id, msg)
                    except:
                        pass

                    # FREE channel (low confidence)
                    try:
                        if p < 85:
                            bot.send_message(FREE_CHANNEL, f"FREE SIGNAL ⚠️\n{a} {s}")
                    except:
                        pass

            time.sleep(300)

        except:
            time.sleep(30)

# ================== RESULT TRACK ==================
def result_tracker():
    while True:
        for s in data["signals"]:
            if "result" in s:
                continue

            if time.time() - s["time"] < 300:
                continue

            try:
                df = yf.download(s["asset"], period="1d", interval="1m", progress=False)
                close = df['Close'].squeeze()

                entry = close.iloc[-6]
                exit = close.iloc[-1]

                if "CALL" in s["signal"]:
                    s["result"] = "WIN" if exit > entry else "LOSS"
                else:
                    s["result"] = "WIN" if exit < entry else "LOSS"

            except:
                continue

        save_data(data)
        time.sleep(60)

# ================== TELEGRAM ==================
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg,
        "🚀 Welcome\n\nFree signals: Join channel\nVIP ke liye /buy"
    )

@bot.message_handler(commands=['buy'])
def buy(msg):
    bot.reply_to(msg,
        "💰 VIP Buy:\nUPI: yourupi@pay\nSend screenshot to admin"
    )

@bot.message_handler(commands=['approve'])
def approve(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    try:
        uid = msg.text.split()[1]
        data["vip"].append(uid)
        save_data(data)

        bot.send_message(uid, "✅ VIP Activated")
        bot.reply_to(msg, "Done")

    except:
        bot.reply_to(msg, "Error")

# ================== WEBHOOK ==================
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok"

@app.route("/")
def home():
    return "Bot Running"

# ================== START ==================
if __name__ == "__main__":
    print("🚀 FINAL PRO BOT RUNNING")

    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    threading.Thread(target=signal_loop, daemon=True).start()
    threading.Thread(target=result_tracker, daemon=True).start()

    app.run(host="0.0.0.0", port=8000)
