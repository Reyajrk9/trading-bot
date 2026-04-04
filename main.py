import telebot
import threading
import time
import os
import json
from datetime import datetime, timedelta

import yfinance as yf
import ta
from sklearn.ensemble import RandomForestClassifier
import numpy as np

from flask import Flask, jsonify

# ================= CONFIG =================
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
VIP_FOREX = os.environ.get("CHANNEL_ID_GLOBAL")

PAYMENT_LINK = "https://rzp.io/l/yourlink"

bot = telebot.TeleBot(TOKEN)

DB_FILE = "users.json"
SIGNAL_FILE = "signals.json"

ASSETS = ["EURUSD=X", "GBPUSD=X", "BTC-USD"]

trades = []

# ================= JSON =================
def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

users = load_json(DB_FILE)
signals = load_json(SIGNAL_FILE)

# ================= FLASK =================
app = Flask(__name__)

@app.route("/")
def home():
    return "🔥 LEVEL 10 RUNNING"

@app.route("/dashboard")
def dashboard():
    total = len(users)
    vip = sum(1 for u in users.values() if u.get("vip"))

    wins = sum(1 for s in signals.values() if s["result"] == "win")
    loss = sum(1 for s in signals.values() if s["result"] == "loss")

    acc = (wins / (wins + loss) * 100) if (wins + loss) > 0 else 0

    return jsonify({
        "users": total,
        "vip_users": vip,
        "wins": wins,
        "loss": loss,
        "accuracy": round(acc, 2),
        "trades": len(trades)
    })

@app.route("/pro")
def pro():
    revenue = sum(199 for u in users.values() if u.get("vip"))

    return jsonify({
        "revenue_est": revenue,
        "total_trades": len(trades)
    })

def run_web():
    app.run(host="0.0.0.0", port=8080)

# ================= AI =================
def train_and_predict(df):
    close = df['Close'].squeeze()

    df['RSI'] = ta.momentum.RSIIndicator(close).rsi()
    df['Change'] = close.pct_change()
    df['Target'] = np.where(close.shift(-1) > close, 1, 0)

    df = df.dropna()
    if len(df) < 50:
        return None, 0

    X = df[['RSI', 'Change']]
    y = df['Target']

    model = RandomForestClassifier()
    model.fit(X[:-1], y[:-1])

    pred = model.predict(X.tail(1))[0]
    prob = model.predict_proba(X.tail(1)).max() * 100

    return pred, prob

# ================= AUTO TRADE =================
def auto_trade(asset, entry):
    result = "win" if np.random.rand() > 0.4 else "loss"

    trades.append({
        "asset": asset,
        "entry": entry,
        "result": result
    })

# ================= SIGNAL =================
def generate_signal():
    for asset in ASSETS:

        df = yf.download(asset, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 60:
            continue

        pred, prob = train_and_predict(df)

        if prob < 87:
            continue

        entry = float(df['Close'].iloc[-1])
        sid = str(time.time())

        signals[sid] = {
            "asset": asset,
            "entry": entry,
            "time": str(datetime.now()),
            "result": "pending"
        }

        save_json(SIGNAL_FILE, signals)

        auto_trade(asset, entry)

        return sid, asset, entry, prob

    return None

# ================= RESULT TRACK =================
def check_results():
    while True:
        for sid, s in signals.items():
            if s["result"] == "pending":

                df = yf.download(s["asset"], period="5m", interval="1m", progress=False)

                if not df.empty:
                    current = df['Close'].iloc[-1]

                    if current > s["entry"] * 1.0005:
                        s["result"] = "win"
                    else:
                        s["result"] = "loss"

        save_json(SIGNAL_FILE, signals)
        time.sleep(300)

# ================= SIGNAL LOOP =================
def signal_loop():
    while True:
        sig = generate_signal()

        if sig:
            sid, asset, entry, prob = sig

            msg = f"""
🔥 VIP SIGNAL

📊 Asset: {asset}
💰 Entry: {entry}
📈 Confidence: {prob}%

⚠️ Use proper risk management
"""

            try:
                bot.send_message(VIP_FOREX, msg)
            except:
                pass

        time.sleep(300)

# ================= BOT =================
@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.chat.id)
    ref = msg.text.split()[1] if len(msg.text.split()) > 1 else None

    if uid not in users:
        users[uid] = {"vip": False, "expiry": None, "ref_by": ref}
        save_json(DB_FILE, users)

        if ref and ref in users:
            users[ref]["vip"] = True
            users[ref]["expiry"] = str(datetime.now() + timedelta(days=3))

    bot.send_message(uid, f"Welcome!\n\nReferral link:\nhttps://t.me/YOURBOT?start={uid}")

@bot.message_handler(commands=['buy'])
def buy(msg):
    bot.send_message(msg.chat.id,
        f"💰 VIP ₹199\n\n👉 Pay here:\n{PAYMENT_LINK}\n\nScreenshot bhejo")

@bot.message_handler(content_types=['photo'])
def payment(msg):
    uid = str(msg.chat.id)

    bot.send_message(uid, "⏳ Verifying payment...")

    bot.forward_message(ADMIN_ID, uid, msg.message_id)

    bot.send_message(ADMIN_ID,
        f"User ID: {uid}\nUse /approve {uid}")

@bot.message_handler(commands=['approve'])
def approve(msg):
    if msg.chat.id != ADMIN_ID:
        return

    try:
        uid = msg.text.split()[1]

        users[uid]["vip"] = True
        users[uid]["expiry"] = str(datetime.now() + timedelta(days=30))

        save_json(DB_FILE, users)

        bot.send_message(uid, "✅ VIP Activated 🔥")

    except:
        bot.send_message(msg.chat.id, "Error")

# ================= VIP CHECK =================
def vip_check():
    while True:
        for uid, data in users.items():
            if data.get("vip") and data.get("expiry"):

                exp = datetime.fromisoformat(data["expiry"])
                now = datetime.now()

                if 0 < (exp - now).total_seconds() < 86400:
                    try:
                        bot.send_message(uid, "⚠️ VIP expire hone wala hai! /buy")
                    except:
                        pass

                if now > exp:
                    data["vip"] = False
                    try:
                        bot.send_message(uid, "❌ VIP expired! /buy")
                    except:
                        pass

        save_json(DB_FILE, users)
        time.sleep(3600)

# ================= MAIN =================
if __name__ == "__main__":
    bot.remove_webhook()

    threading.Thread(target=run_web).start()
    threading.Thread(target=signal_loop).start()
    threading.Thread(target=check_results).start()
    threading.Thread(target=vip_check).start()

    bot.infinity_polling()
