from binance.client import Client
import pandas as pd
import time
import os

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

print("🚀 BOT STARTED")

client = Client(API_KEY, API_SECRET)

SYMBOL = "BTCUSDT"

def get_data():
    klines = client.get_klines(symbol=SYMBOL, interval="1m", limit=50)
    df = pd.DataFrame(klines)
    df[4] = df[4].astype(float)
    return df

while True:
    try:
        df = get_data()
        price = df[4].iloc[-1]
        avg = df[4].mean()

        print(f"Price: {price} | Avg: {avg}")

        if price > avg:
            print("📈 Signal: BUY")
        else:
            print("📉 Signal: SELL")

        time.sleep(10)

    except Exception as e:
        print("❌ ERROR:", e)
        time.sleep(5)
