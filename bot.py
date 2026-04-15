import os
import time
import requests
import pandas as pd
from flask import Flask
from threading import Thread
from binance.client import Client
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Ultra Pro AI Bot Running!"

# =========================
# ENV VARIABLES
# =========================
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

client = Client(API_KEY, API_SECRET)
client.API_URL = "https://testnet.binance.vision/api"

# =========================
# SETTINGS
# =========================
SYMBOL = "BTCUSDT"
QUANTITY = 0.001

in_position = False
entry_price = 0
total_profit = 0
trade_count = 0

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data)
    except:
        pass

# =========================
# GET DATA
# =========================
def get_klines(interval):
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={interval}&limit=50"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])

    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df

# =========================
# 5M TREND
# =========================
def trend_5m():
    df = get_klines("5m")

    close = df["close"]
    ema21 = EMAIndicator(close, window=21).ema_indicator()
    ema50 = EMAIndicator(close, window=50).ema_indicator()

    if ema21.iloc[-1] > ema50.iloc[-1]:
        return "UP"
    else:
        return "DOWN"

# =========================
# AI DECISION (HIGH ACCURACY)
# =========================
def ai_decision(df):
    close = df["close"]

    rsi = RSIIndicator(close).rsi()
    ema21 = EMAIndicator(close, window=21).ema_indicator()
    ema50 = EMAIndicator(close, window=50).ema_indicator()
    vwap = (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()

    latest_price = close.iloc[-1]
    latest_rsi = rsi.iloc[-1]
    latest_ema21 = ema21.iloc[-1]
    latest_ema50 = ema50.iloc[-1]
    latest_vwap = vwap.iloc[-1]

    score = 0

    # Trend
    if latest_ema21 > latest_ema50:
        score += 2
    else:
        score -= 2

    # Price above EMA
    if latest_price > latest_ema21:
        score += 1

    # VWAP
    if latest_price > latest_vwap:
        score += 1

    # RSI zone
    if 30 < latest_rsi < 45:
        score += 2

    # Momentum candle
    if close.iloc[-1] > close.iloc[-2]:
        score += 1

    return score, latest_price, latest_rsi, latest_vwap

# =========================
# MAIN BOT
# =========================
def run_bot():
    global in_position, entry_price, total_profit, trade_count

    print("🔥 ULTRA PRO BOT STARTED", flush=True)

    while True:
        try:
            df = get_klines("1m")
            trend = trend_5m()

            score, price, rsi, vwap = ai_decision(df)

            print(f"\n💰 Price: {price}", flush=True)
            print(f"📉 RSI: {rsi}", flush=True)
            print(f"📊 VWAP: {vwap}", flush=True)
            print(f"📊 5M Trend: {trend}", flush=True)
            print(f"🤖 AI Score: {score}", flush=True)

            # =========================
            # ENTRY
            # =========================
            if not in_position:

                if score >= 5 and trend == "UP":

                    print("🚀 STRONG BUY SIGNAL", flush=True)

                    send_telegram(f"""
🚀 STRONG BUY
Price: {price}
RSI: {rsi}
Trend: {trend}
""")

                    client.order_market_buy(
                        symbol=SYMBOL,
                        quantity=QUANTITY
                    )

                    entry_price = price
                    in_position = True

                    print(f"✅ Bought at {entry_price}", flush=True)

                else:
                    print("⏳ No trade", flush=True)

            # =========================
            # EXIT (TRAILING STOP)
            # =========================
            else:

                profit_percent = (price - entry_price) / entry_price * 100
                stop_loss = entry_price * 0.995

                if profit_percent > 0.5:
                    stop_loss = entry_price

                if profit_percent > 1:
                    stop_loss = entry_price * 1.003

                if profit_percent > 2:
                    stop_loss = entry_price * 1.01

                print(f"📈 Profit: {profit_percent:.2f}%", flush=True)
                print(f"🛑 Trailing SL: {stop_loss}", flush=True)

                if price <= stop_loss:

                    print("❌ EXIT", flush=True)

                    client.order_market_sell(
                        symbol=SYMBOL,
                        quantity=QUANTITY
                    )

                    profit = (price - entry_price) * QUANTITY
                    total_profit += profit
                    trade_count += 1

                    send_telegram(f"""
❌ EXIT
Price: {price}
Profit: {profit}
Total: {total_profit}
Trades: {trade_count}
""")

                    in_position = False

                else:
                    print("⏳ Holding", flush=True)

        except Exception as e:
            print("❌ Error:", str(e), flush=True)

        time.sleep(20)

# Run bot
Thread(target=run_bot).start()

# Render server
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
