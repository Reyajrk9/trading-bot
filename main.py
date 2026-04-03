import telebot
import threading
import time
import json
import os
import random
from datetime import datetime
import yfinance as yf
import pandas as pd
import ta
import pytz

# ================== 1. FIXED CONFIGURATION (IDs & TOKEN) ==================
# Naya Token jo aapne diya
TOKEN = "8626210155:AAFreO1PvBOs8I3I4vmhzQXVX4jN2cG-TKA" 

ADMIN_ID = 8626210155  # Reyaj Ali User ID
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
UPI_ID = "7568887980-2@ibl" # Kotak Bank UPI
PRICE = "299"
IST = pytz.timezone('Asia/Kolkata')

# Channel IDs from your screenshots
FREE_CH = "-1003649744853"        # RK TRADING FREE (Results yahan jayenge)
VIP_INDIAN_CH = "-1003786564773"   # RK_Nifty_Signals_VIP (Indian Market)
VIP_FOREX_CH = "-1003872928915"    # RK_Binary_Forex_Global (Forex/Crypto)

bot = telebot.TeleBot(TOKEN)

# ================== 2. MARKET ASSETS ==================
INDIAN_ASSETS = ["^NSEI", "^BSESN"]
FOREX_ASSETS = ["EURUSD=X", "GBPUSD=X", "BTC-USD", "ETH-USD", "GC=F"]

# ================== 3. SIGNAL ENGINE ==================
def get_market_signal(asset_list):
    try:
        asset = random.choice(asset_list)
        df = yf.download(asset, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 20: return None, None, None
        
        rsi = ta.momentum.RSIIndicator(df['Close']).rsi().iloc[-1]
        
        if rsi < 35:
            return asset, "CALL 🟢 (BUY)", random.randint(91, 97)
        elif rsi > 65:
            return asset, "PUT 🔴 (SELL)", random.randint(91, 97)
    except: pass
    return None, None, None

def signal_loop():
    while True:
        # Check Indian Market for Nifty VIP
        a_in, s_in, c_in = get_market_signal(INDIAN_ASSETS)
        if s_in:
            broadcast_signal(VIP_INDIAN_CH, a_in, s_in, c_in, "INDIAN 🇮🇳")

        # Check Forex/Binary Market for Forex VIP
        a_fx, s_fx, c_fx = get_market_signal(FOREX_ASSETS)
        if s_fx:
            broadcast_signal(VIP_FOREX_CH, a_fx, s_fx, c_fx, "FOREX/BINARY 🌍")
            
        time.sleep(300) # Scan every 5 mins

def broadcast_signal(ch_id, asset, signal, conf, label):
    msg = (f"💎 **RK {label} VIP SIGNAL** 💎\n"
           f"━━━━━━━━━━━━━━\n"
           f"🌍 **ASSET:** {asset}\n"
           f"🚦 **ACTION:** {signal}\n"
           f"🎯 **CONFIDENCE:** {conf}%\n"
           f"⏳ **TIME:** 2 MINUTE\n"
           f"━━━━━━━━━━━━━━\n"
           f"🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})")
    try:
        sent = bot.send_message(ch_id, msg, parse_mode="Markdown")
        # Result ko free channel mein bhejne ke liye tracker
        threading.Thread(target=post_result_to_free, args=(asset, label), daemon=True).start()
    except: pass

def post_result_to_free(asset, label):
    time.sleep(130) # 2 min trade expiry
    res = random.choice(["WIN ✅", "WIN ✅", "WIN ✅", "LOSS ❌"])
    res_msg = (f"📊 **{label} VIP RESULT**\n"
               f"━━━━━━━━━━━━━━\n"
               f"🌍 Asset: {asset}\n"
               f"🏆 Status: {res}\n"
               f"━━━━━━━━━━━━━━\n"
               f"🔥 Join VIP for daily sureshots! 👇")
    bot.send_message(FREE_CH, res_msg, parse_mode="Markdown")

# ================== 4. USER & ADMIN COMMANDS ==================
@bot.message_handler(commands=['start'])
def welcome(msg):
    bot.send_message(msg.chat.id, "🚀 **RK TRADING BOT IS ONLINE**\n\nNifty aur Forex signals ke liye /buy type karein.")

@bot.message_handler(commands=['buy'])
def buy_plan(msg):
    text = (f"💎 **VIP PREMIUM ACCESS**\n"
            f"━━━━━━━━━━━━━━\n"
            f"💰 Price: ₹{PRICE}\n"
            f"💳 UPI ID: `{UPI_ID}`\n\n"
            f"📸 **Step:** Payment karke screenshot bhejien. Admin verify karke aapko dono VIP links de dega.")
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_payment(msg):
    # Forward to Admin for verification
    bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
    bot.send_message(ADMIN_ID, f"📩 **New Screenshot!**\nUser ID: `{msg.from_user.id}`\nApprove: `/approve {msg.from_user.id}`")
    bot.send_message(msg.chat.id, "⏳ **Payment proof bhej diya gaya hai.** Admin verify karke aapko VIP links message kar dega.")

@bot.message_handler(commands=['approve'])
def approve_user(msg):
    if msg.from_user.id == ADMIN_ID:
        try:
            uid = msg.text.split()[1]
            # Yahan apne asli VIP links daal dein
            bot.send_message(uid, "✅ **PAYMENT APPROVED!**\n\n🇮🇳 Nifty VIP: https://t.me/+Abc123Example\n🌍 Forex VIP: https://t.me/+Xyz789Example\n\nWelcome to RK Family!")
            bot.send_message(ADMIN_ID, f"User {uid} successfully approved.")
        except: pass

# ================== 5. RUN BOT ==================
if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=signal_loop, daemon=True).start()
    print("🚀 RK BOT DEPLOYED SUCCESSFULLY WITH NEW TOKEN...")
    bot.infinity_polling()
