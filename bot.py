import os
import time
import math
from datetime import datetime

from flask import Flask, jsonify, render_template_string
from threading import Thread

from binance.client import Client
from binance.enums import *

# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

SYMBOL = "BTCUSDT"
INTERVAL = Client.KLINE_INTERVAL_1MINUTE
TRADE_AMOUNT_USDT = 10
PAPER_TRADING = True          # Change to False for real trading
TAKE_PROFIT = 0.008           # 0.8%
STOP_LOSS = 0.004             # 0.4%

client = Client(API_KEY, API_SECRET)

# ============================================================
# GLOBAL VARIABLES
# ============================================================

bot_running = True
position = None
entry_price = 0.0
quantity = 0.0
total_trades = 0
winning_trades = 0
losing_trades = 0
total_profit = 0.0
last_signal = "WAIT"
latest_price = 0.0
logs = []

# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Binance Trading Bot</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {
            font-family: Arial;
            background: #111;
            color: white;
            padding: 20px;
        }
        .card {
            background: #222;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        h1 { color: #00ff99; }
        pre {
            background: black;
            padding: 15px;
            border-radius: 10px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <h1>🚀 Binance AI Trading Bot</h1>

    <div class="card">
        <h2>Live Statistics</h2>
        <p>Price: {{ price }}</p>
        <p>Signal: {{ signal }}</p>
        <p>Position: {{ position }}</p>
        <p>Total Trades: {{ trades }}</p>
        <p>Winning Trades: {{ wins }}</p>
        <p>Losing Trades: {{ losses }}</p>
        <p>Total Profit: ${{ profit }}</p>
    </div>

    <div class="card">
        <h2>Live Logs</h2>
        <pre>{% for log in logs %}{{ log }}
{% endfor %}</pre>
    </div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(
        HTML,
        price=latest_price,
        signal=last_signal,
        position=position or "NONE",
        trades=total_trades,
        wins=winning_trades,
        losses=losing_trades,
        profit=round(total_profit, 2),
        logs=logs[-30:]
    )

@app.route("/health")
def health():
    return jsonify({"status": "running"})

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    text = f"[{timestamp}] {message}"
    print(text, flush=True)
    logs.append(text)

    if len(logs) > 500:
        logs.pop(0)

def get_price():
    ticker = client.get_symbol_ticker(symbol=SYMBOL)
    return float(ticker["price"])

def calculate_signal():
    klines = client.get_klines(
        symbol=SYMBOL,
        interval=INTERVAL,
        limit=50
    )

    closes = [float(k[4]) for k in klines]

    ema9 = sum(closes[-9:]) / 9
    ema21 = sum(closes[-21:]) / 21

    current = closes[-1]

    score = 0

    if current > ema9:
        score += 1

    if ema9 > ema21:
        score += 1

    if closes[-1] > closes[-2]:
        score += 1

    return score

def buy():
    global position, entry_price, quantity, total_trades

    price = get_price()
    qty = round(TRADE_AMOUNT_USDT / price, 6)

    if not PAPER_TRADING:
        client.order_market_buy(
            symbol=SYMBOL,
            quantity=qty
        )

    position = "LONG"
    entry_price = price
    quantity = qty
    total_trades += 1

    log(f"🚀 BUY @ {price} | Qty: {qty}")

def sell():
    global position, total_profit
    global winning_trades, losing_trades

    price = get_price()

    if not PAPER_TRADING:
        client.order_market_sell(
            symbol=SYMBOL,
            quantity=quantity
        )

    pnl = (price - entry_price) * quantity
    total_profit += pnl

    if pnl > 0:
        winning_trades += 1
    else:
        losing_trades += 1

    log(f"💰 SELL @ {price} | PnL: ${round(pnl,2)}")

    position = None

# ============================================================
# MAIN BOT LOOP
# ============================================================

def trading_bot():
    global latest_price, last_signal

    log("Bot started successfully.")

    while bot_running:
        try:
            latest_price = get_price()
            score = calculate_signal()

            log(f"Price: {latest_price} | Score: {score}")

            if position is None:
                if score >= 3:
                    last_signal = "BUY"
                    buy()
                else:
                    last_signal = "WAIT"

            else:
                current_profit = (
                    (latest_price - entry_price) / entry_price
                )

                if current_profit >= TAKE_PROFIT:
                    sell()

                elif current_profit <= -STOP_LOSS:
                    sell()

            time.sleep(20)

        except Exception as e:
            log(f"ERROR: {e}")
            time.sleep(30)

# ============================================================
# STARTUP
# ============================================================

if __name__ == "__main__":
    Thread(target=trading_bot).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
