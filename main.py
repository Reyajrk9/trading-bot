import telebot
import os
import time
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from datetime import datetime

TOKEN = os.getenv('BOT_TOKEN')
INDIAN_CH = os.getenv('CHANNEL_ID_INDIAN')
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL')

bot = telebot.TeleBot(TOKEN)
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"

def get_market_analysis(symbol):
    try:
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 25: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df = df.dropna()
        return df if not df.empty else None
    except Exception as e:
        print(f"Fetch Error ({symbol}): {e}")
        return None

def check_result_and_post(symbol, chat_id, entry_price, signal_type, signal_msg_id):
    # 2 minute wait for result
    time.sleep(120) 
    analysis = get_market_analysis(symbol)
    if analysis is not None:
        current_price = float(analysis.iloc[-1]['Close'])
        is_win = False
        
        if "CALL" in signal_type and current_price > entry_price: is_win = True
        elif "PUT" in signal_type and current_price < entry_price: is_win = True
        
        result_emoji = "✅ ITM! SHUDDH PROFIT 💰" if is_win else "❌ OTM! NEXT TIME"
        result_text = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **RESULT FOR {symbol}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏁 Status: **{result_emoji}**\n"
            f"📍 Entry: {round(entry_price, 5)}\n"
            f"🔚 Close: {round(current_price, 5)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚀 **Join for more:** [Click Here]({QUOTEX_LINK})"
        )
        bot.send_message(chat_id, result_text, reply_to_message_id=signal_msg_id, parse_mode='Markdown')

def send_signals():
    targets = [("EURUSD=X", GLOBAL_CH, "GLOBAL BINARY"), ("^NSEI", INDIAN_CH, "NIFTY 50")]
    
    for symbol, chat_id, label in targets:
        df = get_market_analysis(symbol)
        if df is not None:
            analysis = df.iloc[-1]
            price = float(analysis['Close'])
            rsi = float(analysis['RSI'])
            ema = float(analysis['EMA_20'])
            
            sig_type = None
            if rsi < 30 and price > ema: sig_type = "CALL 📈"
            elif rsi > 70 and price < ema: sig_type = "PUT 📉"
            
            if sig_type:
                msg_text = (
                    f"🚀 **{label} SIGNAL**\n\n"
                    f"Action: **{sig_type}**\n"
                    f"Price: {round(price, 5)}\n"
                    f"RSI: {round(rsi, 2)}\n"
                    f"Time: 2 Min\n\n"
                    f"🔗 [Trade on Quotex]({QUOTEX_LINK})"
                )
                sent_msg = bot.send_message(chat_id, msg_text, parse_mode='Markdown', disable_web_page_preview=True)
                print(f"{label} Signal Sent! ✅")
                
                # Result Check function ko background mein chalana
                import threading
                threading.Thread(target=check_result_and_post, args=(symbol, chat_id, price, sig_type, sent_msg.message_id)).start()

if __name__ == "__main__":
    print("RK Result-Tracking Bot Live... 🚀")
    bot.remove_webhook()
    while True:
        try:
            send_signals()
            time.sleep(60)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(20)
