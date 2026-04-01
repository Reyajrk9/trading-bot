import telebot
import os
import time
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import threading
import pytz
from datetime import datetime

TOKEN = os.getenv('BOT_TOKEN')
INDIAN_CH = os.getenv('CHANNEL_ID_INDIAN')
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL')
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"

bot = telebot.TeleBot(TOKEN)
last_signal_times = {"EURUSD=X": 0, "^NSEI": 0}

def get_market_analysis(symbol):
    try:
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 15: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        return df.dropna()
    except Exception as e:
        print(f"Fetch Error: {e}")
        return None

def check_result_and_post(symbol, chat_id, entry_price, signal_type, signal_msg_id):
    time.sleep(125) # 2 Min Trade Time
    df = get_market_analysis(symbol)
    if df is not None:
        current_price = float(df.iloc[-1]['Close'])
        is_win = (current_price > entry_price if "CALL" in signal_type else current_price < entry_price)
        
        if is_win:
            text = (
                f"🎉 **#ROCKET_SURESHOT_WIN** 🎉\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ **RESULT:** SHUDDH PROFIT (ITM)\n"
                f"💰 **STATUS:** 100% SUCCESS\n"
                f"🚀 **NEXT SIGNAL?** JOIN VIP FAST\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 [TRADE ON QUOTEX]({QUOTEX_LINK})"
            )
        else:
            text = "❌ **MARKET VOLATILE!** OTM. Recovery signal coming soon..."
        
        bot.send_message(chat_id, text, reply_to_message_id=signal_msg_id, parse_mode='Markdown')

def send_signals():
    global last_signal_times
    # Testing symbols: EURUSD=X (Forex), BTC-USD (Crypto - Best for 24/7 test)
    targets = [("EURUSD=X", GLOBAL_CH, "FOREX GLOBAL"), ("BTC-USD", GLOBAL_CH, "CRYPTO SPECIAL")]
    
    for symbol, chat_id, label in targets:
        if not chat_id: continue
        if time.time() - last_signal_times.get(symbol, 0) < 600: continue # 10 min gap

        df = get_market_analysis(symbol)
        if df is not None:
            price, rsi = df.iloc[-1]['Close'], df.iloc[-1]['RSI']
            sig_type = None
            
            # FASTER STRATEGY (RSI 35/65)
            if rsi < 35: sig_type = "CALL 📈 (BUY)"
            elif rsi > 65: sig_type = "PUT 📉 (SELL)"
            
            if sig_type:
                last_signal_times[symbol] = time.time()
                msg = (
                    f"🔥 **AJAY TRADER STYLE: {label}** 🔥\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🚦 **ACTION:** {sig_type}\n"
                    f"🎯 **ENTRY:** {round(price, 5)}\n"
                    f"⏳ **TIME:** 2 MINUTE\n"
                    f"🌟 **SURESHOT:** 99.9% ACCURACY\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"👉 [OPEN QUOTEX & TRADE]({QUOTEX_LINK})\n\n"
                    f"**LETS GO GUYS! SHARE REACTIONS!** ❤️🔥"
                )
                sent = bot.send_message(chat_id, msg, parse_mode='Markdown', disable_web_page_preview=True)
                threading.Thread(target=check_result_and_post, args=(symbol, chat_id, price, sig_type, sent.message_id)).start()

if __name__ == "__main__":
    print("🚀 RK Ajay-Trader Style Bot Live...")
    while True:
        try:
            send_signals()
            time.sleep(30)
        except Exception as e:
            time.sleep(20)
