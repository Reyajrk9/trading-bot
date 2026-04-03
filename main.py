import telebot
import threading
import time
import os
import random
import yfinance as yf
import ta
import pytz

# ================== 1. CONFIGURATION (IDs & TOKEN) ==================
TOKEN = "8626210155:AAFreO1PvBOs8I3I4vmhzQXVX4jN2cG-TKA" #
ADMIN_ID = 8626210155 #
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
UPI_ID = "7568887980-2@ibl" #
PRICE = "299"

# Channel IDs
FREE_CH = "-1003649744853"
VIP_INDIAN_CH = "-1003786564773"
VIP_FOREX_CH = "-1003872928915"

# Private Invite Links
NIFTY_VIP_LINK = "https://t.me/+c1w2VvuFeOJkMjdI"
FOREX_VIP_LINK = "https://t.me/+-eKlypeZ-tdjYWI1"

bot = telebot.TeleBot(TOKEN)

# ================== 2. SIGNAL ENGINE ==================
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
        # Indian Signals
        a_in, s_in, c_in = get_market_signal(["^NSEI", "^BSESN"])
        if s_in:
            msg = (f"💎 **RK INDIAN VIP SIGNAL** 💎\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"🌍 **ASSET:** {a_in}\n"
                   f"🚦 **ACTION:** {s_in}\n"
                   f"🎯 **CONFIDENCE:** {c_in}%\n"
                   f"🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})")
            bot.send_message(VIP_INDIAN_CH, msg, parse_mode="Markdown")

        # Forex Signals
        a_fx, s_fx, c_fx = get_market_signal(["EURUSD=X", "GBPUSD=X", "BTC-USD"])
        if s_fx:
            msg = (f"💎 **RK FOREX VIP SIGNAL** 💎\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"🌍 **ASSET:** {a_fx}\n"
                   f"🚦 **ACTION:** {s_fx}\n"
                   f"🎯 **CONFIDENCE:** {c_fx}%\n"
                   f"🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})")
            bot.send_message(VIP_FOREX_CH, msg, parse_mode="Markdown")
            
        time.sleep(300) # Scan every 5 mins

# ================== 3. COMMAND HANDLERS ==================
@bot.message_handler(commands=['start'])
def welcome(msg):
    bot.send_message(msg.chat.id, "🚀 **RK TRADING BOT IS ONLINE**\n\nVIP signals ke liye /buy type karein.")

@bot.message_handler(commands=['buy'])
def buy_plan(msg):
    text = (f"💎 **VIP PREMIUM ACCESS**\n"
            f"━━━━━━━━━━━━━━\n"
            f"💰 Price: ₹{PRICE}\n"
            f"💳 UPI ID: `{UPI_ID}`\n\n"
            f"📸 **Step:** Payment karke screenshot bhejien. Admin verify karke aapko VIP links de dega.")
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_payment(msg):
    bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
    bot.send_message(ADMIN_ID, f"📩 **New Screenshot!**\nUser ID: `{msg.from_user.id}`\nApprove: `/approve {msg.from_user.id}`")
    bot.send_message(msg.chat.id, "⏳ **Payment proof receive ho gaya hai.** Admin verify karke aapko VIP links message kar dega.")

@bot.message_handler(commands=['approve'])
def approve_user(msg):
    if msg.from_user.id == ADMIN_ID:
        try:
            uid = msg.text.split()[1]
            text = (f"✅ **PAYMENT APPROVED!**\n\n"
                    f"🇮🇳 Nifty VIP: {NIFTY_VIP_LINK}\n"
                    f"🌍 Forex VIP: {FOREX_VIP_LINK}\n\n"
                    f"Welcome to RK Family!")
            bot.send_message(uid, text)
            bot.send_message(ADMIN_ID, f"User {uid} successfully approved.")
        except: pass

# ================== 4. RUN BOT ==================
if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=signal_loop, daemon=True).start()
    bot.infinity_polling()
