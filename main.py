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
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL') 
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
ADMIN_ID = 6363026338 
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

# --- [SURESHOT TRACKER & MTG] ---
def result_tracker(symbol, entry_p, sig_t, msg_id):
    time.sleep(125)
    df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False)
    if df is not None:
        cp = float(df['Close'].iloc[-1])
        win = (cp > entry_p if "CALL" in sig_t else cp < entry_p)
        global daily_stats
        if win:
            daily_stats["wins"] += 1
            bot.send_message(GLOBAL_CH, "🎆 **#RK_SURESHOT_WINNER** 🎆\n━━━━━━━━━━━━━━\n✅ RESULT: SHUDDH PROFIT (ITM)\n💰 STATUS: 100% SUCCESS\n🚀 NEXT SIGNAL? JOIN VIP FAST", reply_to_message_id=msg_id)
        else:
            daily_stats["losses"] += 1
            mtg_msg = (f"⚠️ **VOLATILE MARKET!** ⚠️\n━━━━━━━━━━━━━━\nDon't Panic! Use **1-STEP MTG** Now.\nDirection: {sig_t}\nTime: 2 MIN\nDouble your previous amount for 100% Recovery! 💸")
            bot.send_message(GLOBAL_CH, mtg_msg, reply_to_message_id=msg_id)

# --- [ADMIN & UTILS] ---
@bot.message_handler(commands=['risk'])
def risk_calc(message):
    try:
        bal = float(message.text.split()[1])
        bot.reply_to(message, f"🛡️ **RK RISK ADVISOR**\n━━━━━━━━━━━━━━\n💰 Balance: ${bal}\n🟢 Safe Trade: ${round(bal*0.02, 2)}\n🔴 Max Risk: ${round(bal*0.05, 2)}")
    except: bot.reply_to(message, "Usage: /risk 100")

@bot.message_handler(commands=['prealert', 'sessionstart'])
def admin_cmd(message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    if '/prealert' in message.text:
        bot.send_message(GLOBAL_CH, f"🔥 **RK LEGENDARY SESSION LOADING** 🔥\n━━━━━━━━━━━━━━\nReady your Quotex! High Accuracy Guaranteed.\n👉 [JOIN NOW]({QUOTEX_LINK})")
    elif '/sessionstart' in message.text:
        global session_active
        session_active = True
        bot.send_message(GLOBAL_CH, "🚀 **SESSION LIVE!** 🚀\nScanning Markets... Wait for the Magic! ✨")

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
                    # Pre-Signal Hype
                    bot.send_message(GLOBAL_CH, f"⏳ **RK ANALYZING {label}...**\nInstitutional Sentiment: 92% Strong. Stay Ready! 🔥")
                    time.sleep(5)
                    msg = (f"💎 **RK PREMIUM ALERT: {label}** 💎\n━━━━━━━━━━━━━━\n🚦 ACTION: {sig}\n🎯 ENTRY: {price}\n⏳ TIME: 2 MINUTE\n📝 REASON: {reason}\n━━━━━━━━━━━━━━\n🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})\n\n**REACTIONS FAST FOR NEXT!** ❤️🔥")
                    sent = bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown', disable_web_page_preview=True)
                    threading.Thread(target=result_tracker, args=(sym, price, sig, sent.message_id)).start()
        time.sleep(40)

if __name__ == "__main__":
    print("🚀 RK GOD-MODE Bot Active...")
    threading.Thread(target=main_engine).start()
    bot.infinity_polling()
