import telebot
import time
import threading
import random

TOKEN = "8626210155:AAH914jJYsADPAU4ZuLK3gdaZiW611TAj5o"
CHANNEL_ID = "@rkniftysignals"

bot = telebot.TeleBot(TOKEN)

def auto_signal():
    while True:
        signal = random.choice(["BUY NIFTY 🔥", "SELL NIFTY ⚠️"])
        text = f"📊 Auto Signal: {signal}"
        
        bot.send_message(CHANNEL_ID, text)
        time.sleep(300)  # 5 min

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🔥 RK Auto Trading Bot Active!")

threading.Thread(target=auto_signal).start()

bot.polling()
