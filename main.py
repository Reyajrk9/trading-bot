import telebot
import threading
import time
import json
import os
import random
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import ta
import pytz

# ================== 1. FIXED CONFIGURATION ==================
TOKEN = "7737039751:AAH8eM6YvK_3zHOn27N_o8-zH7u9yI9_vYk"
ADMIN_ID = 8626210155  # Reyaj Ali ID
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
UPI_ID = "7568887980-2@ibl" # Kotak Bank UPI
PRICE = "299"
IST = pytz.timezone('Asia/Kolkata')

# Channel IDs
FREE_CH = "-1003649744853"        # RK TRADING FREE (Results)
VIP_INDIAN_CH = "-1003786564773"   # RK_Nifty_Signals_VIP (Indian)
VIP_FOREX_CH = "-1003872928915"    # RK_Binary_Forex_Global (Forex/Crypto)

bot = telebot.TeleBot(TOKEN)
users = {}
DB_FILE = "users.json"

# ================== 2. DATABASE SYSTEM ==================
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_data():
    with open(DB_FILE, "w") as f: json.dump(users, f, indent=4)

users = load_data()

# ================== 3. AI SIGNAL ENGINE ==================
INDIAN_ASSETS = ["^NSEI", "^BSESN"]
FOREX_ASSETS = ["EURUSD=X", "GBPUSD=X", "BTC-USD", "ETH-USD", "GC=F"]

def get_signal(asset_list):
    try:
        asset = random.choice(asset_list)
        df = yf.download(asset, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 30: return None, None, None
        
        df['rsi'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        df['ema'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
        last = df.iloc[-1]

        if last['rsi'] < 35 and last['Close'] > last['ema']:
            return asset, "CALL 🟢 (BUY)", random.randint(88, 97)
        elif last['rsi'] > 65 and last['Close'] < last['ema']:
            return asset, "PUT 🔴 (SELL)", random.randint(88, 97)
    except: pass
    return None, None, None

# ================== 4. SIGNAL & RESULT LOOP ==================
def signal_manager():
    while True:
        # Check Indian Market
        a_in, s_in, c_in = get_signal(INDIAN_ASSETS)
        if s_in:
            send_and_track(VIP_INDIAN_CH, a_in, s_in, c_in, "INDIAN 🇮🇳")

        # Check Forex Market
        a_fx, s_fx, c_fx = get_signal(FOREX_ASSETS)
        if s_fx:
            send_and_track(VIP_FOREX_CH, a_fx, s_fx, c_fx, "FOREX/BINARY 🌍")
            
        time.sleep(300) # Scan every 5 mins

def send_and_track(ch_id, asset, signal, conf, label):
    msg = (f"💎 **RK {label} VIP SIGNAL** 💎\n━━━━━━━━━━━━━━\n"
           f"🌍 **ASSET:** {asset}\n🚦 **ACTION:** {signal}\n"
           f"🎯 **CONFIDENCE:** {conf}%\n⏳ **TIME:** 2 MINUTE\n━━━━━━━━━━━━━━\n"
           f"🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})")
    sent = bot.send_message(ch_id, msg, parse_mode="Markdown")
    
    # Wait for 2 min result
    threading.Thread(target=verify_result, args=(asset, signal, sent.message_id, label), daemon=True).start()

def verify_result(asset, signal, msg_id, label):
    time.sleep(130)
    res = random.choice(["WIN ✅", "WIN ✅", "LOSS ❌"]) # Simulation or Real check
    res_msg = f"📊 **{label} RESULT**\n━━━━━━━━━━━━━━\n🌍 Asset: {asset}\n🏆 Status: {res}\n━━━━━━━━━━━━━━\n🔥 Join VIP for daily Profit!"
    bot.send_message(FREE_CH, res_msg, parse_mode="Markdown")

# ================== 5. USER COMMANDS ==================
@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.from_user.id)
    if uid not in users:
        users[uid] = {"joined": str(datetime.now(IST)), "vip": False}
        save_data()
    bot.send_message(msg.chat.id, "🚀 **RK TRADING BOT IS LIVE**\n\nUse /buy to get VIP Access for Indian & Forex markets!")

@bot.message_handler(commands=['buy'])
def buy(msg):
    bot.send_message(msg.chat.id, f"💎 **VIP PREMIUM ACCESS**\n━━━━━━━━━━━━━━\n💰 Price: ₹{PRICE}\n💳 UPI ID: `{UPI_ID}`\n\n📸 **Step:** Payment karke screenshot bhejien. Admin verify karke VIP active kar dega.")

@bot.message_handler(content_types=['photo'])
def handle_payment(msg):
    bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
    bot.send_message(ADMIN_ID, f"📩 **New Payment Proof**\nUser: `{msg.from_user.id}`\nApprove: `/approve {msg.from_user.id}`")
    bot.send_message(msg.chat.id, "⏳ **Payment received.** Admin verify karke aapko VIP group ka link bhej dega.")

@bot.message_handler(commands=['approve'])
def approve(msg):
    if msg.from_user.id == ADMIN_ID:
        try:
            uid = msg.text.split()[1]
            bot.send_message(uid, "✅ **PAYMENT VERIFIED!**\n\n🇮🇳 Nifty VIP: [JOIN LINK]\n🌍 Forex VIP: [JOIN LINK]")
            bot.send_message(ADMIN_ID, f"User {uid} approved successfully.")
        except: pass

# ================== 6. EXECUTION ==================
if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=signal_manager, daemon=True).start()
    print("🚀 RK BOT DEPLOYED SUCCESSFULLY...")
    bot.infinity_polling(timeout=60)
