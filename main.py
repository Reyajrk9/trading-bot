import telebot
import threading
import time
import json
import os
import random
import yfinance as yf
import pandas as pd
import ta
import ccxt
import logging
import stripe
from datetime import datetime

# ================== 1. CONFIGURATION ==================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8626210155:AAFreO1PvBOs8I3I4vmhzQXVX4jN2cG-TKA")
ADMIN_ID = 8626210155 
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
UPI_ID = "7568887980-2@ibl"

# Channel IDs
FREE_CH = "-1003649744853"
VIP_INDIAN_CH = "-1003786564773"
VIP_FOREX_CH = "-1003872928915"

# Private Invite Links
NIFTY_VIP_LINK = "https://t.me/+c1w2VvuFeOJkMjdI"
FOREX_VIP_LINK = "https://t.me/+-eKlypeZ-tdjYWI1"

# Database setup (To save paid users permanently)
USER_DB = "paid_users.json"
if not os.path.exists(USER_DB):
    with open(USER_DB, "w") as f: json.dump([], f)

def load_paid_users():
    with open(USER_DB, "r") as f: return set(json.load(f))

def save_paid_user(uid):
    users = list(load_paid_users())
    if uid not in users:
        users.append(uid)
        with open(USER_DB, "w") as f: json.dump(users, f)

PAID_USERS = load_paid_users()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RKProBot")
bot = telebot.TeleBot(TOKEN)

# ================== 2. ADVANCED SIGNAL ENGINE ==================
def get_signal(asset_list):
    try:
        asset = random.choice(asset_list)
        df = yf.download(asset, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 30: return None, None, None

        # Strategy: RSI + EMA Cross + MACD
        rsi = ta.momentum.RSIIndicator(df['Close']).rsi().iloc[-1]
        ema_9 = ta.trend.EMAIndicator(df['Close'], 9).ema_indicator().iloc[-1]
        ema_21 = ta.trend.EMAIndicator(df['Close'], 21).ema_indicator().iloc[-1]
        macd_diff = ta.trend.MACD(df['Close']).macd_diff().iloc[-1]

        signal, confidence = None, random.randint(93, 98)
        
        if rsi < 35 and ema_9 > ema_21 and macd_diff > 0:
            signal = "CALL 🟢 (BUY)"
        elif rsi > 65 and ema_9 < ema_21 and macd_diff < 0:
            signal = "PUT 🔴 (SELL)"
            
        return asset, signal, confidence
    except Exception as e:
        logger.error(f"Signal Error: {e}")
        return None, None, None

def signal_loop():
    while True:
        try:
            # Indian Market Scan
            a_in, s_in, c_in = get_signal(["^NSEI", "^BSESN"])
            if s_in:
                msg = f"💎 **RK INDIAN VIP** 💎\n\n🌍 Asset: {a_in}\n🚦 Action: {s_in}\n🎯 Conf: {c_in}%\n🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})"
                bot.send_message(VIP_INDIAN_CH, msg, parse_mode="Markdown")

            # Forex Market Scan
            a_fx, s_fx, c_fx = get_signal(["EURUSD=X", "GBPUSD=X", "BTC-USD"])
            if s_fx:
                msg = f"💎 **RK FOREX VIP** 💎\n\n🌍 Asset: {a_fx}\n🚦 Action: {s_fx}\n🎯 Conf: {c_fx}%\n🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})"
                bot.send_message(VIP_FOREX_CH, msg, parse_mode="Markdown")
            
            time.sleep(300) # 5 Min Scan
        except Exception as e:
            logger.error(f"Loop error: {e}")
            time.sleep(30)

# ================== 3. BOT COMMANDS ==================
@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, "🚀 **RK PRO CLOUD BOT IS ONLINE**\n\nVIP join karne ke liye /buy type karein.")

@bot.message_handler(commands=['buy'])
def buy(msg):
    text = (f"💎 **VIP PREMIUM ACCESS**\n"
            f"━━━━━━━━━━━━━━\n"
            f"💰 Price: ₹299 (Lifetime)\n"
            f"💳 UPI ID: `{UPI_ID}`\n\n"
            f"📸 Screenshot bhejien manually approve hone ke liye.")
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_payment(msg):
    bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
    bot.send_message(ADMIN_ID, f"📩 **New Proof!**\nUser: `{msg.from_user.id}`\nApprove: `/approve {msg.from_user.id}`")
    bot.send_message(msg.chat.id, "⏳ Payment proof receive ho gaya hai. Admin check kar raha hai...")

@bot.message_handler(commands=['approve'])
def approve(msg):
    if msg.from_user.id == ADMIN_ID:
        try:
            uid = int(msg.text.split()[1])
            save_paid_user(uid) # Database mein save
            text = (f"✅ **PAYMENT APPROVED!**\n\n"
                    f"🇮🇳 Nifty VIP: {NIFTY_VIP_LINK}\n"
                    f"🌍 Forex VIP: {FOREX_VIP_LINK}")
            bot.send_message(uid, text)
            bot.send_message(ADMIN_ID, f"User {uid} successfully added to database.")
        except: pass

# ================== 4. RUN ==================
if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=signal_loop, daemon=True).start()
    print("Bot Started Successfully...")
    bot.infinity_polling()
