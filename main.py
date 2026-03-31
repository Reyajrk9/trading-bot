import yfinance as yf
import telebot
import os
import time
import threading

TOKEN = os.getenv("BOT_TOKEN", "APNA_REAL_TOKEN_YAHAN")
CHANNEL_ID = "@rkniftysignals"

bot = telebot.TeleBot(TOKEN)

# 📊 Data Fetch
def get_data(symbol):
    try:
        return yf.download(symbol, period="1d", interval="5m")
    except:
        return None

# 📈 Signal Logic
def generate_signal(symbol, name):
    df = get_data(symbol)

    if df is None or df.empty:
        return f"{name}: ⚠️ Data Not Available"

    try:
        close = df['Close']

        ema9 = close.ewm(span=9).mean()
        ema21 = close.ewm(span=21).mean()

        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        price = close.iloc[-1]
        last_ema9 = ema9.iloc[-1]
        last_ema21 = ema21.iloc[-1]
        last_rsi = rsi.iloc[-1]

        # 🎯 Strategy
        if last_ema9 > last_ema21 and last_rsi < 70:
            entry = round(price, 2)
            sl = round(price - 50, 2)
            target = round(price + 100, 2)
            return f"📊 {name}\nBUY 🔥\nEntry: {entry}\nSL: {sl}\nTarget: {target}"

        elif last_ema9 < last_ema21 and last_rsi > 30:
            entry = round(price, 2)
            sl = round(price + 50, 2)
            target = round(price - 100, 2)
            return f"📊 {name}\nSELL ⚠️\nEntry: {entry}\nSL: {sl}\nTarget: {target}"

        else:
            return f"📊 {name}\nNO TRADE ❌"

    except Exception as e:
        print("Error:", e)
        return f"{name}: ⚠️ Error"

# 🤖 Manual Command
@bot.message_handler(commands=['signal'])
def send_signal(message):
    nifty = generate_signal("^NSEI", "NIFTY")
    banknifty = generate_signal("^NSEBANK", "BANKNIFTY")

    bot.send_message(message.chat.id, nifty + "\n\n" + banknifty)

# 🔥 Auto Signal Loop
def auto_signal_loop():
    while True:
        try:
            nifty = generate_signal("^NSEI", "NIFTY")
            banknifty = generate_signal("^NSEBANK", "BANKNIFTY")

            bot.send_message(CHANNEL_ID, nifty + "\n\n" + banknifty)
            print("Signal sent")

        except Exception as e:
            print("Auto Error:", e)

        time.sleep(300)  # 5 min

# ▶️ Start bot + auto thread
print("Bot Running...")
threading.Thread(target=auto_signal_loop).start()
bot.polling()
