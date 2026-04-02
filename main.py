import telebot
import os
import time
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import threading
from datetime import datetime
import pytz

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
# Variable agar missing ho toh ye default IDs lega
GLOBAL_CH = int(os.getenv('CHANNEL_ID_GLOBAL', '-1003872928915')) 
ADMIN_ID = int(os.getenv('ADMIN_ID', '6589410347')) 

QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
IST = pytz.timezone('Asia/Kolkata')

bot = telebot.TeleBot(TOKEN)
last_signal_times = {}
session_active = False
daily_stats = {"wins": 0, "losses": 0}

# --- [CORE ANALYSIS] ---
def get_institutional_signal(symbol):
    try:
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 50: return None, None, None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_200'] = ta.ema(df['Close'], length=200)
        
        curr = df.iloc[-1]
        price, rsi, ema = curr['Close'], curr['RSI'], curr['EMA_200']
        
        sig, reason = None, ""
        if price > ema and rsi < 30:
            sig, reason = "CALL 📈 (BUY)", "RK Institutional Dip"
        elif price < ema and rsi > 70:
            sig, reason = "PUT 📉 (SELL)", "RK Institutional Peak"
            
        return sig, round(price, 5), reason
    except: return None, None, None

def is_indian_market_open():
    now = datetime.now(IST)
    return (now.weekday() < 5) and (9, 15) <= (now.hour, now.minute) <= (15, 30)

# --- [SURESHOT TRACKER] ---
def result_tracker(symbol, entry_p, sig_t, msg_id):
    time.sleep(125)
    try:
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False)
        if df is not None:
            cp = float(df['Close'].iloc[-1])
            win = (cp > entry_p if "CALL" in sig_t else cp < entry_p)
            global daily_stats
            if win:
                daily_stats["wins"] += 1
                bot.send_message(GLOBAL_CH, "🎆 **#RK_SURESHOT_WINNER** 🎆\n━━━━━━━━━━━━━━\n✅ RESULT: ITM\n💰 STATUS: 100% SUCCESS", reply_to_message_id=msg_id)
            else:
                daily_stats["losses"] += 1
                bot.send_message(GLOBAL_CH, f"⚠️ **USE 1-STEP MTG!**\nDirection: {sig_t}", reply_to_message_id=msg_id)
    except: pass

# --- [ADMIN COMMANDS] ---
@bot.message_handler(commands=['prealert', 'sessionstart'])
def admin_cmd(message):
    if int(message.from_user.id) != ADMIN_ID: return
    if '/prealert' in message.text:
        bot.send_message(GLOBAL_CH, f"🔥 **RK SESSION LOADING** 🔥\n👉 [JOIN NOW]({QUOTEX_LINK})")
    elif '/sessionstart' in message.text:
        global session_active
        session_active = True
        bot.send_message(GLOBAL_CH, "🚀 **SESSION LIVE!** 🚀")

# --- [MAIN LOOP] ---
def main_engine():
    global last_signal_times, session_active
    while True:
        if session_active:
            assets = [("^NSEI", "NIFTY-50")] if is_indian_market_open() else []
            assets += [("EURUSD=X", "FOREX GLOBAL"), ("BTC-USD", "CRYPTO SPECIAL")]
            for sym, label in assets:
                if time.time() - last_signal_times.get(sym, 0) < 600: continue
                sig, price, reason = get_institutional_signal(sym)
                if sig:
                    last_signal_times[sym] = time.time()
                    bot.send_message(GLOBAL_CH, f"⏳ **ANALYZING {label}...** Stay Ready!")
                    time.sleep(5)
                    msg = (f"💎 **RK PREMIUM ALERT: {label}** 💎\n🚦 ACTION: {sig}\n🎯 ENTRY: {price}\n⏳ TIME: 2 MINUTE")
                    sent = bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown', disable_web_page_preview=True)
                    threading.Thread(target=result_tracker, args=(sym, price, sig, sent.message_id)).start()
        time.sleep(40)

if __name__ == "__main__":
    print("🚀 Bot starting...")
    # FIX: Conflict error aur TypeError dono ko ek saath khatam karne ke liye simple polling
    threading.Thread(target=main_engine).start()
    bot.infinity_polling() # 'skip_pending_updates' hata diya gaya hai error ki wajah se
