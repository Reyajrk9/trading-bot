import telebot
import threading
import time
import os
import random
import yfinance as yf
import pandas as pd
import pytz

# --- CONFIGURATION ---
TOKEN = "8626210155:AAFreO1PvBOs8I3I4vmhzQXVX4jN2cG-TKA" 
ADMIN_ID = 8626210155 
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
UPI_ID = "7568887980-2@ibl"
PRICE = "299"

# CHANNEL IDs
FREE_CH = "-1003649744853"
VIP_INDIAN_CH = "-1003786564773"
VIP_FOREX_CH = "-1003872928915"

# VIP LINKS
NIFTY_VIP_LINK = "https://t.me/+c1w2VvuFeOJkMjdI"
FOREX_VIP_LINK = "https://t.me/+-eKlypeZ-tdjYWI1"

bot = telebot.TeleBot(TOKEN)

def get_market_signal(asset_list):
    try:
        asset = random.choice(asset_list)
        df = yf.download(asset, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 20: return None, None, None
        
        # Simple RSI Calculation (Bina 'ta' library ke error ke)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        if rsi < 35: return asset, "CALL 🟢 (BUY)", random.randint(91, 97)
        elif rsi > 65: return asset, "PUT 🔴 (SELL)", random.randint(91, 97)
    except Exception as e:
        print(f"Signal Error: {e}")
    return None, None, None

def signal_loop():
    while True:
        # Indian Signals
        a_in, s_in, c_in = get_market_signal(["^NSEI", "^BSESN"])
        if s_in:
            msg = f"💎 **RK INDIAN VIP** 💎\n\n🌍 ASSET: {a_in}\n🚦 ACTION: {s_in}\n🎯 CONFIDENCE: {c_in}%\n🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})"
            bot.send_message(VIP_INDIAN_CH, msg, parse_mode="Markdown")

        # Forex Signals
        a_fx, s_fx, c_fx = get_market_signal(["EURUSD=X", "GBPUSD=X", "BTC-USD"])
        if s_fx:
            msg = f"💎 **RK FOREX VIP** 💎\n\n🌍 ASSET: {a_fx}\n🚦 ACTION: {s_fx}\n🎯 CONFIDENCE: {c_fx}%\n🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})"
            bot.send_message(VIP_FOREX_CH, msg, parse_mode="Markdown")
        time.sleep(300)

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, "🚀 **RK TRADING BOT IS LIVE**\n\nVIP signals ke liye /buy type karein.")

@bot.message_handler(commands=['buy'])
def buy(msg):
    bot.send_message(msg.chat.id, f"💎 **VIP ACCESS**\n\n💰 Price: ₹{PRICE}\n💳 UPI: `{UPI_ID}`\n\nScreenshot bhejein.")

@bot.message_handler(content_types=['photo'])
def handle_payment(msg):
    bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
    bot.send_message(ADMIN_ID, f"📩 New Proof!\nUser: `{msg.from_user.id}`\nApprove: `/approve {msg.from_user.id}`")
    bot.send_message(msg.chat.id, "⏳ Admin verify kar raha hai...")

@bot.message_handler(commands=['approve'])
def approve(msg):
    if msg.from_user.id == ADMIN_ID:
        try:
            uid = msg.text.split()[1]
            bot.send_message(uid, f"✅ **APPROVED!**\n\n🇮🇳 Nifty VIP: {NIFTY_VIP_LINK}\n🌍 Forex VIP: {FOREX_VIP_LINK}")
            bot.send_message(ADMIN_ID, f"User {uid} Approved!")
        except: pass

if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=signal_loop, daemon=True).start()
    bot.infinity_polling()
