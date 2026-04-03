import telebot
import os
import time
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import threading
from datetime import datetime
import pytz

# --- CONFIG ---
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
        # Fetching data using yfinance
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False, auto_adjust=True)
        
        if df is None or df.empty or len(df) < 15:
            return None, None, None
            
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)

        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_200'] = ta.ema(df['Close'], length=200)
        
        curr = df.iloc[-1]
        price = float(curr['Close'])
        rsi = float(curr['RSI'])
        ema = float(curr['EMA_200'])
        
        sig, reason = None, ""
        if price > ema and rsi < 30:
            sig, reason = "CALL 📈 (BUY)", "Institutional Dip"
        elif price < ema and rsi > 70:
            sig, reason = "PUT 📉 (SELL)", "Institutional Peak"
            
        return sig, round(price, 5), reason
    except:
        return None, None, None

def is_indian_market_open():
    now = datetime.now(IST)
    return (now.weekday() < 5) and (9, 15) <= (now.hour, now.minute) <= (15, 30)

# --- RESULT TRACKER ---
def result_tracker(symbol, entry_p, sig_t, msg_id):
    time.sleep(125)
    try:
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False)
        if not df.empty:
            cp = float(df['Close'].iloc[-1])
            win = (cp > entry_p if "CALL" in sig_t else cp < entry_p)
            if win:
                bot.send_message(GLOBAL_CH, "✅ **RESULT: ITM (WINNER)**", reply_to_message_id=msg_id)
            else:
                bot.send_message(GLOBAL_CH, "⚠️ **USE 1-STEP MTG!**", reply_to_message_id=msg_id)
    except: pass

# --- COMMANDS ---
@bot.message_handler(commands=['prealert', 'sessionstart', 'stop'])
def admin_cmd(message):
    global session_active
    if int(message.from_user.id) != ADMIN_ID: return
    if '/prealert' in message.text:
        bot.send_message(GLOBAL_CH, f"🔥 **RK PREMIUM SESSION LOADING** 🔥\n━━━━━━━━━━━━━━\n👉 [JOIN NOW]({QUOTEX_LINK})")
    elif '/sessionstart' in message.text:
        session_active = True
        bot.send_message(GLOBAL_CH, "🚀 **SESSION LIVE! SCANNING MARKETS...**")
    elif '/stop' in message.text:
        session_active = False
        bot.send_message(GLOBAL_CH, "🛑 **SESSION ENDED.**")

def main_engine():
    global last_signal_times, session_active
    while True:
        if session_active:
            assets = [
                ("EURUSD=X", "EUR/USD"), ("GBPUSD=X", "GBP/USD"),
                ("BTC-USD", "BITCOIN"), ("ETH-USD", "ETHEREUM"),
                ("GC=F", "GOLD (XAU/USD)"), ("^NSEI", "NIFTY 50")
            ]
            for sym, label in assets:
                if time.time() - last_signal_times.get(sym, 0) < 600: continue
                if sym == "^NSEI" and not is_indian_market_open(): continue

                sig, price, reason = get_institutional_signal(sym)
                if sig:
                    last_signal_times[sym] = time.time()
                    bot.send_message(GLOBAL_CH, f"⏳ **RK ANALYZING {label}...** Stay Ready!")
                    time.sleep(5)
                    msg = (f"💎 **RK PREMIUM SIGNAL** 💎\n━━━━━━━━━━━━━━\n🌍 **ASSET:** {label}\n🚦 **ACTION:** {sig}\n🎯 **ENTRY:** {price}\n⏳ **TIME:** 2 MINUTE\n━━━━━━━━━━━━━━")
                    sent = bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown', disable_web_page_preview=True)
                    threading.Thread(target=result_tracker, args=(sym, price, sig, sent.message_id), daemon=True).start()
        time.sleep(180)

if __name__ == "__main__":
    bot.remove_webhook()
    # Start the analysis engine in a background thread
    threading.Thread(target=main_engine, daemon=True).start()
    bot.infinity_polling()
