import os
import threading
import time
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running!"

def run_bot():
    print("✅ Bot started successfully")
    
    while True:
        print("🔄 Bot is running and checking market...")
        
        price = 100
        if price > 90:
            print("📈 BUY signal")
        
        time.sleep(10)

# Run bot in background
threading.Thread(target=run_bot).start()

# Required for Render Web Service
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
