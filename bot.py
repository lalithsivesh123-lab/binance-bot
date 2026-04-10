def run_bot():
    import time
    import requests
    import pandas as pd
    from ta.momentum import RSIIndicator
    from ta.trend import EMAIndicator

    print("✅ Strategy bot started", flush=True)

    while True:
        try:
            url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50"
            data = requests.get(url).json()

            df = pd.DataFrame(data, columns=[
                "time","open","high","low","close","volume",
                "close_time","qav","trades","tbbav","tbqav","ignore"
            ])

            df["close"] = df["close"].astype(float)
            df["volume"] = df["volume"].astype(float)

            # Indicators
            rsi = RSIIndicator(df["close"]).rsi()
            ema = EMAIndicator(df["close"], window=9).ema_indicator()

            # VWAP Calculation
            df["vwap"] = (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()

            latest_price = df["close"].iloc[-1]
            latest_rsi = rsi.iloc[-1]
            latest_ema = ema.iloc[-1]
            latest_vwap = df["vwap"].iloc[-1]

            print(f"💰 Price: {latest_price}", flush=True)
            print(f"📉 RSI: {latest_rsi}", flush=True)
            print(f"📊 VWAP: {latest_vwap}", flush=True)

            # PRO STRATEGY
            if latest_rsi < 30 and latest_price > latest_ema and latest_price > latest_vwap:
                print("🚀 STRONG BUY SIGNAL", flush=True)

            elif latest_rsi > 70 and latest_price < latest_ema and latest_price < latest_vwap:
                print("🔻 STRONG SELL SIGNAL", flush=True)

            else:
                print("⏳ No trade", flush=True)

        except Exception as e:
            print("❌ Error:", e, flush=True)

        time.sleep(15)
