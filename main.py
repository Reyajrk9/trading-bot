import os
import telebot

TOKEN = os.getenv('BOT_TOKEN')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔥 Welcome to Trading Signal Bot!")

@bot.message_handler(func=lambda message: True)
def signal(message):
    bot.reply_to(message, "📊 Signal: BUY NIFTY 🔥")

bot.polling()
