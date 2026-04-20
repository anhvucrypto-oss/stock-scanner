import pandas as pd
import requests
from datetime import datetime
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

FORECAST_FILE = "forecast.csv"

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"


def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        r = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        }, timeout=10)

        print("📡 TELEGRAM RESPONSE:", r.text)

    except Exception as e:
        print("❌ TELEGRAM ERROR:", e)


def run():

    print("\n🚀 BOT DEBUG RUNNING...")

    # ===== LOAD FORECAST =====
    if not os.path.exists(FORECAST_FILE):
        print("❌ forecast.csv NOT FOUND")
        return

    df = pd.read_csv(FORECAST_FILE)

    if df.empty:
        print("❌ forecast EMPTY")
        return

    # ===== BUILD MESSAGE =====
    msg = "🔥 TEST SIGNAL\n\n"

    for _, row in df.head(3).iterrows():
        msg += (
            f"{row['symbol']}\n"
            f"Entry: {row['entry']}\n"
            f"SL: {row['sl']} | TP: {row['tp']}\n"
            f"Score: {row['score']}\n\n"
        )

    # ===== FORCE SEND =====
    print("📤 Sending Telegram...")
    send(msg)


if __name__ == "__main__":
    run()
