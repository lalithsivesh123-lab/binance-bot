from flask import Flask
from binance.client import Client
import os, time, requests

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

client = Client(API_KEY, API_SECRET)

SYMBOL = "BTCUSDT"

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def run_bot():
    while True:
        price = float(client.get_symbol_ticker(symbol=SYMBOL)['price'])

        if int(price) % 2 == 0:
            qty = 0.001
            client.order_market_buy(symbol=SYMBOL, quantity=qty)
            send(f"BUY at {price}")

        time.sleep(60)

@app.route('/')
def home():
    return "Bot Running 🤖"

import threading

threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
