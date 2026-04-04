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
from flask import Flask

# ================== CONFIG ==================
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

VIP_INDIAN = os.environ.get("CHANNEL_ID_INDIAN")
VIP_FOREX = os.environ.get("CHANNEL_ID_GLOBAL")

QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"

bot = telebot.TeleBot(TOKEN)

DB_FILE = "users.json"

# ================== LOAD/SAVE USERS ==================
def load_users():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

users = load_users()

# ================== FLASK ==================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ RK LEVEL 5 BOT RUNNING"

def run_web():
    app.run(host="0.0.0.0", port=8080)

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

        model = RandomForestClassifier()
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
        for assets, ch in [
            (["^NSEI"], VIP_INDIAN),
            (["EURUSD=X"], VIP_FOREX)
        ]:
            a, s, p = get_ai_signal(assets)

            if s and p > 85:
                msg = f"🔥 VIP SIGNAL\n\n{a}\n{s}\nConfidence: {p}%"

                try:
                    bot.send_message(ch, msg)
                except:
                    pass

        time.sleep(300)

# ================== BOT COMMANDS ==================

@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.chat.id)

    if uid not in users:
        users[uid] = {"vip": False}
        save_users(users)

    bot.send_message(uid,
        "👋 Welcome!\n\n"
        "Free signals limited.\n"
        "VIP lene ke liye /vip likho"
    )

@bot.message_handler(commands=['vip'])
def vip(msg):
    bot.send_message(msg.chat.id,
        "💰 VIP PLAN\n\n"
        "1 Month = ₹199\n\n"
        "UPI: yourupi@upi\n\n"
        "Payment ke baad screenshot bhejo"
    )

# ================== PAYMENT PROOF ==================
@bot.message_handler(content_types=['photo'])
def payment_proof(msg):
    uid = str(msg.chat.id)

    bot.send_message(ADMIN_ID,
        f"💰 Payment Request from {uid}",
    )

    bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)

    bot.send_message(uid, "⏳ Verification pending...")

# ================== ADMIN APPROVE ==================
@bot.message_handler(commands=['approve'])
def approve(msg):
    if msg.chat.id != ADMIN_ID:
        return

    try:
        uid = msg.text.split()[1]
        users[uid]["vip"] = True
        save_users(users)

        bot.send_message(uid, "✅ VIP Activated!")
    except:
        bot.send_message(msg.chat.id, "❌ Error")

# ================== MAIN ==================
if __name__ == "__main__":
    bot.remove_webhook()

    threading.Thread(target
