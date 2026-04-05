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

# ================= CONFIG (Railway Se Uthayega) =================
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 6589410347))
VIP_FOREX = os.environ.get("CHANNEL_ID_GLOBAL")
PAYMENT_LINK = "https://rzp.io/l/yourlink"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DB_FILE = "users.json"
SIGNAL_FILE = "signals.json"
ASSETS = ["EURUSD=X", "GBPUSD=X", "BTC-USD"]
trades = []

# ================= JSON HELPERS =================
def load_json(file):
    if not os.path.exists(file): return {}
    with open(file, "r") as f:
        try: return json.load(f)
        except: return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

users = load_json(DB_FILE)
signals = load_json(SIGNAL_FILE)

# ================= FLASK (Railway Port Fix) =================
@app.route("/")
def home(): return "🔥 RK PRO LEVEL 10 RUNNING"

@app.route("/dashboard")
def dashboard():
    total = len(users)
    vip = sum(1 for u in users.values() if u.get("vip"))
    wins = sum(1 for s in signals.values() if s.get("result") == "win")
    loss = sum(1 for s in signals.values() if s.get("result") == "loss")
    acc = (wins / (wins + loss) * 100) if (wins + loss) > 0 else 0
    return jsonify({"users": total, "vip_users": vip, "accuracy": round(acc, 2), "trades": len(trades)})

def run_web():
    # Railway environment variable se port uthayega
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ================= AI ENGINE (Fixed Truth Value Error) =================
def train_and_predict(df):
    try:
        # Fixed: Ensuring 1D data for TA
        close = df['Close'].squeeze()
        df['RSI'] = ta.momentum.RSIIndicator(close).rsi()
        df['Change'] = close.pct_change()
        df['Target'] = np.where(close.shift(-1) > close, 1, 0)
        df = df.dropna()
        if len(df) < 50: return None, 0
        X = df[['RSI', 'Change']]
        y = df['Target']
        model = RandomForestClassifier(n_estimators=100)
        model.fit(X[:-1], y[:-1])
        pred = model.predict(X.tail(1))[0]
        prob = model.predict_proba(X.tail(1)).max() * 100
        return pred, prob
    except: return None, 0

# ================= SIGNAL SYSTEM =================
def generate_signal():
    for asset in ASSETS:
        df = yf.download(asset, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 60: continue
        pred, prob = train_and_predict(df)
        if prob < 87: continue
        entry = float(df['Close'].iloc[-1])
        sid = str(time.time())
        signals[sid] = {"asset": asset, "entry": entry, "time": str(datetime.now()), "result": "pending"}
        save_json(SIGNAL_FILE, signals)
        return sid, asset, entry, prob
    return None

def signal_loop():
    while True:
        sig = generate_signal()
        if sig:
            sid, asset, entry, prob = sig
            msg = f"🔥 **VIP AI SIGNAL**\n\n📊 Asset: {asset}\n💰 Entry: {entry}\n📈 AI Confidence: {round(prob, 2)}%\n\n🚀 [TRADE ON QUOTEX](https://broker-qx.pro/?lid=2061690)"
            try: bot.send_message(VIP_FOREX, msg, parse_mode="Markdown")
            except: pass
        time.sleep(300)

# ================= BOT COMMANDS =================
@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.chat.id)
    bot.send_message(uid, f"🚀 **RK PRO ACTIVE**\n\nReferral link:\nhttps://t.me/YOUR_BOT?start={uid}")

@bot.message_handler(commands=['approve'])
def approve(msg):
    if msg.chat.id != ADMIN_ID: return
    try:
        uid = msg.text.split()[1]
        users[uid] = users.get(uid, {})
        users[uid]["vip"] = True
        users[uid]["expiry"] = str(datetime.now() + timedelta(days=30))
        save_json(DB_FILE, users)
        bot.send_message(uid, "✅ **VIP Activated!** 🔥")
    except: bot.send_message(ADMIN_ID, "Error in ID")

# ================= MAIN RUNNER =================
if __name__ == "__main__":
    # Conflict fix
    bot.remove_webhook()
    
    # Background Threads
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=signal_loop, daemon=True).start()
    
    print("🚀 Level 10 Bot Started Successfully!")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
