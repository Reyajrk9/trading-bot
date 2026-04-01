import telebot
import os
import time
import yfinance as yf
import pandas_ta as ta

# Railway Variables
TOKEN = os.getenv('BOT_TOKEN')
INDIAN_CH = os.getenv('CHANNEL_ID_INDIAN')
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL')

bot = telebot.TeleBot(TOKEN)
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"

def get_market_data(symbol):
    try:
        data = yf.download(tickers=symbol, period='1d', interval='1m', progress=False)
        if data is not None and not data.empty and len(data) > 14:
            data['RSI'] = ta.rsi(data['Close'], length=14)
            return data.iloc[-1]
    except Exception as e:
        print(f"Data Fetch Error: {e}")
    return None

def send_automated_signals():
    global_data = get_market_data("EURUSD=X")
    if global_data is not None:
        # Fixed: .item() handles the 'Series' to float conversion
        try:
            current_rsi = float(global_data['RSI'].item())
        except:
            current_rsi = float(global_data['RSI'])
        
        if current_rsi > 70 or current_rsi < 30:
            action = "🔴 PUT / SELL" if current_rsi > 70 else "🟢 CALL / BUY"
            emoji = "📉" if current_rsi > 70 else "📈"
            
            msg = (
                f"📊 **AI BINARY SIGNAL** {emoji}\n\n"
                f"🪙 Asset: **EUR/USD**\n"
                f"🚀 Action: **{action}**\n"
                f"⚡ RSI Level: {round(current_rsi, 2)}\n"
                f"⏱️ Timeframe: 1-5 Min\n\n"
                f"🔗 **Trade Here:** [Open Quotex]({QUOTEX_LINK})\n"
                f"🎁 Use Code: **TT50** for 50% Bonus!"
            )
            bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown', disable_web_page_preview=True)
            print(f"Signal Sent! ✅")

if __name__ == "__main__":
    print("RK Ultimate Automation Bot Starting... 🚀")
    bot.remove_webhook()
    
    while True:
        try:
            send_automated_signals()
            time.sleep(60) 
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(20)
