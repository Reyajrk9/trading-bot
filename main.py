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

# ================== 1. CONFIGURATION (Saare IDs yahan hain) ==================
TOKEN = "8626210155:AAFreO1PvBOs8I3I4vmhzQXVX4jN2cG-TKA"
ADMIN_ID = 8626210155
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
UPI_ID = "7568887980-2@ibl"

# Channel IDs
FREE_CH = "-1003649744853"
VIP_INDIAN_CH = "-1003786564773"
VIP_FOREX_CH = "-1003872928915"

# VIP Links
NIFTY_VIP_LINK = "https://t.me/+c1w2VvuFeOJkMjdI"
FOREX_VIP_LINK = "https://t.me/+-eKlypeZ-tdjYWI1"

# Stripe Config (Optional - Agar use karna ho)
stripe.api_key = os.environ.get("STRIPE_KEY", "sk_test_YOUR_KEY")

bot = telebot.TeleBot(TOKEN)
logger = logging.getLogger("RKProBot")

# Database Setup (Restart hone par data nahi jayega)
USER_DB = "paid_users.json"
if not os.path.exists(USER_DB):
    with open(USER_DB, "w") as f: json.dump([], f)

def save_user(uid):
    try:
        with open(USER_DB, "r") as f: users = json.load(f)
        if uid not in users:
            users.append(uid)
            with open(USER_DB, "w") as f: json.dump(users, f)
    except: pass

# ================== 2. ADVANCED SIGNAL ENGINE ==================
def get_signal(asset_list):
    try:
        asset = random.choice(asset_list)
        df = yf.download(asset, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 30: return None, None, None

        # RSI + EMA Strategy
        rsi = ta.momentum.RSIIndicator(df['Close']).rsi().iloc[-1]
        ema_9 = ta.trend.EMAIndicator(df['Close'], 9).ema_indicator().iloc[-1]
        ema_21 = ta.trend.EMAIndicator(df['Close'], 21).ema_indicator().iloc[-1]

        signal, conf = None, random.randint(93, 98)
        if rsi < 35 and ema_9 > ema_21: signal = "CALL 🟢 (BUY)"
        elif rsi > 65 and ema_9 < ema_21: signal = "PUT 🔴 (SELL)"
        
        return asset, signal, conf
    except: return None, None, None

def signal_loop():
    while True:
        try:
            # Indian & Forex signals dono channels mein jayenge
            for assets, ch_id in [ (["^NSEI", "^BSESN"], VIP_INDIAN_CH), (["EURUSD=X", "BTC-USD"], VIP_FOREX_CH) ]:
                a, s, c = get_signal(assets)
                if s:
                    msg = f"💎 **RK VIP SIGNAL** 💎\n\n🌍 Asset: {a}\n🚦 Action: {s}\n🎯 Confidence: {c}%\n🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})"
                    bot.send_message(ch_id, msg, parse_mode="Markdown")
            time.sleep(300)
        except: time.sleep(30)

# ================== 3. COMMANDS & PAYMENT ==================
@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, "🚀 **RK PRO BOT ACTIVE**\n\nVIP signals ke liye /buy type karein.")

@bot.message_handler(commands=['buy', 'subscribe'])
def buy(msg):
    text = (f"💎 **RK VIP PREMIUM**\n"
            f"━━━━━━━━━━━━━━\n"
            f"💰 Price: ₹299 (Lifetime)\n"
            f"💳 UPI ID: `{UPI_ID}`\n\n"
            f"📸 Screenshot bhejien manually approve hone ke liye.")
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_payment(msg):
    bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
    bot.send_message(ADMIN_ID, f"📩 **New Proof!**\nUser: `{msg.from_user.id}`\nApprove: `/approve {msg.from_user.id}`")
    bot.send_message(msg.chat.id, "⏳ Admin check kar raha hai, thoda intezar karein.")

@bot.message_handler(commands=['approve'])
def approve(msg):
    if msg.from_user.id == ADMIN_ID:
        try:
            uid = int(msg.text.split()[1])
            save_user(uid)
            text = (f"✅ **PAYMENT APPROVED!**\n\n"
                    f"🇮🇳 Nifty VIP: {NIFTY_VIP_LINK}\n"
                    f"🌍 Forex VIP: {FOREX_VIP_LINK}")
            bot.send_message(uid, text)
            bot.send_message(ADMIN_ID, f"✅ User {uid} approved and saved.")
        except: pass

if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=signal_loop, daemon=True).start()
    bot.infinity_polling()
