import telebot
import threading
import time
import os
import json
import requests
from datetime import datetime, timedelta
import yfinance as yf
import ta
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from flask import Flask, jsonify, request
from functools import wraps
import hashlib
import hmac

# ================= CONFIG =================
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 6589410347))
VIP_FOREX = os.environ.get("CHANNEL_ID_GLOBAL")
RAZORPAY_KEY = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")
PAYMENT_LINK = "https://rzp.io/l/yourlink"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DB_FILE = "users.json"
SIGNAL_FILE = "signals.json"
TRADES_FILE = "trades.json"
BACKTEST_FILE = "backtest.json"
ASSETS = ["EURUSD=X", "GBPUSD=X", "BTC-USD"]

# ================= JSON HELPERS =================
def load_json(file):
    if not os.path.exists(file): return {}
    with open(file, "r") as f:
        try: return json.load(f)
        except: return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

users = load_json(DB_FILE)
signals = load_json(SIGNAL_FILE)	rades = load_json(TRADES_FILE)
backtest_results = load_json(BACKTEST_FILE)

# ================= TRADE MANAGEMENT SYSTEM =================
class TradeManager:
    def __init__(self):
        self.open_trades = {}
    
    def create_trade(self, uid, asset, entry, risk, reward):
        trade_id = str(time.time())
        stop_loss = entry * (1 - risk/100)
        take_profit = entry * (1 + reward/100)
        
        self.open_trades[trade_id] = {
            "user_id": uid,
            "asset": asset,
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "status": "open",
            "created_at": str(datetime.now()),
            "exit_price": None,
            "result": None
        }
        
        trades[trade_id] = self.open_trades[trade_id]
        save_json(TRADES_FILE, trades)
        return trade_id
    
    def close_trade(self, trade_id, exit_price):
        if trade_id not in self.open_trades:
            return False
        
        trade = self.open_trades[trade_id]
        trade["exit_price"] = exit_price
        trade["status"] = "closed"
        
        if exit_price > trade["take_profit"]:
            trade["result"] = "win"
        elif exit_price < trade["stop_loss"]:
            trade["result"] = "loss"
        else:
            trade["result"] = "breakeven"
        
        trades[trade_id] = trade
        save_json(TRADES_FILE, trades)
        return True
    
    def get_user_trades(self, uid):
        return [t for t in self.open_trades.values() if t["user_id"] == uid]

trade_manager = TradeManager()

# ================= USER DASHBOARD SYSTEM =================
class UserStats:
    @staticmethod
    def get_user_dashboard(uid):
        user_trades = trade_manager.get_user_trades(uid)
        wins = sum(1 for t in user_trades if t.get("result") == "win")
        losses = sum(1 for t in user_trades if t.get("result") == "loss")
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        
        total_profit = sum(
            (t["exit_price"] - t["entry"]) for t in user_trades 
            if t["status"] == "closed" and t["exit_price"]
        )
        
        return {
            "total_trades": len(user_trades),
            "open_trades": sum(1 for t in user_trades if t["status"] == "open"),
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "total_profit": round(total_profit, 2)
        }

# ================= PAYMENT INTEGRATION (Razorpay) =================
def verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_signature = hmac.new(
        RAZORPAY_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return expected_signature == razorpay_signature

@app.route("/create-payment", methods=["POST"])
def create_payment():
    data = request.json
    uid = data.get("user_id")
    
    headers = {"X-Razorpay-App-Id": RAZORPAY_KEY}
    payload = {
        "amount": 99900,  # 999 rupees in paise
        "currency": "INR",
        "receipt": f"vip_{uid}",
        "notes": {"user_id": uid, "plan": "vip_30days"}
    }
    
    response = requests.post(
        "https://api.razorpay.com/v1/orders",
        json=payload,
        auth=(RAZORPAY_KEY, RAZORPAY_SECRET)
    )
    
    return jsonify(response.json())

@app.route("/verify-payment", methods=["POST"])
def verify_payment():
    data = request.json
    if verify_razorpay_signature(data["order_id"], data["payment_id"], data["signature"]):
        uid = data.get("user_id")
        users[uid]["vip"] = True
        users[uid]["expiry"] = str(datetime.now() + timedelta(days=30))
        save_json(DB_FILE, users)
        return jsonify({"status": "success"})
    return jsonify({"status": "failed"}), 400

# ================= ENHANCED SIGNAL SYSTEM =================
class SignalGenerator:
    def __init__(self):
        self.timeframes = ["1m", "5m", "15m", "1h"]
    
    def analyze_multi_timeframe(self, asset):
        signals_data = {}
        for tf in self.timeframes:
            try:
                df = yf.download(asset, period="60d", interval=tf, progress=False)
                if df.empty or len(df) < 20:
                    continue
                
                close = df['Close'].squeeze()
                df['RSI'] = ta.momentum.RSIIndicator(close).rsi()
                df['MACD'] = ta.trend.macd(close)
                df['BBands_Upper'] = ta.volatility.BollingerBands(close).bollinger_hband()
                df['BBands_Lower'] = ta.volatility.BollingerBands(close).bollinger_lband()
                
                current_price = close.iloc[-1]
                rsi = df['RSI'].iloc[-1]
                macd = df['MACD'].iloc[-1]
                
                signal = "BUY" if rsi < 30 and macd > 0 else "SELL" if rsi > 70 and macd < 0 else "HOLD"
                
                signals_data[tf] = {
                    "signal": signal,
                    "rsi": round(rsi, 2),
                    "macd": round(macd, 4),
                    "price": round(current_price, 4)
                }
            except:
                continue
        
        return signals_data
    
    def generate_signal(self):
        for asset in ASSETS:
            multi_tf = self.analyze_multi_timeframe(asset)
            if not multi_tf:
                continue
            
            buy_count = sum(1 for v in multi_tf.values() if v["signal"] == "BUY")
            
            if buy_count >= 2:  # At least 2 timeframes showing BUY
                entry = multi_tf[self.timeframes[0]]["price"]
                sid = str(time.time())
                signals[sid] = {
                    "asset": asset,
                    "entry": entry,
                    "time": str(datetime.now()),
                    "result": "pending",
                    "multi_tf": multi_tf
                }
                save_json(SIGNAL_FILE, signals)
                return sid, asset, entry, multi_tf
        
        return None

signal_generator = SignalGenerator()

# ================= BACKTESTING MODULE =================
def backtest_strategy(asset, start_date="2023-01-01", end_date="2024-01-01"):
    df = yf.download(asset, start=start_date, end=end_date, progress=False)
    if df.empty or len(df) < 50:
        return None
    
    close = df['Close'].squeeze()
    df['RSI'] = ta.momentum.RSIIndicator(close).rsi()
    df['Signal'] = np.where(df['RSI'] < 30, 1, np.where(df['RSI'] > 70, -1, 0))
    
    trades_list = []
    entry_price = None
    entry_idx = None
    
    for idx, row in df.iterrows():
        if row['Signal'] == 1 and entry_price is None:
            entry_price = row['Close']
            entry_idx = idx
        elif row['Signal'] == -1 and entry_price is not None:
            exit_price = row['Close']
            profit = exit_price - entry_price
            profit_pct = (profit / entry_price) * 100
            trades_list.append({
                "entry": entry_price,
                "exit": exit_price,
                "profit": round(profit, 2),
                "profit_pct": round(profit_pct, 2)
            })
            entry_price = None
    
    total_trades = len(trades_list)
    winning_trades = sum(1 for t in trades_list if t["profit"] > 0)
    total_profit = sum(t["profit"] for t in trades_list)
    
    sharpe_ratio = calculate_sharpe_ratio(trades_list) if trades_list else 0
    
    backtest_data = {
        "asset": asset,
        "period": f"{start_date} to {end_date}",
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "win_rate": round((winning_trades / total_trades * 100) if total_trades > 0 else 0, 2),
        "total_profit": round(total_profit, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "trades": trades_list,
        "timestamp": str(datetime.now())
    }
    
    backtest_results[asset] = backtest_data
    save_json(BACKTEST_FILE, backtest_results)
    
    return backtest_data

def calculate_sharpe_ratio(trades):
    if not trades or len(trades) < 2:
        return 0
    
    returns = [t["profit_pct"] for t in trades]
    mean_return = np.mean(returns)
    std_return = np.std(returns)
    
    return (mean_return / std_return) if std_return != 0 else 0

# ================= FLASK ROUTES =================
@app.route("/")
def home():
    return "🔥 RK PRO LEVEL 10 - ENHANCED TRADING BOT RUNNING"

@app.route("/dashboard")
def dashboard():
    total_users = len(users)
    vip_users = sum(1 for u in users.values() if u.get("vip"))
    all_trades = list(trades.values())
    won_trades = sum(1 for t in all_trades if t.get("result") == "win")
    lost_trades = sum(1 for t in all_trades if t.get("result") == "loss")
    accuracy = (won_trades / (won_trades + lost_trades) * 100) if (won_trades + lost_trades) > 0 else 0
    
    return jsonify({
        "users": total_users,
        "vip_users": vip_users,
        "accuracy": round(accuracy, 2),
        "total_trades": len(all_trades),
        "won_trades": won_trades,
        "lost_trades": lost_trades
    })

@app.route("/user-stats/<uid>")
def user_stats(uid):
    stats = UserStats.get_user_dashboard(uid)
    return jsonify(stats)

@app.route("/backtest/<asset>")
def backtest_api(asset):
    result = backtest_strategy(asset)
    if result:
        return jsonify(result)
    return jsonify({"error": "Backtest failed"}), 400

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

# ================= SIGNAL LOOP =================
def signal_loop():
    while True:
        try:
            sig = signal_generator.generate_signal()
            if sig:
                sid, asset, entry, multi_tf = sig
                tf_str = "\\n".join([f"{k}: {v['signal']} (RSI: {v['rsi']})" for k, v in multi_tf.items()])
                msg = f"🔥 **VIP AI SIGNAL**\\n\\n📊 Asset: {asset}\\n💰 Entry: {entry}\\n\\n📈 **Multi-Timeframe Analysis:**\\n{tf_str}\\n\\n🚀 [TRADE ON QUOTEX](https://broker-qx.pro/?lid=2061690)"
                try:
                    bot.send_message(VIP_FOREX, msg, parse_mode="Markdown")
                except:
                    pass
        except Exception as e:
            print(f"Signal generation error: {e}")
        
        time.sleep(300)

# ================= BOT COMMANDS =================
@bot.message_handler(commands=["start"])
def start(msg):
    uid = str(msg.chat.id)
    if uid not in users:
        users[uid] = {"vip": False, "created_at": str(datetime.now())}
        save_json(DB_FILE, users)
    
    bot.send_message(uid, f"🚀 **RK PRO ACTIVE**\\n\\nReferral link:\\nhttps://t.me/YOUR_BOT?start={uid}\\n\\nCommands:\\n/stats - View your stats\\n/trades - View your trades\\n/backtest - Run backtest\\n/pay - Get VIP access")

@bot.message_handler(commands=["stats"])
def stats_cmd(msg):
    uid = str(msg.chat.id)
    stats = UserStats.get_user_dashboard(uid)
    msg_text = f"📊 **YOUR TRADING STATS**\\n\\nTotal Trades: {stats['total_trades']}\\nOpen: {stats['open_trades']}\\nWins: {stats['wins']}\\nLosses: {stats['losses']}\\nWin Rate: {stats['win_rate']}%\\nTotal Profit: ${stats['total_profit']}"
    bot.send_message(uid, msg_text, parse_mode="Markdown")

@bot.message_handler(commands=["pay"])
def pay_cmd(msg):
    uid = str(msg.chat.id)
    bot.send_message(uid, f"💳 **GET VIP ACCESS**\\n\\n₹999 for 30 days\\n\\n[PAY NOW]({PAYMENT_LINK})", parse_mode="Markdown")

@bot.message_handler(commands=["approve"])
def approve(msg):
    if msg.chat.id != ADMIN_ID:
        return
    
    try:
        uid = msg.text.split()[1]
        users[uid] = users.get(uid, {})
        users[uid]["vip"] = True
        users[uid]["expiry"] = str(datetime.now() + timedelta(days=30))
        save_json(DB_FILE, users)
        bot.send_message(uid, "✅ **VIP Activated!** 🔥")
        bot.send_message(ADMIN_ID, f"✅ User {uid} activated")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Error: {str(e)}")

@bot.message_handler(func=lambda msg: True)
def handle_messages(msg):
    uid = str(msg.chat.id)
    if msg.text.lower() == "dashboard":
        stats = UserStats.get_user_dashboard(uid)
        bot.send_message(uid, json.dumps(stats, indent=2))

# ================= MAIN RUNNER =================
if __name__ == "__main__":
    try:
        bot.remove_webhook()
    except:
        pass
    
    print("🚀 Starting RK PRO Trading Bot v2.0...")
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=signal_loop, daemon=True).start()
    
    print("✅ Web server and signal loop started!")
    print("🚀 Bot is now polling for messages...")
    
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
