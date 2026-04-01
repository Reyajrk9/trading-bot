import telebot
import os
import time

# Railway se variables uthayega
TOKEN = os.getenv('BOT_TOKEN')
INDIAN_CH = os.getenv('CHANNEL_ID_INDIAN')
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL')

bot = telebot.TeleBot(TOKEN)

def send_news_alert():
    news_msg = (
        "<b>📢 LIVE MARKET NEWS ALERT 📢</b>\n\n"
        "📊 <b>Current Status:</b> High Volatility Detected!\n"
        "⚠️ <b>Warning:</b> Badi news aane wali hai. Apne trades ko trailing SL ke sath secure karein.\n\n"
        "✅ Stay Tuned for Next Update!"
    )
    try:
        bot.send_message(INDIAN_CH, news_msg, parse_mode='HTML')
        print("News Alert Sent! ✅")
    except Exception as e:
        print(f"News Error: {e}")

def send_global_promo():
    msg = (
        "<b>⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️</b>\n"
        "<b>COMPOUNDING SESSION IS FREE</b>\n\n"
        "📍 <b>REGISTRATION LINK</b> 👇\n"
        "https://broker-qx.pro/?lid=2061690\n\n"
        "🎁 <b>BONUS CODE:</b> <b>TT50</b>\n"
        "Contact: <b>@Technical_suport1</b>"
    )
    try:
        bot.send_message(GLOBAL_CH, msg, parse_mode='HTML')
        print("Global Promo Sent! ✅")
    except Exception as e:
        print(f"Global Promo Error: {e}")

if __name__ == "__main__":
    print("RK Multi-Channel Bot Starting... 🚀")
    
    # Conflict khatam karne ke liye purane webhooks hatayein
    bot.remove_webhook()
    time.sleep(1)

    # Bot start hote hi pehle messages bhej dega
    send_news_alert()
    send_global_promo()
    
    while True:
        try:
            # Interval badha diya hai taaki conflict na ho
            bot.polling(none_stop=True, interval=15, timeout=60)
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(20)
