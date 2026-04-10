import os
import time
import requests
import pandas as pd
from flask import Flask
from threading import Thread
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running!"

def run_bot():
    print("✅ Strategy bot started", flush=True)

    while True:
        try:
            # Fetch data from Binance
            url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50"
            data = requests.get(url, timeout=5).json()

            df = pd.DataFrame(data, columns=[
                "time","open","high","low","close","volume",
                "close_time","qav","trades","tbbav","tbqav","ignore"
            ])

            # Convert data
            df["close"] = df["close"].astype(float)
            df["volume"] = df["volume"].astype(float)

            # Indicators
            rsi = RSIIndicator(df["close"]).rsi()
            ema = EMAIndicator(df["close"], window=9).ema_indicator()

            # VWAP
            df["vwap"] = (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()

            # Latest values
            latest_price = df["close"].iloc[-1]
            latest_rsi = rsi.iloc[-1]
            latest_ema = ema.iloc[-1]
            latest_vwap = df["vwap"].iloc[-1]

            # Logs
            print(f"\n💰 Price: {latest_price}", flush=True)
            print(f"📉 RSI: {latest_rsi}", flush=True)
            print(f"📊 VWAP: {latest_vwap}", flush=True)

            # Strategy with SL & Target
            if latest_rsi < 30 and latest_price > latest_ema and latest_price > latest_vwap:
                entry = latest_price
                sl = entry * 0.99
                target = entry * 1.02

                print("🚀 STRONG BUY SIGNAL", flush=True)
                print(f"🎯 Entry: {entry}", flush=True)
                print(f"🛑 Stop Loss: {sl}", flush=True)
                print(f"💰 Target: {target}", flush=True)

            elif latest_rsi > 70 and latest_price < latest_ema and latest_price < latest_vwap:
                entry = latest_price
                sl = entry * 1.01
                target = entry * 0.98

                print("🔻 STRONG SELL SIGNAL", flush=True)
                print(f"🎯 Entry: {entry}", flush=True)
                print(f"🛑 Stop Loss: {sl}", flush=True)
                print(f"💰 Target: {target}", flush=True)

            else:
                print("⏳ No trade", flush=True)

        except Exception as e:
            print("❌ Error:", e, flush=True)

        time.sleep(15)

# Start bot thread
Thread(target=run_bot).start()

# Flask server (Render requirement)
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
