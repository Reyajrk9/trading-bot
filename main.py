import telebot
import os
import time

# Railway se config uthayega
TOKEN = os.getenv('BOT_TOKEN')
INDIAN_CH = os.getenv('CHANNEL_ID_INDIAN')
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL')

bot = telebot.TeleBot(TOKEN)

# --- 1. NEWS ALERT ---
def send_news_alert():
    news_msg = (
        "<b>📢 LIVE MARKET NEWS ALERT 📢</b>\n\n"
        "📊 <b>Current Status:</b> High Volatility Detected!\n"
        "⚠️ <b>Warning:</b> Badi news aane wali hai. Apne trades ko trailing SL ke sath secure karein.\n\n"
        "💡 <b>Expert Tip:</b> Nifty aur Global markets mein sharp move aa sakta hai. Risk management ka dhyan rakhein.\n\n"
        "✅ Stay Tuned for Next Update!"
    )
    try:
        bot.send_message(INDIAN_CH, news_msg, parse_mode='HTML')
        print("News Alert Sent! ✅")
    except Exception as e:
        print(f"News Error: {e}")

# --- 2. PROMOTION ALERT (HTML Mode for No Errors) ---
def send_global_promo():
    msg = (
        "<b>⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️</b>\n"
        "<b>COMPOUNDING SESSION IS FREE JUST</b>\n"
        "<b>CREATE A NEW ACCOUNT WITH MY</b>\n"
        "<b>LINK AND DIPOSIT 100%</b> 💰\n\n"
        "📢 <b>WANT TO JOIN 50$ TO 2500$</b>\n"
        "<b>COMPOUNDING SESSION</b> 📈📈\n\n"
        "🚨 <b>JOIN FAST LIMITED SEATS</b> 🪑\n\n"
        "📍 <b>CREATE A NEW ACCOUNT</b> 👇\n\n"
        "https://broker-qx.pro/?lid=2061690\n"
        "https://broker-qx.pro/?lid=2061690\n\n"
        "🎁 <b>BONUS CODE</b> 👇 <b>TT50</b> 🎁\n\n"
        "📍 <b>DIPOSIT MINIMUM 50$ AND SEND</b>\n"
        "<b>ME TRADER ID</b> ⚡️🔮\n"
        "<b>@Technical_suport1</b>"
    )
    try:
        bot.send_message(GLOBAL_CH, msg, parse_mode='HTML')
        print("Global Promo Sent! ✅")
    except Exception as e:
        print(f"Global Promo Error: {e}")

# --- MAIN LOOP ---
if __name__ == "__main__":
    print("RK Multi-Channel Bot Starting... 🚀")
    
    # Start hote hi pehle updates
    send_news_alert()
    send_global_promo()
    
    while True:
        try:
            # Conflict fix karne ke liye delete_webhook zaruri hai
            bot.delete_webhook()
            bot.polling(none_stop=True, interval=5, timeout=40)
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(15)
