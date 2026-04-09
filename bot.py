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
    print("✅ Bot started successfully")

    while True:
        try:
            url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
            response = requests.get(url, timeout=5)
            data = response.json()

            price = float(data['price'])
            print(f"💰 BTC Price: {price}")

            if price > 50000:
                print("📈 BUY signal")
            else:
                print("📉 SELL signal")

        except Exception as e:
            print("❌ Error:", e)

        time.sleep(10)

# 👇 IMPORTANT: start bot BEFORE app.run()
bot_thread = Thread(target=run_bot)
bot_thread.start()

# 👇 Flask must be last
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
