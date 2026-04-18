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

# =========================
# ENV VARIABLES
# =========================
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

client = Client(API_KEY, API_SECRET)
client.API_URL = "https://testnet.binance.vision/api"

# =========================
# GLOBAL STATE
# =========================
SYMBOL = "BTCUSDT"

in_position = False
entry_price = 0
quantity = 0

total_profit = 0
trade_count = 0
wins = 0
losses = 0
last_trade = "No trades yet"
win_rate = 0

daily_loss = 0
max_daily_loss = -5

# =========================
# DASHBOARD
# =========================
@app.route('/')
def dashboard():
    status = "🟢 IN TRADE" if in_position else "⏳ WAITING"
    avg_profit = total_profit / trade_count if trade_count > 0 else 0

    return f"""
    <html>
    <head>
        <title>Pro Trading Dashboard</title>
        <meta http-equiv="refresh" content="10">
    </head>
    <body style="font-family: Arial; background:#0d1117; color:white; padding:20px;">
        <h1>🤖 PRO AI TRADING DASHBOARD</h1>

        <h2>Status: {status}</h2>

        <hr>

        <p>📊 Total Trades: {trade_count}</p>
        <p>✅ Wins: {wins}</p>
        <p>❌ Losses: {losses}</p>
        <p>🎯 Win Rate: {win_rate:.2f}%</p>

        <hr>

        <p>💰 Total Profit: {total_profit:.2f} USDT</p>
        <p>📈 Avg Profit/Trade: {avg_profit:.2f} USDT</p>

        <hr>

        <p>📌 Last Trade: {last_trade}</p>
    </body>
    </html>
    """

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# =========================
# POSITION SIZE
# =========================
def get_quantity(price):
    capital = 100
    risk_per_trade = 0.02
    risk_amount = capital * risk_per_trade
    stop_loss_percent = 0.005

    qty = risk_amount / (price * stop_loss_percent)
    return round(qty, 5)

# =========================
# DATA
# =========================
def get_klines(interval):
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={interval}&limit=50"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])

    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df

# =========================
# FILTERS
# =========================
def is_sideways(df):
    range_percent = ((df["high"].max() - df["low"].min()) / df["low"].min()) * 100
    return range_percent < 0.5

def trend_5m():
    df = get_klines("5m")
    ema21 = EMAIndicator(df["close"], window=21).ema_indicator()
    ema50 = EMAIndicator(df["close"], window=50).ema_indicator()
    return "UP" if ema21.iloc[-1] > ema50.iloc[-1] else "DOWN"

# =========================
# AI DECISION
# =========================
def ai_decision(df):
    close = df["close"]

    rsi = RSIIndicator(close).rsi()
    ema21 = EMAIndicator(close, window=21).ema_indicator()
    ema50 = EMAIndicator(close, window=50).ema_indicator()
    vwap = (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()

    price = close.iloc[-1]
    rsi_val = rsi.iloc[-1]
    vwap_val = vwap.iloc[-1]

    score = 0

    if ema21.iloc[-1] > ema50.iloc[-1]:
        score += 2
    if price > ema21.iloc[-1]:
        score += 1
    if price > vwap_val:
        score += 1
    if 30 < rsi_val < 45:
        score += 2
    if close.iloc[-1] > close.iloc[-2]:
        score += 1

    return score, price, rsi_val

# =========================
# STRATEGY
# =========================
def run_strategy():
    global in_position, entry_price, quantity
    global total_profit, trade_count, wins, losses, last_trade, win_rate, daily_loss

    if daily_loss <= max_daily_loss:
        print("🛑 Daily loss limit reached", flush=True)
        return

    df = get_klines("1m")
    trend = trend_5m()
    score, price, rsi = ai_decision(df)

    volume_avg = df["volume"].rolling(10).mean().iloc[-1]
    volume_ok = df["volume"].iloc[-1] > volume_avg

    print(f"Price: {price} | Score: {score}", flush=True)

    # ENTRY
    if not in_position:
        if score >= 5 and trend == "UP" and rsi < 50 and not is_sideways(df) and volume_ok:

            quantity = get_quantity(price)
            client.order_market_buy(symbol=SYMBOL, quantity=quantity)

            entry_price = price
            in_position = True

            send_telegram(f"🚀 BUY at {price}")

    # EXIT
    else:
        profit_percent = (price - entry_price) / entry_price * 100
        stop_loss = entry_price * 0.995

        if profit_percent > 0.5:
            stop_loss = entry_price
        if profit_percent > 1:
            stop_loss = entry_price * 1.003
        if profit_percent > 2:
            stop_loss = entry_price * 1.01

        if profit_percent > 1:
            client.order_market_sell(symbol=SYMBOL, quantity=quantity / 2)

        if price <= stop_loss:
            client.order_market_sell(symbol=SYMBOL, quantity=quantity / 2)

            profit = (price - entry_price) * quantity
            total_profit += profit
            trade_count += 1

            if profit > 0:
                wins += 1
                result = "WIN"
            else:
                losses += 1
                daily_loss += profit
                result = "LOSS"

            last_trade = f"{result} | {profit:.2f} USDT"

            if trade_count > 0:
                win_rate = (wins / trade_count) * 100

            send_telegram(last_trade)

            in_position = False

# =========================
# MAIN LOOP
# =========================
def run_bot():
    send_telegram("🤖 BOT STARTED 24/7")

    while True:
        try:
            run_strategy()
        except Exception as e:
            send_telegram(f"⚠️ Error: {str(e)}")
        time.sleep(20)

Thread(target=run_bot).start()

# =========================
# SERVER
# =========================
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
