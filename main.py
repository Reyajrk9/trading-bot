import telebot
import os
import time
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import threading
import random
from datetime import datetime
import pytz

# --- CONFIGURATION ---
# Railway environment variables se connect kiya gaya hai
TOKEN = os.getenv('BOT_TOKEN')
GLOBAL_CH = int(os.getenv('CHANNEL_ID_GLOBAL', '-1003872928915')) 
ADMIN_ID = int(os.getenv('ADMIN_ID', '6589410347')) 
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
IST = pytz.timezone('Asia/Kolkata')

bot = telebot.TeleBot(TOKEN)
last_signal_times = {}
session_active = False

# --- USER ENGAGEMENT POSTS ---
# Ye messages bot khud beech-beech mein bhejega group active rakhne ke liye
ENGAGEMENT_POSTS = [
    "🔥 Market is looking volatile today! Stay disciplined. 📉",
    "💎 Patience is the key to trading success. RK Signals loading...",
    "🚀 Ready for the next sureshot? Keep your Quotex tab open! 👉 [JOIN NOW](" + QUOTEX_LINK + ")",
    "📊 Institutional players are active. We are scanning for the best entry."
]

# --- CORE ANALYSIS ENGINE ---
def get_advanced_signal(symbol):
    try:
        # Fetching 1-minute interval data for fast signals
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 20: 
            return None, None, None, None
            
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)

        # Technical Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_20'] = ta.ema(df['Close'], length=20) # Faster EMA for more signals
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14) # For dynamic SL/TP
        
        curr = df.iloc[-1]
        price = float(curr['Close'])
        rsi = float(curr['RSI'])
        ema20 = float(curr['EMA_20'])
        atr = float(curr['ATR'])
        
        sig = None
        # Advanced Logic: Trend + RSI Overbought/Oversold
        if price > ema20 and rsi < 40: 
            sig = "CALL 📈 (BUY)"
        elif price < ema20 and rsi > 60: 
            sig = "PUT 📉 (SELL)"
            
        if sig:
            # Calculating SL and TP based on market volatility (ATR)
            sl = price - (atr * 1.5) if "CALL" in sig else price + (atr * 1.5)
            tp = price + (atr * 2) if "CALL" in sig else price - (atr * 2)
            return sig, round(price, 5), round(sl, 5), round(tp, 5)
            
        return None, None, None, None
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None, None, None, None

# --- RESULT TRACKER & EXIT ALERTS ---
def result_tracker(symbol, entry_p, sig_t, msg_id):
    time.sleep(125) # Waiting for 2-minute expiry
    try:
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False)
        if not df.empty:
            cp = float(df['Close'].iloc[-1])
            win = (cp > entry_p if "CALL" in sig_t else cp < entry_p)
            
            if win:
                bot.send_message(GLOBAL_CH, f"💰 **PROFIT BOOKED!** 💰\n━━━━━━━━━━━━━━\n✅ Exit Price: {round(cp, 5)}\n🔥 Status: Sureshot WIN", reply_to_message_id=msg_id)
            else:
                bot.send_message(GLOBAL_CH, "⚠️ **EXIT / MTG ALERT**\n━━━━━━━━━━━━━━\nPrice hit SL. Use 1-Step MTG for 2 min!", reply_to_message_id=msg_id)
    except: 
        pass

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['sessionstart', 'stop', 'prealert'])
def admin_cmd(message):
    global session_active
    if int(message.from_user.id) != ADMIN_ID: 
        return
        
    if '/sessionstart' in message.text:
        session_active = True
        bot.send_message(GLOBAL_CH, "🚀 **ADVANCE SESSION LIVE!**\nScanning Forex, Crypto & Commodities...")
    elif '/stop' in message.text:
        session_active = False
        bot.send_message(GLOBAL_CH, "🛑 **SESSION ENDED.**")
    elif '/prealert' in message.text:
        bot.send_message(GLOBAL_CH, f"🔥 **RK SESSION LOADING** 🔥\nGet your accounts ready! 👉 [JOIN]({QUOTEX_LINK})")

# --- BACKGROUND PROCESSES ---
def auto_engage():
    """Posts random engagement messages every 30-60 minutes."""
    while True:
        if session_active:
            time.sleep(random.randint(1800, 3600))
            bot.send_message(GLOBAL_CH, random.choice(ENGAGEMENT_POSTS), parse_mode='Markdown')
        time.sleep(600)

def main_engine():
    global last_signal_times, session_active
    # Start auto-engagement thread
    threading.Thread(target=auto_engage, daemon=True).start()
    
    while True:
        if session_active:
            # Extended asset list for higher signal frequency
            assets = [
                ("EURUSD=X", "EUR/USD"), ("GBPUSD=X", "GBP/USD"), 
                ("BTC-USD", "BITCOIN"), ("ETH-USD", "ETHEREUM"),
                ("GC=F", "GOLD"), ("AUDUSD=X", "AUD/USD")
            ]
            
            for sym, label in assets:
                # 5-minute gap between signals for the same asset
                if time.time() - last_signal_times.get(sym, 0) < 300: 
                    continue 
                
                sig, price, sl, tp = get_advanced_signal(sym)
                if sig:
                    last_signal_times[sym] = time.time()
                    # Pre-alert for engagement
                    bot.send_message(GLOBAL_CH, f"⏳ **RK ANALYZING {label}...** Ready your amount!")
                    time.sleep(3)
                    
                    msg = (f"💎 **RK ADVANCE SIGNAL** 💎\n━━━━━━━━━━━━━━\n"
                           f"🌍 **ASSET:** {label}\n🚦 **ACTION:** {sig}\n"
                           f"🎯 **ENTRY:** {price}\n"
                           f"🛑 **SL:** {sl} | ✅ **TP:** {tp}\n"
                           f"⏳ **TIME:** 2 MINUTE\n━━━━━━━━━━━━━━")
                    sent = bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown', disable_web_page_preview=True)
                    
                    # Start result tracking thread
                    threading.Thread(target=result_tracker, args=(sym, price, sig, sent.message_id), daemon=True).start()
        
        time.sleep(60) # Scan every minute for new opportunities

if __name__ == "__main__":
    bot.remove_webhook()
    # Start main scanning engine
    threading.Thread(target=main_engine, daemon=True).start()
    print("Bot is starting...")
    # Infinity polling with long timeout to avoid Railway conflict errors
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
