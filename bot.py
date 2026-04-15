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
    return "🤖 AI PRO Trading Bot Running!"

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
total_profit = 0
trade_count = 0

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data)
    except:
        pass

# =========================
# AI LOGIC
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
    global in_position, entry_price, total_profit, trade_count

    print("🤖 PRO AI BOT STARTED", flush=True)

    while True:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval=1m&limit=50"
            data = requests.get(url).json()

            df = pd.DataFrame(data, columns=[
                "time","open","high","low","close","volume",
                "close_time","qav","trades","tbbav","tbqav","ignore"
            ])

            df["close"] = df["close"].astype(float)
            df["volume"] = df["volume"].astype(float)

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

                if decision >= 2 and latest_price > latest_ema and latest_price > latest_vwap:

                    print("🚀 BUY SIGNAL", flush=True)

                    send_telegram(f"""
🚀 BUY SIGNAL
Pair: {SYMBOL}
Price: {latest_price}
AI Score: {decision}
""")

                    client.order_market_buy(
                        symbol=SYMBOL,
                        quantity=QUANTITY
                    )

                    entry_price = latest_price
                    in_position = True

                    print(f"✅ Bought at {entry_price}", flush=True)

                else:
                    print("⏳ No trade", flush=True)

            # =========================
            # EXIT (TRAILING STOP)
            # =========================
            elif in_position:

                profit_percent = (latest_price - entry_price) / entry_price * 100

                stop_loss = entry_price * 0.995

                if profit_percent > 0.5:
                    stop_loss = entry_price

                if profit_percent > 1:
                    stop_loss = entry_price * 1.003

                if profit_percent > 2:
                    stop_loss = entry_price * 1.01

                print(f"📈 Profit: {profit_percent:.2f}%", flush=True)
                print(f"🛑 Trailing SL: {stop_loss}", flush=True)

                if latest_price <= stop_loss:

                    print("❌ EXIT (Trailing SL HIT)", flush=True)

                    client.order_market_sell(
                        symbol=SYMBOL,
                        quantity=QUANTITY
                    )

                    profit = (latest_price - entry_price) * QUANTITY
                    total_profit += profit
                    trade_count += 1

                    print(f"💰 Trade Profit: {profit}", flush=True)
                    print(f"📊 Total Profit: {total_profit}", flush=True)

                    send_telegram(f"""
❌ EXIT
Pair: {SYMBOL}
Price: {latest_price}
Profit: {profit}
Total Profit: {total_profit}
Trades: {trade_count}
""")

                    in_position = False

                else:
                    print("⏳ Holding (Trailing Active)", flush=True)

        except Exception as e:
            print("❌ Error:", str(e), flush=True)

        time.sleep(20)

# Run bot
Thread(target=run_bot).start()

# Render server
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
