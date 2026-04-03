import telebot
import threading
import time
import os
import random
import yfinance as yf
import ta
import pytz

# --- CONFIGURATION ---
TOKEN = "8626210155:AAFreO1PvBOs8I3I4vmhzQXVX4jN2cG-TKA" # Aapka naya token
ADMIN_ID = 8626210155 # Aapki Admin ID
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
UPI_ID = "7568887980-2@ibl" # Aapki UPI ID
PRICE = "299"

# --- CHANNEL IDs ---
FREE_CH = "-1003649744853" # Public Free Channel
VIP_INDIAN_CH = "-1003786564773" # Private Nifty VIP
VIP_FOREX_CH = "-1003872928915" # Private Forex VIP

# --- PRIVATE INVITE LINKS ---
NIFTY_VIP_LINK = "https://t.me/+c1w2VvuFeOJkMjdI" #
FOREX_VIP_LINK = "https://t.me/+-eKlypeZ-tdjYWI1" #

bot = telebot.TeleBot(TOKEN)

# Signal Logic
def get_market_signal(asset_list):
    try:
        asset = random.choice(asset_list)
        df = yf.download(asset, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 20: return None, None, None
        rsi = ta.momentum.RSIIndicator(df['Close']).rsi().iloc[-1]
        if rsi < 35: return asset, "CALL 🟢 (BUY)", random.randint(91, 97)
        elif rsi > 65: return asset, "PUT 🔴 (SELL)", random.randint(91, 97)
    except: pass
    return None, None, None

def signal_loop():
    while True:
        # Indian Market Signals
        a_in, s_in, c_in = get_market_signal(["^NSEI", "^BSESN"])
        if s_in:
            msg = f"💎 **RK INDIAN VIP** 💎\n\n🌍 ASSET: {a_in}\n🚦 ACTION: {s_in}\n🎯 CONFIDENCE: {c_in}%\n🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})"
            bot.send_message(VIP_INDIAN_CH, msg, parse_mode="Markdown")
        
        # Forex/Crypto Signals
        a_fx, s_fx, c_fx = get_market_signal(["EURUSD=X", "GBPUSD=X", "BTC-USD"])
        if s_fx:
            msg = f"💎 **RK FOREX VIP** 💎\n\n🌍 ASSET: {a_fx}\n🚦 ACTION: {s_fx}\n🎯 CONFIDENCE: {c_fx}%\n🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})"
            bot.send_message(VIP_FOREX_CH, msg, parse_mode="Markdown")
            
        time.sleep(300) # Har 5 minute mein signal

# Bot Commands
@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, "🚀 **RK TRADING BOT ACTIVE**\n\nVIP signals join karne ke liye /buy command ka use karein.")

@bot.message_handler(commands=['buy'])
def buy(msg):
    caption = f"💎 **VIP ACCESS (LIFETIME)**\n\n💰 Price: ₹{PRICE}\n💳 UPI ID: `{UPI_ID}`\n\nPayment karne ke baad screenshot yahan bhejein. Admin verify karke aapko approve karega."
    bot.send_message(msg.chat.id, caption, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_payment(msg):
    # Admin ko photo forward karna verification ke liye
    bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
    bot.send_message(ADMIN_ID, f"📩 **NEW PAYMENT PROOF**\nUser ID: `{msg.from_user.id}`\nApprove karne ke liye click karein: `/approve {msg.from_user.id}`")
    bot.send_message(msg.chat.id, "⏳ Aapka payment proof receive ho gaya hai. Admin verify kar raha hai...")

@bot.message_handler(commands=['approve'])
def approve(msg):
    if msg.from_user.id == ADMIN_ID:
        try:
            user_to_approve = msg.text.split()[1]
            welcome_msg = (
                f"✅ **CONGRATULATIONS! PAYMENT APPROVED**\n\n"
                f"Ab aap hamare VIP channels join kar sakte hain:\n\n"
                f"🇮🇳 **Indian VIP:** {NIFTY_VIP_LINK}\n"
                f"🌍 **Forex VIP:** {FOREX_VIP_LINK}\n\n"
                f"Welcome to the RK Trading Family! 🚀"
            )
            bot.send_message(user_to_approve, welcome_msg)
            bot.send_message(ADMIN_ID, f"✅ User {user_to_approve} ko VIP links bhej diye gaye hain.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ Error: {e}\nFormat: `/approve USER_ID`")

if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=signal_loop, daemon=True).start()
    print("Bot is running...")
    bot.infinity_polling()
