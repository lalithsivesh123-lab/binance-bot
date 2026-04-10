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
    return "✅ Safe Auto Trading Bot Running!"

# Binance API
api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)

SYMBOL = "BTCUSDT"
QUANTITY = 0.0001  # keep small for safety

in_position = False
entry_price = 0

def run_bot():
    global in_position, entry_price

    print("🛡️ Safe Auto Trading Started", flush=True)

    while True:
        try:
            # Fetch data
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

            # =========================
            # ENTRY LOGIC
            # =========================
            if not in_position:

                if latest_rsi < 60 and latest_price > latest_ema and latest_price > latest_vwap:
                    print("🚀 BUY SIGNAL", flush=True)

                    order = client.order_market_buy(
                        symbol=SYMBOL,
                        quantity=QUANTITY
                    )

                    entry_price = latest_price
                    in_position = True

                    print(f"✅ Bought at {entry_price}", flush=True)

            # =========================
            # EXIT LOGIC (SL / TARGET)
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
                    print("⏳ Holding position", flush=True)

        except Exception as e:
            print("❌ Error:", e, flush=True)

        time.sleep(20)

Thread(target=run_bot).start()

port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
