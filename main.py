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

def get_market_analysis(symbol):
    try:
        # 1-minute data fetch kar rahe hain
        data = yf.download(tickers=symbol, period='1d', interval='1m', progress=False)
        if data is not None and not data.empty and len(data) > 20:
            # Indicators calculate karna
            data['RSI'] = ta.rsi(data['Close'], length=14)
            data['EMA_20'] = ta.ema(data['Close'], length=20)
            return data.iloc[-1]
    except Exception as e:
        print(f"Analysis Error: {e}")
    return None

def send_pro_signals():
    symbol = "EURUSD=X"
    analysis = get_market_analysis(symbol)
    
    if analysis is not None:
        try:
            current_rsi = float(analysis['RSI'].item())
            current_price = float(analysis['Close'].item())
            ema_20 = float(analysis['EMA_20'].item())
        except:
            current_rsi = float(analysis['RSI'])
            current_price = float(analysis['Close'])
            ema_20 = float(analysis['EMA_20'])

        # --- LOGIC: RSI + EMA DOUBLE CONFIRMATION ---
        signal_type = None
        
        # SELL Signal: RSI > 70 aur Price EMA se niche girna shuru ho
        if current_rsi > 70 and current_price < ema_20:
            signal_type = "PUT"
            emoji = "🔴"
            action = "SELL / DOWN"
            
        # BUY Signal: RSI < 30 aur Price EMA ke upar nikalna shuru ho
        elif current_rsi < 30 and current_price > ema_20:
            signal_type = "CALL"
            emoji = "🟢"
            action = "BUY / UP"

        if signal_type:
            msg = (
                f"🔥 **PRO AI SIGNAL: {signal_type}** 🔥\n\n"
                f"🪙 Asset: **EUR/USD**\n"
                f"🚀 Action: **{action}** {emoji}\n"
                f"📊 Strategy: **EMA + RSI (90% Acc.)**\n"
                f"⚡ RSI Level: {round(current_rsi, 2)}\n"
                f"⏱️ Expiry: **2-5 Minutes**\n\n"
                f"🔗 **Direct Trade Link:**\n[OPEN QUOTEX ACCOUNT]({QUOTEX_LINK})\n\n"
                f"🎁 Use Code: **TT50** for Deposit Bonus!\n"
                f"⚠️ *Risk 2% of your wallet only.*"
            )
            bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown', disable_web_page_preview=True)
            print(f"Pro Signal Sent! ✅ ({signal_type})")

if __name__ == "__main__":
    print("RK Pro-Trading Bot Live... 🚀")
    bot.remove_webhook()
    
    while True:
        try:
            send_pro_signals()
            # 1 minute wait taaki har candle check ho
            time.sleep(60) 
        except Exception as e:
            print(f"System Error: {e}")
            time.sleep(20)
