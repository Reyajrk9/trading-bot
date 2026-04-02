import telebot
import os
import time
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import threading
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL') 
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
ADMIN_ID = 6363026338 # Apni ID yahan confirm kar lein

bot = telebot.TeleBot(TOKEN)
last_signal_times = {}
session_active = False

# --- [MARKET ANALYSIS ENGINE] ---
def get_data(symbol, tf='1m'):
    try:
        period = '1d' if tf == '1m' else '5d'
        df = yf.download(tickers=symbol, period=period, interval=tf, progress=False, auto_adjust=True)
        if df is None or df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return None

def get_signal_logic(symbol):
    df_1m = get_data(symbol, '1m')
    df_5m = get_data(symbol, '5m')
    if df_1m is None or df_5m is None or len(df_1m) < 30: return None, None, None
    
    # 5m Trend Filter (Institutional Style)
    ema_5m = ta.ema(df_5m['Close'], length=20).iloc[-1]
    price_now = df_1m['Close'].iloc[-1]
    trend = "UP 🚀" if price_now > ema_5m else "DOWN 📉"
    
    # 1m RSI Logic
    rsi = ta.rsi(df_1m['Close'], length=14).iloc[-1]
    
    sig, reason = None, ""
    if rsi < 32 and price_now > ema_5m:
        sig, reason = "CALL 📈 (BUY)", "Oversold + Bullish Trend"
    elif rsi > 68 and price_now < ema_5m:
        sig, reason = "PUT 📉 (SELL)", "Overbought + Bearish Trend"
        
    return sig, round(price_now, 5), reason

# --- [ADMIN COMMANDS FOR HYPE] ---
@bot.message_handler(commands=['sessionstart', 'prealert', 'call', 'put'])
def admin_commands(message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    global session_active
    cmd = message.text.split()[0]
    
    if cmd == '/prealert':
        msg = f"🔥 **RK FAMILY ATTENTION** 🔥\n━━━━━━━━━━━━━━━━━━━━\nPublic Session Start Soon! ⏰\nAaj ki session me loss recovery + strong setups milenge.\nJoin Now 👇\n{QUOTEX_LINK}"
    elif cmd == '/sessionstart':
        session_active = True
        msg = "🚀 **SESSION START!** 🚀\n━━━━━━━━━━━━━━━━━━━━\nRK Bot is now scanning for 100% Sureshot setups. Stay Active!"
    elif cmd in ['/call', '/put']:
        symbol = message.text.split()[1].upper() if len(message.text.split()) > 1 else "VIP ASSET"
        sig_type = "CALL 📈 (BUY)" if cmd == '/call' else "PUT 📉 (SELL)"
        msg = f"💎 **RK ADMIN SPECIAL** 💎\n━━━━━━━━━━━━━━━━━━━━\n💹 ASSET: {symbol}\n🚦 ACTION: {sig_type}\n⏳ TIME: 2 MINUTE\n🎯 CONFIDENCE: 100%\n━━━━━━━━━━━━━━━━━━━━\n👉 [TRADE ON QUOTEX]({QUOTEX_LINK})"
    
    bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown', disable_web_page_preview=True)

# --- [RESULT TRACKING] ---
def check_result(symbol, chat_id, entry_p, sig_t, msg_id):
    time.sleep(125)
    df = get_data(symbol, '1m')
    if df is not None:
        cp = float(df.iloc[-1]['Close'])
        win = (cp > entry_p if "CALL" in sig_t else cp < entry_p)
        if win:
            res = f"🎆 **#RK_SURESHOT_WIN** 🎆\n━━━━━━━━━━━━━━━━━━━━\n✅ RESULT: DIRECT ITM\n💰 STATUS: 100% SUCCESS\n🚀 NEXT: [JOIN VIP]({QUOTEX_LINK})\n━━━━━━━━━━━━━━━━━━━━\n**SHARE YOUR REACTIONS!** ❤️🔥"
        else:
            res = "⚠️ **VOLATILE!** 1-Step MTG (Same direction, 2 min). Recovery signal is coming!"
        bot.send_message(chat_id, res, reply_to_message_id=msg_id, parse_mode='Markdown')

# --- [AUTOMATION ENGINE] ---
def auto_engine():
    global last_signal_times, session_active
    assets = [("EURUSD=X", "FOREX PREMIUM"), ("BTC-USD", "CRYPTO MASTER")]
    while True:
        if session_active:
            for sym, label in assets:
                if time.time() - last_signal_times.get(sym, 0) < 900: continue
                sig, price, reason = get_signal_logic(sym)
                if sig:
                    last_signal_times[sym] = time.time()
                    msg = (f"💎 **RK PREMIUM: {label}** 💎\n━━━━━━━━━━━━━━━━━━━━\n🚦 ACTION: {sig}\n🎯 ENTRY: {price}\n⏳ TIME: 2 MINUTE\n📝 REASON: {reason}\n━━━━━━━━━━━━━━━━━━━━\n🚀 [TRADE NOW]({QUOTEX_LINK})\n\n**REACTIONS FAST!** 👇🔥")
                    sent = bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown', disable_web_page_preview=True)
                    threading.Thread(target=check_result, args=(sym, GLOBAL_CH, price, sig, sent.message_id)).start()
        time.sleep(45)

if __name__ == "__main__":
    print("🚀 RK Legendary Bot Active...")
    threading.Thread(target=auto_engine).start()
    bot.infinity_polling()
