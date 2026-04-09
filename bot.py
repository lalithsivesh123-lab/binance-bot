import os
import threading
import time
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running!"

def run_bot():
    print("✅ Bot started successfully")

    while True:
        try:
            # Binance BTC price
            url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
            data = requests.get(url, timeout=5).json()
            price = float(data['price'])

            print(f"💰 BTC Price: {price}")

            if price > 50000:
                print("📈 BUY signal")
            else:
                print("📉 SELL signal")

        except Exception as e:
            print("❌ Error:", e)

        time.sleep(10)

# Start bot in background
threading.Thread(target=run_bot).start()

# Run Flask server (REQUIRED for Render)
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
