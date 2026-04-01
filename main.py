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

# Aapka Permanent Quotex Link
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"

def get_market_data(symbol):
    try:
        data = yf.download(tickers=symbol, period='1d', interval='1m', progress=False)
        if not data.empty and len(data) > 14:
            data['RSI'] = ta.rsi(data['Close'], length=14)
            return data.iloc[-1]
    except:
        return None
    return None

def send_automated_signals():
    # 1. Global/Binary Analysis (EUR/USD)
    global_data = get_market_data("EURUSD=X")
    if global_data is not None:
        rsi = global_data['RSI']
        if rsi > 70 or rsi < 30:
            action = "🔴 PUT / SELL" if rsi > 70 else "🟢 CALL / BUY"
            emoji = "📉" if rsi > 70 else "📈"
            
            msg = (
                f"📊 **AI BINARY SIGNAL** {emoji}\n\n"
                f"🪙 Asset: **EUR/USD**\n"
                f"🚀 Action: **{action}**\n"
                f"⚡ RSI Level: {round(rsi, 2)}\n"
                f"⏱️ Timeframe: 1-5 Min\n\n"
                f"🔗 **Trade Here:** [Open Quotex]({QUOTEX_LINK})\n"
                f"🎁 Use Code: **TT50** for 50% Bonus!"
            )
            bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown', disable_web_page_preview=True)
            print("Global Signal Sent! ✅")

    # 2. Compounding & Promo (Har 30 min mein ek baar - Optional)
    # Isko aap interval ke hisaab se customize kar sakte hain.

if __name__ == "__main__":
    print("RK Ultimate Automation Bot Starting... 🚀")
    bot.remove_webhook() # Conflict Error (409) rokne ke liye
    
    while True:
        try:
            # Har 1 minute mein market scan karega
            send_automated_signals()
            time.sleep(60) 
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(20)
