import telebot
import os
import time
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import threading
from datetime import datetime
import pytz

# --- CONFIGURATION (RAILWAY VARIABLES) ---
TOKEN = os.getenv('BOT_TOKEN')
GLOBAL_CH = int(os.getenv('CHANNEL_ID_GLOBAL', '-1003872928915')) 
ADMIN_ID = int(os.getenv('ADMIN_ID', '6589410347')) 
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
IST = pytz.timezone('Asia/Kolkata')

bot = telebot.TeleBot(TOKEN)
last_signal_times = {}
session_active = False

# --- ANALYSIS ENGINE ---
def get_institutional_signal(symbol):
    try:
        # 1m interval for Binary/Scalping
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 50: 
            return None, None, None
            
        # Multi-index columns fix for new yfinance versions
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)

        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_200'] = ta.ema(df['Close'], length=200)
        
        curr = df.iloc[-1]
        price = float(curr['Close'])
        rsi = float(curr['RSI'])
        ema = float(curr['EMA_200'])
        
        sig, reason = None, ""
        # Institutional Strategy: Trend + Momentum
        if price > ema and rsi < 30:
            sig, reason = "CALL 📈 (BUY)", "Institutional Dip"
        elif price < ema and rsi > 70:
            sig, reason = "PUT 📉 (SELL)", "Institutional Peak"
            
        return sig, round(price, 5), reason
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None, None, None

def is_indian_market_open():
    now = datetime.now(IST)
    # Monday-Friday, 9:15 AM to 3:30 PM
    return (now.weekday() < 5) and (9, 15) <= (now.hour, now.minute) <= (15, 30)

# --- RESULT TRACKER (WIN/LOSS) ---
def result_tracker(symbol, entry_p, sig_t, msg_id):
    # Wait 2 minutes + 5 sec buffer for candle close
    time.sleep(125)
    try:
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False)
        if df is not None and not df.empty:
            cp = float(df['Close'].iloc[-1])
            win = (cp > entry_p if "CALL" in sig_t else cp < entry_p)
            
            if win:
                bot.send_message(GLOBAL_CH, "🎆 **#RK_SURESHOT_WINNER** 🎆\n━━━━━━━━━━━━━━\n✅ RESULT: ITM (SHUDDH PROFIT)\n💰 STATUS: 100% SUCCESS", reply_to_message_id=msg_id)
            else:
                mtg_msg = f"⚠️ **MARKET VOLATILE!**\n━━━━━━━━━━━━━━\nDirection was: {sig_t}\nUse **1-STEP MTG** (Double Amount) for 2 MINUTE now! 💸"
                bot.send_message(GLOBAL_CH, mtg_msg, reply_to_message_id=msg_id)
    except Exception as e:
        print(f"Tracker Error: {e}")

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['prealert', 'sessionstart', 'stop'])
def admin_cmd(message):
    global session_active
    if int(message.from_user.id) != ADMIN_ID: 
        return
        
    if '/prealert' in message.text:
        bot.send_message(GLOBAL_CH, f"🔥
