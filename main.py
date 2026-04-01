import telebot
import os
import time
import yfinance as yf
import pandas_ta as ta
import pandas as pd

TOKEN = os.getenv('BOT_TOKEN')
INDIAN_CH = os.getenv('CHANNEL_ID_INDIAN')
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL')

bot = telebot.TeleBot(TOKEN)
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"

def get_market_analysis(symbol):
    try:
        # 1. Fetching data with auto_adjust to avoid NoneType errors
        df = yf.download(tickers=symbol, period='1d', interval='1m', progress=False, auto_adjust=True)
        
        if df is None or df.empty or len(df) < 25:
            return None

        # 2. Fix for Multi-Index Columns (YFinance New Update)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 3. Calculating Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        
        # Drop NaN values to ensure float conversion works
        df = df.dropna()
        
        if not df.empty:
            return df.iloc[-1]
    except Exception as e:
        print(f"Fetch Error ({symbol}): {e}")
    return None

def send_signals():
    # symbols check
    targets = [("EURUSD=X", GLOBAL_CH, "GLOBAL BINARY"), ("^NSEI", INDIAN_CH, "NIFTY 50")]
    
    for symbol, chat_id, label in targets:
        analysis = get_market_analysis(symbol)
        if analysis is not None:
            try:
                price = float(analysis['Close'])
                rsi = float(analysis['RSI'])
                ema = float(analysis['EMA_20'])
                
                # Logic Double Confirmation
                sig_type = None
                if rsi < 30 and price > ema:
                    sig_type = "CALL 📈"
                elif rsi > 70 and price < ema:
                    sig_type = "PUT 📉"
                
                if sig_type:
                    msg = f"🚀 **{label} SIGNAL**\n\nAction: **{sig_type}**\nPrice: {round(price, 4)}\nRSI: {round(rsi, 2)}\n\n[Trade on Quotex]({QUOTEX_LINK})"
                    bot.send_message(chat_id, msg, parse_mode='Markdown')
                    print(f"{label} Signal Sent! ✅")
            except Exception as e:
                print(f"Logic Error: {e}")

if __name__ == "__main__":
    print("RK Ultimate Combined Bot Live... 🚀")
    bot.remove_webhook()
    while True:
        try:
            send_signals()
            time.sleep(60)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(20)
