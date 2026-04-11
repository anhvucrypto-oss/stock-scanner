import requests
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from datetime import datetime
import time
import os
import base64

print("🚀 AUTO TRADE REALTIME BOT START")

# ===== CONFIG =====
TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"
REPO = "YOUR_USERNAME/stock-scanner"
FILE_PATH = "trades_log.csv"

CAPITAL = 100000000
RISK = 0.01

# ===== LOAD SYMBOL =====
symbols = pd.read_csv("symbols.csv")["symbol"].dropna().tolist()
print(f"✅ Loaded {len(symbols)} symbols")

# ===== INIT LOG FILE =====
if not os.path.exists("trades_log.csv"):
    with open("trades_log.csv", "w") as f:
        f.write("time,symbol,entry,sl,tp,result\n")

# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        print("❌ Telegram lỗi")

# ===== PUSH GITHUB =====
def push_to_github():
    try:
        with open("trades_log.csv", "r") as f:
            content = f.read()

        encoded = base64.b64encode(content.encode()).decode()

        url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

        res = requests.get(url, headers={
            "Authorization": f"token {GITHUB_TOKEN}"
        })

        sha = None
        if res.status_code == 200:
            sha = res.json()["sha"]

        data = {
            "message": "update trades log",
            "content": encoded,
            "sha": sha
        }

        requests.put(url, json=data, headers={
            "Authorization": f"token {GITHUB_TOKEN}"
        })

        print("✅ pushed to GitHub")

    except Exception as e:
        print("❌ Push lỗi:", e)

# ===== DATA =====
def get_data(symbol):
    try:
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol={symbol}&resolution=1D&from=1700000000&to=9999999999"
        data = requests.get(url, timeout=10).json()

        if "c" not in data:
            return None

        df = pd.DataFrame({
            "close": data["c"],
            "high": data["h"],
            "low": data["l"]
        })

        if len(df) < 50:
            return None

        return df

    except:
        return None

# ===== SIGNAL =====
def find_trade():

    for s in symbols:

        print(f"🔎 {s}")

        df = get_data(s)
        if df is None:
            continue

        df["rsi"] = RSIIndicator(df["close"], 14).rsi()

        # simple signal (demo)
        if df["rsi"].iloc[-2] < 50 and df["rsi"].iloc[-1] > 50:

            entry = round(df["close"].iloc[-1], 1)
            sl = round(entry * 0.97, 1)
            tp = round(entry * 1.06, 1)

            return s, entry, sl, tp

    return None

# ===== SAVE TRADE =====
def save_trade(symbol, entry, sl, tp):

    row = f"{datetime.now()},{symbol},{entry},{sl},{tp},\n"

    with open("trades_log.csv", "a") as f:
        f.write(row)

# ===== RUN =====
def run():

    print("\n🚀 RUNNING...")

    trade = find_trade()

    if trade is None:
        print("❌ No trade")
        return

    symbol, entry, sl, tp = trade

    msg = f"""
🔥 TRADE

{symbol}
Entry: {entry}
SL: {sl}
TP: {tp}
"""

    print(msg)

    send(msg)
    save_trade(symbol, entry, sl, tp)
    push_to_github()

# ===== LOOP =====
while True:

    run()

    print("⏳ Sleep 5 phút...\n")
    time.sleep(300)
