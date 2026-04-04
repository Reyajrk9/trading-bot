import telebot
import threading
import time
import os
import random
import yfinance as yf
import pandas as pd
import ta
from sklearn.ensemble import RandomForestClassifier
import numpy as np

# ================== 1. DYNAMIC CONFIG (Railway Variables) ==================
# Railway ke dashboard se variables apne aap utha lega
TOKEN = os.environ.get("BOT_TOKEN", "8626210155:AAFreO1PvBOs8I3I4vmhzQXVX4jN2cG-TKA")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 6589410347)) # Updated Admin ID from your SS

# Channel IDs from your Railway Variables
VIP_INDIAN = os.environ.get("CHANNEL_ID_INDIAN", "-1003786564773")
VIP_FOREX = os.environ.get("CHANNEL_ID_GLOBAL", "-1003872928915")
FREE_CH = os.environ.get("RK_TRADING_FREE", "-1003649744853")

QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"
bot = telebot.TeleBot(TOKEN)

# ================== 2. AI-ML ENGINE (Random Forest) ==================
def train_and_predict(df):
    try:
        # Technical Features
        df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        df['Price_Change'] = df['Close'].pct_change()
        df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
        
        df = df.dropna()
        if len(df) < 50: return None, 0

        X = df[['RSI', 'Price_Change']]
        y = df['Target']
        
        # ML Training
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X[:-1], y[:-1])
        
        # Prediction
        last_row = X.tail(1)
        prediction = model.predict(last_row)[0]
        probability = model.predict_proba(last_row).max() * 100
        
        return prediction, probability
    except:
        return None, 0

# ================== 3. SIGNAL LOGIC ==================
def get_ai_signal(asset_list):
    try:
        asset = random.choice(asset_list)
        df = yf.download(asset, period="1d", interval="1m", progress=False)
        
        # FIXED: .iloc[-1] for 1-dimensional data error
        if df is None or df.empty or len(df) < 60: 
            return None, None, 0

        pred, prob = train_and_predict(df)
        rsi = ta.momentum.RSIIndicator(df['Close']).rsi().iloc[-1]
        
        signal = None
        # Logic: AI + RSI Confirmation
        if pred == 1 and rsi < 48:
            signal = "CALL 🟢 (AI BUY)"
        elif pred == 0 and rsi > 52:
            signal = "PUT 🔴 (AI SELL)"
            
        return asset, signal, round(prob, 2)
    except:
        return None, None, 0

def signal_loop():
    while True:
        try:
            # Market Scanning
            markets = [ (["^NSEI", "^BSESN"], VIP_INDIAN), (["EURUSD=X", "BTC-USD"], VIP_FOREX) ]
            
            for assets, ch_id in markets:
                a, s, p = get_ai_signal(assets)
                if s and p > 85: # 85% Accuracy Filter
                    msg = (f"🤖 **RK AI-ML PREDICTION** 🤖\n\n"
                           f"🌍 Asset: {a}\n🚦 Action: {s}\n🎯 AI Confidence: {p}%\n"
                           f"⚡ Method: Random Forest AI\n\n"
                           f"🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})")
                    bot.send_message(ch_id, msg, parse_mode="Markdown")
            
            time.sleep(300)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(30)

# ================== 4. START BOT ==================
if __name__ == "__main__":
    bot.remove_webhook()
    print("AI-ML Master Bot Starting...")
    threading.Thread(target=signal_loop, daemon=True).start()
    bot.infinity_polling()
