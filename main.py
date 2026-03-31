import yfinance as yf
import telebot
import os
import time
import threading
import pandas as pd
import mplfinance as mpf
import requests
from bs4 import BeautifulSoup

# Setup
TOKEN = os.getenv("BOT_TOKEN", "8626210155:AAH914jJYsADPAU4ZuLK3gdaZiW611TAj5o")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@rkniftysignals")
bot = telebot.TeleBot(TOKEN)

# 📈 Chart Generator
def save_chart(df, symbol, name):
    df_chart = df.tail(30) # Last 30 candles
    file_path = f"{name}_chart.png"
    
    # EMA Indicators for Chart
    ema9 = df_chart['Close'].ewm(span=9).mean()
    ema21 = df_chart['Close'].ewm(span=21).mean()
    apds = [mpf.make_addplot(ema9, color='blue'), mpf.make_addplot(ema21, color='orange')]
    
    mpf.plot(df_chart, type='candle', style='charles', 
             title=f"{name} Live Chart", savefig=file_path, addplot=apds)
    return file_path

# 🔔 News Alert (Scraper)
def get_market_news():
    try:
        url = "https://economictimes.indiatimes.com/markets/stocks/news"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_title = soup.find('h3').text
        return f"📰 **MARKET NEWS ALERT**\n\n{news_title}\n\nStay alert! ⚠️"
    except:
        return None

# 🎯 Advanced Signal Logic (Trailing SL & Format)
def generate_advanced_signal(symbol, name):
    df = yf.download(symbol, period="5d", interval="5m", progress=False)
    if df.empty: return None, None

    close = df['Close']
    price = float(close.iloc[-1].item())
    
    # Basic Strategy
    ema9 = close.ewm(span=9).mean().iloc[-1]
    ema21 = close.ewm(span=21).mean().iloc[-1]
    
    msg = ""
    if ema9 > ema21:
        msg = (f"🚀 **{name} POWER SIGNAL**\n\n"
               f"Action: **BUY / CALL** 🔥\n"
               f"Entry: {price:.2f}\n"
               f"StopLoss: {price-40:.2f}\n"
               f"Target: {price+80:.2f}\n\n"
               f"✅ **TRAILING SL:** Once profit reaches +20 points, move SL to Entry Price.")
    elif ema9 < ema21:
        msg = (f"📉 **{name} DANGER SIGNAL**\n\n"
               f"Action: **SELL / PUT** 📉\n"
               f"Entry: {price:.2f}\n"
               f"StopLoss: {price+40:.2f}\n"
               f"Target: {price-80:.2f}\n\n"
               f"✅ **TRAILING SL:** Lock profits as price moves down.")
    
    chart_file = save_chart(df, symbol, name)
    return msg, chart_file

# 🤖 Promotional Msg (Like your SS)
def send_promo():
    promo_text = (
        "💎 **VIP COMPOUNDING SESSION**\n\n"
        "If you want to earn 50k daily with us, join our VIP channel now.\n"
        "Register here: [Link]\n\n"
        "Follow these steps:\n"
        "1. Open Account\n"
        "2. Deposit Min $50\n"
        "3. Send ID to @Admin"
    )
    bot.send_message(CHANNEL_ID, promo_text, parse_mode="Markdown")

# Auto Loop
def main_loop():
    while True:
        try:
            # 1. Send Signals with Charts
            for sym, nme in [("^NSEI", "NIFTY"), ("^NSEBANK", "BANKNIFTY")]:
                signal_msg, chart_img = generate_advanced_signal(sym, nme)
                if signal_msg:
                    with open(chart_img, 'rb') as photo:
                        bot.send_photo(CHANNEL_ID, photo, caption=signal_msg, parse_mode="Markdown")
            
            # 2. News Alert
            news = get_market_news()
            if news: bot.send_message(CHANNEL_ID, news, parse_mode="Markdown")
            
            # 3. Promo Msg every 1 hour
            if time.localtime().tm_min == 0:
                send_promo()

        except Exception as e:
            print(f"Loop Error: {e}")
        
        time.sleep(900) # Every 15 mins

if __name__ == "__main__":
    print("Bot is flying... 🚀")
    threading.Thread(target=main_loop, daemon=True).start()
    bot.infinity_polling()
