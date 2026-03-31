import yfinance as yf
import pandas as pd

import telebot
import time
import threading
import random
import os

TOKEN = os.getenv("BOT_TOKEN", "8626210155:AAH914jJYsADPAU4ZuLK3gdaZiW611TAj5o")


# 📢 Channel username
CHANNEL_ID = "@rkniftysignals"

bot = telebot.TeleBot(TOKEN)

def get_data():
    data = yf.download("^NSEI", period="1d", interval="5m")
    return data

def get_data():
    try:
        data = yf.download("^NSEI", period="1d", interval="5m")
        return data
    except:
        return None

def generate_signal():
    df = get_data()
    
    if df is None or df.empty:
        return "⚠️ Data not available"

    try:
        df['EMA9'] = df['Close'].ewm(span=9).mean()
        df['EMA21'] = df['Close'].ewm(span=21).mean()
        
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        last = df.iloc[-1]
        
        if last['EMA9'] > last['EMA21'] and last['RSI'] < 70:
            return "BUY NIFTY 🔥"
        elif last['EMA9'] < last['EMA21'] and last['RSI'] > 30:
            return "SELL NIFTY ⚠️"
        else:
            return "NO TRADE ❌"
    except:
        return "⚠️ Calculation Error"
    df = get_data()
    
    df['EMA9'] = df['Close'].ewm(span=9).mean()
    df['EMA21'] = df['Close'].ewm(span=21).mean()
    
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    last = df.iloc[-1]
    
    if last['EMA9'] > last['EMA21'] and last['RSI'] < 70:
        return "BUY NIFTY 🔥"
    elif last['EMA9'] < last['EMA21'] and last['RSI'] > 30:
        return "SELL NIFTY ⚠️"
    else:
        return "NO TRADE ❌"

# 🔁 Auto Signal Function
def auto_signal():
    while True:
        print("Generated Signal:", signal)
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
