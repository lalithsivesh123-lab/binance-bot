def run_bot():
    import time
    import requests

    print("✅ Bot started successfully")

    while True:
        try:
            # Get BTC price from Binance
            url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
            data = requests.get(url).json()
            price = float(data['price'])

            print(f"💰 BTC Price: {price}")

            # Simple strategy (test)
            if price > 50000:
                print("📈 BUY signal")
            else:
                print("📉 SELL signal")

        except Exception as e:
            print("❌ Error:", e)

        time.sleep(10)
