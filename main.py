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
GLOBAL_CH = os.getenv('CHANNEL_ID_GLOBAL') 
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
# Apni ID yahan daalein taaki /call command kaam kare
ADMIN_ID = 6363026338 

bot = telebot.TeleBot(TOKEN)
last_signal_times = {}

def get_market_data(symbol, tf='1m'):
    try:
        period = '1d' if tf == '1m' else '5d'
        df = yf.download(tickers=symbol, period=period, interval=tf, progress=False, auto_adjust=True)
        if df is None or df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return None

def get_rk_strategy(symbol):
    df_1m = get_market_data(symbol, '1m')
    df_5m = get_market_data(symbol, '5m')
    
    if df_1m is None or df_5m is None or len(df_1m) < 30: return None, None, None
    
    # 5-Min Trend (Master Filter)
    ema_5m = ta.ema(df_5m['Close'], length=20).iloc[-1]
    price_now = df_1m['Close'].iloc[-1]
    trend = "BULLISH 🚀" if price_now > ema_5m else "BEARISH 📉"
    
    # 1-Min Indicators
    rsi = ta.rsi(df_1m['Close'], length=14).iloc[-1]
    
    sig = None
    reason = ""
    
    # CALL Logic: Trend UP + RSI low (Oversold)
    if rsi < 35 and price_now > ema_5m:
        sig = "CALL 📈 (BUY)"
        reason = "Market is Oversold + Strong Bullish Trend"
    # PUT Logic: Trend DOWN + RSI high (Overbought)
    elif rsi > 65 and price_now < ema_5m:
        sig = "PUT 📉 (SELL)"
        reason = "Market is Overbought + Strong Bearish Trend"
        
    return sig, round(price_now, 5), reason

@bot.message_handler(commands=['call', 'put'])
def manual_signal(message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    try:
        args = message.text.split()
        symbol = args[1].upper() if len(args) > 1 else "VIP ASSET"
        sig_type = "CALL 📈 (BUY)" if "call" in message.text.lower() else "PUT 📉 (SELL)"
        msg = (
            f"👑 **RK ADMIN SPECIAL SIGNAL** 👑\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💹 **ASSET:** {symbol}\n"
            f"🚦 **ACTION:** {sig_type}\n"
            f"⏳ **TIME:** 2 MINUTE\n"
            f"🎯 **CONFIDENCE:** 100% SURESHOT\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👉 [TRADE ON QUOTEX]({QUOTEX_LINK})\n\n"
            f"**DONT MISS! BIG MOVE COMING!** 🔥⚡"
        )
        bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown')
    except: bot.reply_to(message, "Usage: /call SYMBOL")

def check_and_post_result(symbol, chat_id, entry_p, sig_t, msg_id):
    time.sleep(125) 
    df = get_market_data(symbol, '1m')
    if df is not None:
        cp = float(df.iloc[-1]['Close'])
        win = (cp > entry_p if "CALL" in sig_t else cp < entry_p)
        if win:
            res = f"🎆 **#RK_SURESHOT_WINNER** 🎆\n━━━━━━━━━━━━━━━━━━━━\n💰 **RESULT:** DIRECT ITM ✅\n💎 **PROFIT:** SUCCESS\n🚀 **NEXT:** [JOIN VIP NOW]({QUOTEX_LINK})\n━━━━━━━━━━━━━━━━━━━━\n**HISTORY CREATED BY RK!** 💸👑"
        else:
            res = "⚠️ **VOLATILE!** 1-Step MTG (Same direction, 2 min). Recovery signal is 100%!"
        bot.send_message(chat_id, res, reply_to_message_id=msg_id, parse_mode='Markdown')

def engine():
    global last_signal_times
    # Adding major assets for constant flow
    assets = [("EURUSD=X", "FOREX"), ("BTC-USD", "CRYPTO"), ("GBPUSD=X", "FOREX")]
    
    while True:
        for sym, label in assets:
            if time.time() - last_signal_times.get(sym, 0) < 600: continue
            
            sig, price, reason = get_rk_strategy(sym)
            if sig:
                last_signal_times[sym] = time.time()
                msg = (
                    f"💎 **RK PREMIUM ALERT: {label}** 💎\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💹 **ASSET:** {sym}\n"
                    f"🚦 **ACTION:** {sig}\n"
                    f"🎯 **ENTRY:** {price}\n"
                    f"⏳ **TIME:** 2 MINUTE\n"
                    f"📝 **REASON:** {reason}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})\n\n"
                    f"**REACTIONS = NEXT SIGNAL!** ❤️🔥"
                )
                sent = bot.send_message(GLOBAL_CH, msg, parse_mode='Markdown', disable_web_page_preview=True)
                threading.Thread(target=check_and_post_result, args=(sym, GLOBAL_CH, price, sig, sent.message_id)).start()
        time.sleep(40)

if __name__ == "__main__":
    print("🚀 RK Institutional Bot V3 Active...")
    threading.Thread(target=engine).start()
    bot.infinity_polling()
