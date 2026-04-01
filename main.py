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
INDIAN_CH = os.getenv('CHANNEL_ID_INDIAN')
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL')
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"

bot = telebot.TeleBot(TOKEN)

def get_market_analysis(symbol):
    try:
        # 1-minute interval data for fast signals
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 20: 
            return None
        
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)
        
        # Technical Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df = df.dropna()
        return df if not df.empty else None
    except Exception as e:
        print(f"❌ Data Fetch Error ({symbol}): {e}")
        return None

def check_result_and_post(symbol, chat_id, entry_price, signal_type, signal_msg_id):
    # Wait 2 minutes for trade expiry
    time.sleep(120) 
    analysis = get_market_analysis(symbol)
    
    if analysis is not None:
        current_price = float(analysis.iloc[-1]['Close'])
        is_win = False
        
        if "CALL" in signal_type and current_price > entry_price: is_win = True
        elif "PUT" in signal_type and current_price < entry_price: is_win = True
        
        result_emoji = "✅ SUCCESS (ITM) 💰" if is_win else "❌ LOSS (OTM) 📉"
        result_status = "PROFIT" if is_win else "RECOVERY NEEDED"

        result_text = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **TRADE RESULT: {symbol}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏁 **Status:** {result_emoji}\n"
            f"📍 **Entry:** {round(entry_price, 5)}\n"
            f"🔚 **Close:** {round(current_price, 5)}\n"
            f"📢 **Signal:** {result_status}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚀 **Next Signal Joining:** [Click Here]({QUOTEX_LINK})"
        )
        try:
            bot.send_message(chat_id, result_text, reply_to_message_id=signal_msg_id, parse_mode='Markdown')
        except Exception as e:
            print(f"Result Posting Error: {e}")

def send_signals():
    # Symbols list
    targets = [("EURUSD=X", GLOBAL_CH, "FOREX GLOBAL"), ("^NSEI", INDIAN_CH, "NIFTY 50 INDEX")]
    
    for symbol, chat_id, label in targets:
        if not chat_id: continue # Skip if ID is missing in Railway
        
        df = get_market_analysis(symbol)
        if df is not None:
            analysis = df.iloc[-1]
            price = float(analysis['Close'])
            rsi = float(analysis['RSI'])
            
            sig_type = None
            # Professional RSI Strategy
            if rsi < 30: 
                sig_type = "CALL 📈 (BUY)"
            elif rsi > 70: 
                sig_type = "PUT 📉 (SELL)"
            
            if sig_type:
                msg_text = (
                    f"🔔 **RK TRADING ALERT: {label}**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💹 **Asset:** {symbol}\n"
                    f"🚦 **Action:** {sig_type}\n"
                    f"📍 **Entry Price:** {round(price, 5)}\n"
                    f"⏳ **Duration:** 2 MIN\n"
                    f"📊 **Market RSI:** {round(rsi, 2)}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔗 [TRADE ON QUOTEX NOW]({QUOTEX_LINK})\n"
                    f"⚠️ *Wait for the next candle to start!*"
                )
                try:
                    sent_msg = bot.send_message(chat_id, msg_text, parse_mode='Markdown', disable_web_page_preview=True)
                    print(f"✅ {label} Signal Sent at {datetime.now().strftime('%H:%M:%S')}")
                    
                    # Result Thread
                    threading.Thread(target=check_result_and_post, args=(symbol, chat_id, price, sig_type, sent_msg.message_id)).start()
                except Exception as e:
                    print(f"Signal Send Error: {e}")

if __name__ == "__main__":
    print("🚀 RK Result-Tracking Bot is Starting...")
    bot.remove_webhook()
    
    while True:
        try:
            # Check for signals every 60 seconds
            send_signals()
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Main Loop Error: {e}")
            time.sleep(30)
