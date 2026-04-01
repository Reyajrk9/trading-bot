import telebot
import os
import time
from datetime import datetime

# Railway Variables se data uthayega
TOKEN = os.getenv('BOT_TOKEN')
INDIAN_CH = os.getenv('CHANNEL_ID_INDIAN')
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL')

bot = telebot.TeleBot(TOKEN)

# --- 1. NEWS ALERT SYSTEM ---
def send_news_alert():
    """Market News Alert bhejta hai"""
    news_msg = (
        "📢 **LIVE MARKET NEWS ALERT** 📢\n\n"
        "📊 **Current Status:** High Volatility Detected!\n"
        "⚠️ **Warning:** Badi news aane wali hai. Apne trades ko trailing SL ke sath secure karein.\n\n"
        "💡 **Expert Tip:** Nifty aur Global markets mein sharp move aa sakta hai. Risk management ka dhyan rakhein.\n\n"
        "✅ Stay Tuned for Next Update!"
    )
    try:
        bot.send_message(INDIAN_CH, news_msg, parse_mode='Markdown')
        print("News Alert Sent to Indian Channel! ✅")
    except Exception as e:
        print(f"News Error: {e}")

# --- 2. PROMOTION SYSTEM (As per your Style) ---
def send_global_promo():
    """Quotex Style Promo"""
    msg = (
        "⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️\n"
        "**COMPOUNDING SESSION IS FREE JUST**\n"
        "**CREATE A NEW ACCOUNT WITH MY**\n"
        "**LINK AND DIPOSIT 100%** 💰\n\n"
        "📢 **WANT TO JOIN 50$ TO 2500$**\n"
        "**COMPOUNDING SESSION** 📈📈\n\n"
        "🚨 **JOIN FAST LIMITED SEATS** 🪑\n\n"
        "📍 **CREATE A NEW ACCOUNT** 👇\n\n"
        "https://broker-qx.pro/?lid=2061690\n" # Tumhara real link
        "https://broker-qx.pro/?lid=2061690\n\n"
        "🎁 **BONUS CODE** 👇 **TT50** 🎁\n\n"
        "📍 **DIPOSIT MINIMUM 50$ AND SEND**\n"
        "**ME TRADER ID** ⚡️🔮\n"
        "@Technical_suport1"
    )
    try:
        bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown')
        print("Global Promo Sent! ✅")
    except Exception as e:
        print(f"Global Promo Error: {e}")

# --- MAIN LOGIC ---
print("RK Multi-Channel Bot is Starting... 🚀")

if __name__ == "__main__":
    # Bot start hote hi turant 1st update bhejega
    send_news_alert()
    send_global_promo()
    
    print("Bot is Live and Monitoring... ⚡")
    
    while True:
        try:
            # Conflict fix: interval=5 aur timeout=30 rakha hai
            bot.polling(none_stop=True, interval=5, timeout=30)
            
            # Har 2 ghante (7200 sec) mein News aur Ads automatic repeat honge
            time.sleep(7200)
            send_news_alert()
            send_global_promo()
            
        except Exception as e:
            # Agar network break ho toh 15 sec wait karke restart karega
            print(f"Restarting due to Error: {e}")
            time.sleep(15)
