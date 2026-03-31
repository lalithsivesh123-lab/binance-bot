from binance.client import Client
import pandas as pd
import time
import os

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

client = Client(API_KEY, API_SECRET)

SYMBOL = "BTCUSDT"

def get_data():
    klines = client.get_klines(symbol=SYMBOL, interval="1m", limit=50)
    df = pd.DataFrame(klines)
    df[4] = df[4].astype(float)
    return df

def strategy(df):
    if df[4].iloc[-1] > df[4].mean():
        return "BUY"
    else:
        return "SELL"

while True:
    df = get_data()
    signal = strategy(df)
    print("Signal:", signal)
    time.sleep(60)
