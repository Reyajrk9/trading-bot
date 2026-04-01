import telebot
import os
import time
import yfinance as yf
import pandas_ta as ta

# Railway Environment Variables
TOKEN = os.getenv('BOT_TOKEN')
INDIAN_CH = os.getenv('CHANNEL_ID_INDIAN')
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL')

bot = telebot.TeleBot(TOKEN)

# Aapka Business Link
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
PROMO_CODE = "TT50"

def calculate_signals(symbol, is_indian=False):
    try:
        # 1-minute data fetch (Accuracy ke liye 1m best hai)
        data = yf.download(tickers=symbol, period='1d', interval='1m', progress=False)
        if data is None or data.empty or len(data) < 25:
            return None
        
        # Indicators: RSI(14) + EMA(20)
        data['RSI'] = ta.rsi(data['Close'], length=14)
        data['EMA_20'] = ta.ema(data['Close'], length=20)
        
        last_row = data.iloc[-1]
        # Fixed: .item() for Series to Float
        price = float(last_row['Close'].item() if hasattr(last_row['Close'], 'item') else last_row['Close'])
        rsi = float(last_row['RSI'].item() if hasattr(last_row['RSI'], 'item') else last_row['RSI'])
        ema = float(last_row['EMA_20'].item() if hasattr(last_row['EMA_20'], 'item') else last_row['EMA_20'])

        # --- SIGNAL LOGIC (Double Confirmation) ---
        signal = None
        # CALL: RSI < 30 (Oversold) aur Price EMA ke upar (Trend Reversal)
        if rsi < 30 and price > ema:
            sl = price - (price * 0.002) # 0.2% SL
            tp1 = price + (price * 0.004) # 0.4% Target
            signal = {"type": "CALL 📈", "entry": price, "sl": sl, "tp": tp1, "rsi": rsi}
            
        # PUT: RSI > 70 (Overbought) aur Price EMA ke niche (Trend Exhaustion)
        elif rsi > 70 and price < ema:
            sl = price + (price * 0.002)
            tp1 = price - (price * 0.004)
            signal = {"type": "PUT 📉", "entry": price, "sl": sl, "tp": tp1, "rsi": rsi}

        return signal
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

def send_to_telegram():
    # 1. GLOBAL (EUR/USD)
    global_sig = calculate_signals("EURUSD=X")
    if global_sig:
        msg = (
            f"🌍 **GLOBAL BINARY SIGNAL**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 Asset: **EUR/USD**\n"
            f"🚀 Action: **{global_sig['type']}**\n"
            f"💰 Entry: {round(global_sig['entry'], 5)}\n"
            f"🚫 SL: {round(global_sig['sl'], 5)}\n"
            f"🎯 Target: {round(global_sig['tp'], 5)}\n"
            f"⚡ RSI: {round(global_sig['rsi'], 2)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 **Trade Now:** [OPEN QUOTEX]({QUOTEX_LINK})\n"
            f"🎁 Bonus Code: **{PROMO_CODE}** (50% Deposit)"
        )
        bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown', disable_web_page_preview=True)

    # 2. INDIAN (NIFTY 50)
    indian_sig = calculate_signals("^NSEI", is_indian=True)
    if indian_sig:
        msg_in = (
            f"🇮🇳 **INDIAN MARKET ALERT**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Index: **NIFTY 50**\n"
            f"🚀 Signal: **{indian_sig['type']}**\n"
            f"📍 Entry: {round(indian_sig['entry'], 2)}\n"
            f"🛑 SL: {round(indian_sig['sl'], 2)}\n"
            f"✅ Target: {round(indian_sig['tp'], 2)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Trading involves risk. Use proper lot size.*"
        )
        bot.send_message(INDIAN_CH, msg_in, parse_mode='Markdown')

if __name__ == "__main__":
    print("RK Ultimate Combined Bot Live... 🚀")
    bot.remove_webhook() # Conflict fix
    
    while True:
        try:
            send_to_telegram()
            time.sleep(60) # Har minute check karega
        except Exception as e:
            print(f"System Loop Error: {e}")
            time.sleep(20)
