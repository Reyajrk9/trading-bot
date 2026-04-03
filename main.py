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

# --- ENGINE ---
def get_institutional_signal(symbol):
    try:
        # Fixed data fetch to avoid delisted error
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 15: return None, None, None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_200'] = ta.ema(df['Close'], length=200)
        curr = df.iloc[-1]
        price, rsi, ema = float(curr['Close']), float(curr['RSI']), float(curr['EMA_200'])
        
        sig = None
        if price > ema and rsi < 30: sig = "CALL 📈 (BUY)"
        elif price < ema and rsi > 70: sig = "PUT 📉 (SELL)"
        return sig, round(price, 5)
    except: return None, None

# --- TRACKER ---
def result_tracker(symbol, entry_p, sig_t, msg_id):
    time.sleep(125)
    try:
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False)
        if not df.empty:
            cp = float(df['Close'].iloc[-1])
            win = (cp > entry_p if "CALL" in sig_t else cp < entry_p)
            txt = "✅ **RESULT: ITM (WINNER)**" if win else "⚠️ **USE 1-STEP MTG!**"
            bot.send_message(GLOBAL_CH, txt, reply_to_message_id=msg_id)
    except: pass

# --- COMMANDS ---
@bot.message_handler(commands=['sessionstart', 'stop'])
def admin_cmd(message):
    global session_active
    if int(message.from_user.id) != ADMIN_ID: return
    if '/sessionstart' in message.text:
        session_active = True
        bot.send_message(GLOBAL_CH, "🚀 **SESSION LIVE!**")
    elif '/stop' in message.text:
        session_active = False
        bot.send_message(GLOBAL_CH, "🛑 **SESSION ENDED.**")

def main_engine():
    global last_signal_times, session_active
    while True:
        if session_active:
            assets = [("EURUSD=X", "EUR/USD"), ("BTC-USD", "BITCOIN"), ("GC=F", "GOLD")]
            for sym, label in assets:
                if time.time() - last_signal_times.get(sym, 0) < 600: continue
                sig, price = get_institutional_signal(sym)
                if sig:
                    last_signal_times[sym] = time.time()
                    msg = f"💎 **RK SIGNAL** 💎\n━━━━━━━━━━━━━━\n🌍 **ASSET:** {label}\n🚦 **ACTION:** {sig}\n🎯 **ENTRY:** {price}\n⏳ **TIME:** 2 MIN"
                    sent = bot.send_message(GLOBAL_CH, msg)
                    threading.Thread(target=result_tracker, args=(sym, price, sig, sent.message_id), daemon=True).start()
        time.sleep(120)

if __name__ == "__main__":
    # Clear old webhooks and start
    bot.remove_webhook()
    threading.Thread(target=main_engine, daemon=True).start()
    print("Bot is running...")
    # FIX: Added long polling params to avoid conflict errors
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
