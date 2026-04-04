import telebot
import threading
import time
import os
import random
import json
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd
import ta
from sklearn.ensemble import RandomForestClassifier
import numpy as np

from flask import Flask, jsonify

# ================= CONFIG =================
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

VIP_INDIAN = os.environ.get("CHANNEL_ID_INDIAN")
VIP_FOREX = os.environ.get("CHANNEL_ID_GLOBAL")

bot = telebot.TeleBot(TOKEN)

DB_FILE = "users.json"
SIGNAL_FILE = "signals.json"

# ================= DATABASE =================
def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

users = load_json(DB_FILE)
signals_db = load_json(SIGNAL_FILE)

# ================= FLASK =================
app = Flask(__name__)

@app.route("/")
def home():
    return "🚀 LEVEL 7 BOT RUNNING"

@app.route("/stats")
def stats():
    total = len(users)
    vip = sum(1 for u in users.values() if u.get("vip"))

    wins = sum(1 for s in signals_db.values() if s["result"] == "win")
    loss = sum(1 for s in signals_db.values() if s["result"] == "loss")

    return jsonify({
        "users": total,
        "vip_users": vip,
        "wins": wins,
        "loss": loss
    })

def run_web():
    app.run(host="0.0.0.0", port=8080)

# ================= AI =================
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

# ================= SIGNAL =================
def get_signal():
    asset = "EURUSD=X"

    df = yf.download(asset, period="1d", interval="1m", progress=False)

    if df is None or df.empty or len(df) < 60:
        return None

    pred, prob = train_and_predict(df)

    if prob < 85:
        return None

    signal_id = str(time.time())

    signals_db[signal_id] = {
        "asset": asset,
        "time": str(datetime.now()),
        "result": "pending"
    }

    save_json(SIGNAL_FILE, signals_db)

    return signal_id, asset, prob

# ================= TRACK RESULT =================
def check_results():
    while True:
        for sid, data in signals_db.items():
            if data["result"] == "pending":
                # Fake result (demo)
                data["result"] = random.choice(["win", "loss"])

        save_json(SIGNAL_FILE, signals_db)
        time.sleep(600)

# ================= SIGNAL LOOP =================
def signal_loop():
    while True:
        sig = get_signal()

        if sig:
            sid, asset, prob = sig

            msg = f"🔥 VIP SIGNAL\n{asset}\nConfidence: {prob}%"

            try:
                bot.send_message(VIP_FOREX, msg)
            except:
                pass

        time.sleep(300)

# ================= BOT =================
@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.chat.id)

    if uid not in users:
        users[uid] = {"vip": False, "expiry": None}
        save_json(DB_FILE, users)

    bot.send_message(uid, "Welcome!\nUse /vip to buy VIP")

@bot.message_handler(commands=['vip'])
def vip(msg):
    bot.send_message(msg.chat.id,
        "VIP ₹199/month\nUPI: yourupi@upi\nSend screenshot"
    )

@bot.message_handler(content_types=['photo'])
def payment(msg):
    bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
    bot.send_message(msg.chat.id, "⏳ Waiting for approval")

@bot.message_handler(commands=['approve'])
def approve(msg):
    if msg.chat.id != ADMIN_ID:
        return

    try:
        uid = msg.text.split()[1]

        users[uid]["vip"] = True
        users[uid]["expiry"] = str(datetime.now() + timedelta(days=30))

        save_json(DB_FILE, users)

        bot.send_message(uid, "✅ VIP Activated 30 Days")
    except:
        bot.send_message(msg.chat.id, "Error")

# ================= VIP CHECK =================
def vip_expiry_check():
    while True:
        for uid, data in users.items():
            if data.get("vip") and data.get("expiry"):
                if datetime.now() > datetime.fromisoformat(data["expiry"]):
                    data["vip"] = False

        save_json(DB_FILE, users)
        time.sleep(3600)

# ================= MAIN =================
if __name__ == "__main__":
    bot.remove_webhook()

    threading.Thread(target=run_web).start()
    threading.Thread(target=signal_loop).start()
    threading.Thread(target=check_results).start()
    threading.Thread(target=vip_expiry_check).start()

    bot.infinity_polling()
