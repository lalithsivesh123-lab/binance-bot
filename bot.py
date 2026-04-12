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
    return "🤖 AI Testnet Trading Bot Running!"

# =========================
# 🔑 TESTNET API KEYS
# =========================
API_KEY = "PASTE_YOUR_TESTNET_API_KEY"
API_SECRET = "PASTE_YOUR_TESTNET_SECRET"

client = Client(API_KEY, API_SECRET)
client.API_URL = "https://testnet.binance.vision/api"

SYMBOL = "BTCUSDT"
QUANTITY = 0.001  # safe test size

in_position = False
entry_price = 0

# =========================
# 🤖 AI DECISION FUNCTION
# =========================
def ai_decision(rsi, price, ema, vwap):
    score = 0

    if rsi < 35:
        score += 1
    elif rsi > 65:
        score -= 1

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

    print("🤖 Testnet Auto Trading Started", flush=True)

    while True:
        try:
            # Get market data
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

            # =========================
            # ENTRY
            # =========================
            if not in_position:

                if decision >= 2:
                    print("🚀 AI BUY SIGNAL", flush=True)

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
            # EXIT (SL / TARGET)
            # =========================
            elif in_position:

                stop_loss = entry_price * 0.99
                target = entry_price * 1.02

                print(f"🛑 SL: {stop_loss} | 🎯 Target: {target}", flush=True)

                if latest_price <= stop_loss:
                    print("❌ STOP LOSS HIT", flush=True)

                    client.order_market_sell(
                        symbol=SYMBOL,
                        quantity=QUANTITY
                    )

                    in_position = False

                elif latest_price >= target:
                    print("💰 TARGET HIT", flush=True)

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

Thread(target=run_bot).start()

app.run(host="0.0.0.0", port=10000)
