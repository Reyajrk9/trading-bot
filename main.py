import telebot
import os
import time
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import threading
import pytz  # ALAG SE IMPORT KIYA HAI
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
INDIAN_CH = os.getenv('CHANNEL_ID_INDIAN')
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL')
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"

bot = telebot.TeleBot(TOKEN)

# Last signal time tracker to avoid spam
last_signal_times = {"EURUSD=X": 0, "^NSEI": 0}

def is_indian_market_open():
    try:
        tz = pytz.timezone('Asia/Kolkata')
        now = datetime.now(tz)
        # Monday to Friday, 9:15 AM to 3:30 PM
        if now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30):
            return True
        return False
    except:
        return False

def get_market_analysis(symbol):
    try:
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df = df.dropna()
        return df if not df.empty else None
    except Exception as e:
        print(f"❌ Fetch Error ({symbol}): {e}")
        return None

def check_result_and_post(symbol, chat_id, entry_price, signal_type, signal_msg_id):
    time.sleep(125) 
    analysis = get_market_analysis(symbol)
    
    if analysis is not None:
        current_price = float(analysis.iloc[-1]['Close'])
        is_win = False
        
        if "CALL" in signal_type and current_price > entry_price: is_win = True
        elif "PUT" in signal_type and current_price < entry_price: is_win = True
        
        result_emoji = "✅ SUCCESS (ITM) 💰" if is_win else "❌ LOSS (OTM) 📉"
        
        result_text = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **TRADE RESULT: {symbol}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏁 Status: **{result_emoji}**\n"
            f"📍 Entry: {round(entry_price, 5)}\n"
            f"🔚 Close: {round(current_price, 5)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 **Next signal?** [Join VIP Now]({QUOTEX_LINK})"
        )
        try:
            bot.send_message(chat_id, result_text, reply_to_message_id=signal_msg_id, parse_mode='Markdown')
        except Exception as e:
            print(f"Result Error: {e}")

def send_signals():
    global last_signal_times
    targets = [("EURUSD=X", GLOBAL_CH, "FOREX GLOBAL"), ("^NSEI", INDIAN_CH, "NIFTY 50")]
    
    for symbol, chat_id, label in targets:
        if not chat_id or chat_id == "None": continue
        
        if symbol == "^NSEI" and not is_indian_market_open():
            continue

        # 5 minute gap
        if time.time() - last_signal_times[symbol] < 300:
            continue

        df = get_market_analysis(symbol)
        if df is not None:
            analysis = df.iloc[-1]
            price = float(analysis['Close'])
            rsi = float(analysis['RSI'])
            
            sig_type = None
            if rsi < 28: sig_type = "CALL 📈 (BUY)"
            elif rsi > 72: sig_type = "PUT 📉 (SELL)"
            
            if sig_type:
                last_signal_times[symbol] = time.time()
                msg_text = (
                    f"🔔 **RK TRADING ALERT: {label}**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💹 **Asset:** {symbol}\n"
                    f"🚦 **Action:** {sig_type}\n"
                    f"📍 **Entry Price:** {round(price, 5)}\n"
                    f"⏳ **Duration:** 2 MIN\n"
                    f"📊 **Market RSI:** {round(rsi, 2)}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔗 [TRADE ON QUOTEX]({QUOTEX_LINK})\n"
                    f"⚠️ *Wait for current candle close!*"
                )
                try:
                    sent_msg = bot.send_message(chat_id, msg_text, parse_mode='Markdown', disable_web_page_preview=True)
                    threading.Thread(target=check_result_and_post, args=(symbol, chat_id, price, sig_type, sent_msg.message_id)).start()
                except Exception as e:
                    print(f"Send Error: {e}")

if __name__ == "__main__":
    print("🚀 RK Professional Trading Bot Active...")
    bot.remove_webhook()
    while True:
        try:
            send_signals()
            time.sleep(30)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(20)
