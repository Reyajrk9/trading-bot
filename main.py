import yfinance as yf
import telebot
import os

# 🔐 Token (Railway env se lega, warna fallback use karega)
TOKEN = os.getenv("BOT_TOKEN", "APNA_REAL_TOKEN_YAHAN")

# 📢 Channel username
CHANNEL_ID = "@rkniftysignals"

bot = telebot.TeleBot(TOKEN)

# 📊 Data Fetch
def get_data():
    try:
        data = yf.download("^NSEI", period="1d", interval="5m")
        return data
    except:
        return None

# 📈 Signal Generator
def generate_signal():
    df = get_data()
    
    if df is None or df.empty:
        return "⚠️ Market Data Not Available"

    try:
        close = df['Close']

        # EMA
        ema9 = close.ewm(span=9).mean()
        ema21 = close.ewm(span=21).mean()

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        last_ema9 = ema9.iloc[-1]
        last_ema21 = ema21.iloc[-1]
        last_rsi = rsi.iloc[-1]

        # 🔥 Strategy
        if last_ema9 > last_ema21 and last_rsi < 70:
            return "BUY NIFTY 🔥"
        elif last_ema9 < last_ema21 and last_rsi > 30:
            return "SELL NIFTY ⚠️"
        else:
            return "NO TRADE ❌"

    except Exception as e:
        print("Error:", e)
        return "⚠️ Calculation Error"

# 🤖 Start Command
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🔥 RK Trading Bot Active!\nSend /signal")

# 📊 Manual Signal
@bot.message_handler(commands=['signal'])
def send_signal(message):
    signal = generate_signal()
    bot.send_message(message.chat.id, f"📊 Manual Signal: {signal}")

# ▶️ Bot Run
print("Bot Running...")
bot.polling()
