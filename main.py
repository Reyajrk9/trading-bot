import telebot
import time
import threading
import random
import os

# 🔐 TOKEN (Railway env se lega)
TOKEN = os.getenv("TOKEN")

# 📢 Channel username
CHANNEL_ID = "@rkniftysignals"

bot = telebot.TeleBot(TOKEN)

# 🧠 Signal Generator (abhi demo, baad me real banayenge)
def generate_signal():
    return random.choice(["BUY NIFTY 🔥", "SELL NIFTY ⚠️"])

# 🔁 Auto Signal Function
def auto_signal():
    while True:
        signal = generate_signal()
        text = f"📊 Auto Signal: {signal}"
        
        try:
            bot.send_message(CHANNEL_ID, text)
            print("Signal Sent:", text)
        except Exception as e:
            print("Error:", e)
        
        time.sleep(300)  # 5 min delay

# 🤖 Start Command
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🔥 RK Trading Bot Active!")

# 📊 Manual Signal Command
@bot.message_handler(commands=['signal'])
def send_signal(message):
    signal = generate_signal()
    text = f"📊 Manual Signal: {signal}"
    
    bot.send_message(CHANNEL_ID, text)
    bot.reply_to(message, "Signal sent to channel ✅")

# 🚀 Auto Thread Start
threading.Thread(target=auto_signal).start()

# ▶️ Bot Run
bot.polling()
