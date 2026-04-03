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

# --- FIXED ANALYSIS ENGINE (Fixes: 57241.jpg) ---
def get_institutional_signal(symbol):
    try:
        # Ticker method is more stable for Crypto/Forex
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='1d', interval='1m')
        
        # Backup if first method fails
        if df is None or df.empty or len(df) < 20:
            df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False, auto_adjust=True)
            
        if df is None or df.empty or len(df) < 20: 
            return None, None, None
            
        # Multi-index columns fix
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)

        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_200'] = ta.ema(df['Close'], length=200)
        
        curr = df.iloc[-1]
        price = float(curr['Close'])
        rsi = float(curr['RSI'])
        ema = float(curr['EMA_200'])
        
        sig, reason = None, ""
        # Strategy: Buy on Dip in Uptrend / Sell on Peak in Downtrend
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
    return (now.weekday() < 5) and (9, 15) <= (now.hour, now.minute) <= (15, 30)

# --- RESULT TRACKER (WIN/LOSS) ---
def result_tracker(symbol, entry_p, sig_t, msg_id):
    time.sleep(125) # Wait for 2-min candle close
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='1d', interval='1m')
        if df is not None and not df.empty:
            cp = float(df['Close'].iloc[-1])
            win = (cp > entry_p if "CALL" in sig_t else cp < entry_p)
            
            if win:
                bot.send_message(GLOBAL_CH, "🎆 **#RK_SURESHOT_WINNER** 🎆\n━━━━━━━━━━━━━━\n✅ RESULT: ITM (SUCCESS)\n💰 STATUS: PROFIT CONFIRMED", reply_to_message_id=msg_id)
            else:
                mtg_msg = f"⚠️ **MARKET REVERSED!**\n━━━━━━━━━━━━━━\nDirection was: {sig_t}\nUse **1-STEP MTG** (Double Amount) for 2 MINUTE now! 💸"
                bot.send_message(GLOBAL_CH, mtg_msg, reply_to_message_id=msg_id)
    except: pass

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['prealert', 'sessionstart', 'stop'])
def admin_cmd(message):
    global session_active
    if int(message.from_user.id) != ADMIN_ID: return
        
    if '/prealert' in message.text:
        bot.send_message(GLOBAL_CH, f"🔥 **RK PREMIUM SESSION LOADING** 🔥\n━━━━━━━━━━━━━━\nAnalyze: High Accuracy Institutional Signals.\n👉 [JOIN NOW]({QUOTEX_LINK})")
    
    elif '/sessionstart' in message.text:
        session_active = True
        bot.send_message(GLOBAL_CH, "🚀 **SESSION LIVE! SCANNING MARKETS...** 🚀\nMonitoring: Forex, Crypto, Gold, Nifty.")
        
    elif '/stop' in message.text:
        session_active = False
        bot.send_message(GLOBAL_CH, "🛑 **SESSION ENDED.**\nSignals Stopped. See you next session! ❤️")

# --- MAIN LOOP (ALL ASSETS) ---
def main_engine():
    global last_signal_times, session_active
    while True:
        if session_active:
            assets = [
                ("EURUSD=X", "EUR/USD"), ("GBPUSD=X", "GBP/USD"), ("USDJPY=X", "USD/JPY"),
                ("BTC-USD", "BITCOIN"), ("ETH-USD", "ETHEREUM"), ("SOL-USD", "SOLANA"),
                ("GC=F", "GOLD (XAU/USD)"), ("^NSEI", "NIFTY 50")
            ]
            
            for sym, label in assets:
                # 10 minute gap per pair
                if time.time() - last_signal_times.get(sym, 0) < 600: continue
                if sym == "^NSEI" and not is_indian_market_open(): continue

                sig, price, reason = get_institutional_signal(sym)
                if sig:
                    last_signal_times[sym] = time.time()
                    bot.send_message(GLOBAL_CH, f"⏳ **RK ANALYZING {label}...** Ready?")
                    time.sleep(5)
                    
                    msg = (f"💎 **RK PREMIUM SIGNAL** 💎\n━━━━━━━━━━━━━━\n"
                           f"🌍 **ASSET:** {label}\n🚦 **ACTION:** {sig}\n"
                           f"🎯 **ENTRY:** {price}\n⏳ **TIME:** 2 MINUTE\n"
                           f"━━━━━━━━━━━━━━\n🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})")
                    
                    try:
                        sent = bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown', disable_web_page_preview=True)
                        t = threading.Thread(target=result_tracker, args=(sym, price, sig, sent.message_id))
                        t.daemon = True
                        t.start()
                    except: pass
        
        # 180s delay for Yahoo Finance safety
        time.sleep(180)

if __name__ == "__main__":
    print("🚀 RK ALL-IN-ONE BOT STARTED...")
    bot.remove_webhook()
    time.sleep(1)
    
    engine_thread = threading.Thread(target=main_engine)
    engine_thread.daemon = True
    engine_thread.start()
    
    bot.infinity_polling()
