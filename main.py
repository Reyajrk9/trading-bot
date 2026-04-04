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

# ================== 1. CONFIGURATION ==================
TOKEN = os.environ.get("BOT_TOKEN")
VIP_INDIAN = os.environ.get("CHANNEL_ID_INDIAN")
VIP_FOREX = os.environ.get("CHANNEL_ID_GLOBAL")
QUOTEX_LINK = "https://broker-qx.pro/?lid=2061690"

bot = telebot.TeleBot(TOKEN)

# ================== 2. AI-ML ENGINE ==================
def train_and_predict(df):
    try:
        # Technical Features Calculation
        df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        df['Price_Change'] = df['Close'].pct_change()
        df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
        
        df = df.dropna()
        if len(df) < 50: return None, 0

        X = df[['RSI', 'Price_Change']]
        y = df['Target']
        
        # Machine Learning Model (Random Forest)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X[:-1], y[:-1])
        
        # Prediction for current candle
        last_row = X.tail(1)
        prediction = model.predict(last_row)[0]
        probability = model.predict_proba(last_row).max() * 100
        
        return prediction, probability
    except:
        return None, 0

# ================== 3. SIGNAL GENERATION ==================
def get_ai_signal(asset_list):
    try:
        asset = random.choice(asset_list)
        df = yf.download(asset, period="1d", interval="1m", progress=False)
        
        if df is None or df.empty or len(df) < 60: 
            return None, None, 0

        pred, prob = train_and_predict(df)
        
        # FIXED: Using .iloc[-1] to avoid Series Truth Value Error
        rsi_val = ta.momentum.RSIIndicator(df['Close']).rsi().iloc[-1]
        
        signal = None
        # AI Logic + RSI Filter
        if pred == 1 and rsi_val < 48:
            signal = "CALL 🟢 (AI BUY)"
        elif pred == 0 and rsi_val > 52:
            signal = "PUT 🔴 (AI SELL)"
            
        return asset, signal, round(prob, 2)
    except:
        return None, None, 0

def signal_loop():
    while True:
        try:
            # Scanning Markets
            tasks = [ (["^NSEI", "^BSESN"], VIP_INDIAN), (["EURUSD=X", "GBPUSD=X", "BTC-USD"], VIP_FOREX) ]
            
            for assets, ch_id in tasks:
                a, s, p = get_ai_signal(assets)
                if s and p > 85: # High confidence filter
                    msg = (f"🤖 **RK AI-ML PREDICTION** 🤖\n\n"
                           f"🌍 Asset: {a}\n🚦 Action: {s}\n🎯 AI Confidence: {p}%\n"
                           f"⚡ Method: Random Forest ML\n\n"
                           f"🚀 [TRADE ON QUOTEX]({QUOTEX_LINK})")
                    bot.send_message(ch_id, msg, parse_mode="Markdown")
            
            time.sleep(300) # Every 5 minutes
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(30)

# ================== 4. BOT RUNNER ==================
if __name__ == "__main__":
    try:
        # Step to fix Conflict Error
        bot.remove_webhook()
        print("RK AI-ML Bot is Starting...")
        
        # Running signal loop in background
        threading.Thread(target=signal_loop, daemon=True).start()
        
        # Start polling
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Fatal Error: {e}")
