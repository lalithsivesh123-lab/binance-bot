import os
import time
import requests
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running!"

def run_bot():
    print("✅ Bot started successfully", flush=True)

    while True:
        try:
            url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
            response = requests.get(url, timeout=5)
            data = response.json()

            price = float(data['price'])
            print(f"💰 BTC Price: {price}", flush=True)

            if price > 50000:
                print("📈 BUY signal", flush=True)
            else:
                print("📉 SELL signal", flush=True)

        except Exception as e:
            print("❌ Error:", e, flush=True)

        time.sleep(10)

Thread(target=run_bot).start()

port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
