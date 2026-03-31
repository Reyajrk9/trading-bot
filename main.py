import yfinance as yf
import telebot
import os
import time
import threading
import pandas as pd # Pandas add kiya logic fix ke liye

# Variables setup
TOKEN = os.getenv("BOT_TOKEN", "8626210155:AAH914jJYsADPAU4ZuLK3gdaZiW611TAj5o")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@rkniftysignals")

bot = telebot.TeleBot(TOKEN)

def get_data(symbol):
    try:
        # 5m interval ke liye period kam se kam 1 ya 5 din hona chahiye
        data = yf.download(symbol, period="5d", interval="5m", progress=False)
        return data
    except Exception as e:
        print(f"Data Fetch Error: {e}")
        return None

def generate_signal(symbol, name):
    df = get_data(symbol)

    if df is None or df.empty or len(df) < 25: # Ensure enough data for EMA/RSI
        return f"📊 {name}: ⚠️ Data Not Available"

    try:
        close = df['Close']
        
        # EMA Calculations
        ema9 = close.ewm(span=9).mean()
        ema21 = close.ewm(span=21).mean()

        # RSI Calculation
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # FIX: .item() use kiya taaki Ambiguous Series error na aaye
        last_price = float(close.iloc[-1].item())
        last_ema9 = float(ema9.iloc[-1].item())
        last_ema21 = float(ema21.iloc[-1].item())
        last_rsi = float(rsi.iloc[-1].item())

        # 🎯 Strategy Logic
        if last_ema9 > last_ema21 and last_rsi < 70:
            return f"📊 **{name} SIGNAL**\n\nAction: BUY 🔥\nEntry: {last_price:.2f}\nSL: {last_price-50:.2f}\nTarget: {last_price+100:.2f}\nRSI: {last_rsi:.2f}"

        elif last_ema9 < last_ema21 and last_rsi > 30:
            return f"📊 **{name} SIGNAL**\n\nAction: SELL 📉\nEntry: {last_price:.2f}\nSL: {last_price+50:.2f}\nTarget: {last_price-100:.2f}\nRSI: {last_rsi:.2f}"

        else:
            return f"📊 {name}: NO TRADE ❌ (RSI: {last_rsi:.2f})"

    except Exception as e:
        print(f"Logic Error for {name}: {e}")
        return f"📊 {name}: ⚠️ System Busy"

@bot.message_handler(commands=['signal'])
def manual_signal(message):
    bot.send_chat_action(message.chat.id, 'typing')
    nifty = generate_signal("^NSEI", "NIFTY")
    banknifty = generate_signal("^NSEBANK", "BANKNIFTY")
    bot.send_message(message.chat.id, f"{nifty}\n\n{banknifty}", parse_mode="Markdown")

def auto_signal_loop():
    while True:
        try:
            # Market hours check (Optional: 9:15 AM to 3:30 PM)
            nifty = generate_signal("^NSEI", "NIFTY")
            banknifty = generate_signal("^NSEBANK", "BANKNIFTY")
            
            # Sirf tabhi message bheje jab signal "NO TRADE" na ho (Optional)
            bot.send_message(CHANNEL_ID, f"{nifty}\n\n{banknifty}", parse_mode="Markdown")
            print("Auto-Signal sent successfully")
        except Exception as e:
            print(f"Loop Error: {e}")
        
        time.sleep(300) # 5 Minutes

if __name__ == "__main__":
    print("🚀 RK Trading Bot is Online...")
    threading.Thread(target=auto_signal_loop, daemon=True).start()
    bot.infinity_polling()
