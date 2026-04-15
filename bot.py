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
    return "🤖 Smart AI Bot Running!"

# =========================
# 🔑 ENV VARIABLES
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

# =========================
# 📲 TELEGRAM FUNCTION
# =========================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data)
    except:
        pass

# =========================
# 🤖 AI LOGIC
# =========================
def ai_decision(rsi, price, ema, vwap):
    score = 0

    if rsi < 35:
        score += 2
    elif rsi > 65:
        score -= 2

    if price > ema:
        score += 1
    else:
        score -= 1

    if price > vwap:
        score += 1
    else:
        score -= 1

    return score

# =========================
# MAIN BOT
# =========================
def run_bot():
    global in_position, entry_price

    print("🤖 Smart AI Trading Started", flush=True)

    while True:
        try:
            # Market data
            url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval=1m&limit=50"
            data = requests.get(url).json()

            df = pd.DataFrame(data, columns=[
                "time","open","high","low","close","volume",
                "close_time","qav","trades","tbbav","tbqav","ignore"
            ])

            df["close"] = df["close"].astype(float)
            df["volume"] = df["volume"].astype(float)

            # Indicators
            rsi = RSIIndicator(df["close"]).rsi()
            ema = EMAIndicator(df["close"], window=9).ema_indicator()
            df["vwap"] = (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()

            latest_price = df["close"].iloc[-1]
            latest_rsi = rsi.iloc[-1]
            latest_ema = ema.iloc[-1]
            latest_vwap = df["vwap"].iloc[-1]

            print(f"\n💰 Price: {latest_price}", flush=True)
            print(f"📉 RSI: {latest_rsi}", flush=True)
            print(f"📊 VWAP: {latest_vwap}", flush=True)

            decision = ai_decision(latest_rsi, latest_price, latest_ema, latest_vwap)
            print(f"🤖 AI Score: {decision}", flush=True)

            # Debug conditions
            print(f"RSI cond (<35): {latest_rsi < 35}", flush=True)
            print(f"EMA cond: {latest_price > latest_ema}", flush=True)
            print(f"VWAP cond: {latest_price > latest_vwap}", flush=True)

            # =========================
            # ENTRY
            # =========================
            if not in_position:

                if decision >= 2 and latest_price > latest_ema and latest_price > latest_vwap:

                    print("🚀 BUY SIGNAL", flush=True)
                    send_telegram(f"🚀 BUY {SYMBOL} at {latest_price}")

                    order = client.order_market_buy(
                        symbol=SYMBOL,
                        quantity=QUANTITY
                    )

                    entry_price = latest_price
                    in_position = True

                    print(f"✅ Bought at {entry_price}", flush=True)

                else:
                    print("⏳ No trade", flush=True)

            # =========================
            # EXIT
            # =========================
            elif in_position:

                stop_loss = entry_price * 0.995
                target = entry_price * 1.015

                print(f"🛑 SL: {stop_loss} | 🎯 Target: {target}", flush=True)

                if latest_price <= stop_loss:
                    print("❌ STOP LOSS HIT", flush=True)
                    send_telegram(f"❌ SL HIT {SYMBOL} at {latest_price}")

                    client.order_market_sell(
                        symbol=SYMBOL,
                        quantity=QUANTITY
                    )

                    in_position = False

                elif latest_price >= target:
                    print("💰 TARGET HIT", flush=True)
                    send_telegram(f"💰 TARGET HIT {SYMBOL} at {latest_price}")

                    client.order_market_sell(
                        symbol=SYMBOL,
                        quantity=QUANTITY
                    )

                    in_position = False

                else:
                    print("⏳ Holding", flush=True)

        except Exception as e:
            print("❌ Error:", str(e), flush=True)

        time.sleep(20)

# Run in background
Thread(target=run_bot).start()

# Render port
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
