import yfinance as yf
import telebot
import os
import time
import threading
from datetime import datetime

# Configuration
TOKEN = os.getenv("BOT_TOKEN", "8626210155:AAH914jJYsADPAU4ZuLK3gdaZiW611TAj5o")
CH_INDIAN = os.getenv("CHANNEL_ID_INDIAN", "@RK_Nifty_Signals_VIP")
CH_GLOBAL = os.getenv("CHANNEL_ID_GLOBAL", "@RK_Binary_Forex_Global")

bot = telebot.TeleBot(TOKEN)

def get_signal(symbol, name, is_binary=False):
    try:
        df = yf.download(symbol, period="1d", interval="5m", progress=False)
        if df.empty: return None
        
        close = df['Close']
        price = float(close.iloc[-1].item())
        ema9 = close.ewm(span=9).mean().iloc[-1]
        ema21 = close.ewm(span=21).mean().iloc[-1]
        
        if ema9 > ema21:
            action = "CALL 🟢" if is_binary else "BUY 🔥"
            return f"📊 **{name} SIGNAL**\n\nAction: {action}\nEntry: {price:.2f}\nSL: {price-40:.2f}\nTarget: {price+80:.2f}"
        elif ema9 < ema21:
            action = "PUT 🔴" if is_binary else "SELL ⚠️"
            return f"📊 **{name} SIGNAL**\n\nAction: {action}\nEntry: {price:.2f}\nSL: {price+40:.2f}\nTarget: {price-80:.2f}"
    except:
        return None
    return None

def auto_loop():
    while True:
        now = datetime.now()
        hr = now.hour
        
        try:
            # Indian Market (Morning/Afternoon)
            if 9 <= hr <= 15:
                for s, n in [("^NSEI", "NIFTY"), ("^NSEBANK", "BANKNIFTY")]:
                    sig = get_signal(s, n)
                    if sig: bot.send_message(CH_INDIAN, sig, parse_mode="Markdown")
            
            # Global/Binary (Evening/Night/Weekend)
            if hr >= 16 or hr < 9 or now.weekday() >= 5:
                for s, n in [("EURUSD=X", "EUR/USD"), ("BTC-USD", "BITCOIN")]:
                    sig = get_signal(s, n, is_binary=True)
                    if sig: bot.send_message(CH_GLOBAL, f"💎 **VIP SESSION**\n\n{sig}", parse_mode="Markdown")
            
            # Promo Messages (Every 2 Hours)
            if now.minute == 0 and hr % 2 == 0:
                bot.send_message(CH_INDIAN, "💰 **Join Paid VIP for 95% Accuracy!**\nMessage: @Admin")
                bot.send_message(CH_GLOBAL, "🎁 **FREE VIP ACCESS**\nRegister: [YOUR_LINK]\nDeposit $50 & Send ID!")

        except Exception as e:
            print(f"Loop Error: {e}")
        
        time.sleep(300) # Check every 5 mins

if __name__ == "__main__":
    print("RK Multi-Channel Bot is Live! 🚀")
    threading.Thread(target=auto_loop, daemon=True).start()
    bot.infinity_polling()
