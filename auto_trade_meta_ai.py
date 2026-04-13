import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time
import os
import base64

print("🚀 HEDGE FUND SYSTEM START")

# ===== CONFIG =====
TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

REPO = "anhvucrypto-oss/stock-scanner"
FILE_PATH = "trades_log.csv"

# ===== INIT FILE =====
if not os.path.exists("trades_log.csv"):
    pd.DataFrame(columns=["time","symbol","entry","sl","tp","result"]).to_csv("trades_log.csv",index=False)

# ===== TELEGRAM =====
def send(msg):
    try:
        print("📨", msg)
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

# ===== PUSH GITHUB =====
def push():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ No token")
        return

    try:
        with open("trades_log.csv","r",encoding="utf-8") as f:
            content = f.read()

        encoded = base64.b64encode(content.encode()).decode()

        url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

        res = requests.get(url, headers=headers)
        sha = res.json()["sha"] if res.status_code == 200 else None

        data = {"message":"update","content":encoded}
        if sha:
            data["sha"] = sha

        res = requests.put(url, json=data, headers=headers)
        print("📡 GitHub:", res.status_code)

    except Exception as e:
        print("❌ push error:", e)

# ===== DATA =====
def get_data(symbol):
    try:
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol={symbol}&resolution=1D&from=1700000000&to=9999999999"
        data = requests.get(url).json()

        if "c" not in data:
            return None

        return pd.DataFrame({
            "close": data["c"],
            "high": data["h"],
            "low": data["l"]
        })
    except:
        return None

# ===== MARKET FILTER =====
def market_ok():
    df = get_data("VNINDEX")
    if df is None or len(df) < 50:
        return False

    df["ma50"] = df["close"].rolling(50).mean()
    return df["close"].iloc[-1] > df["ma50"].iloc[-1]

# ===== SIGNAL =====
symbols = ["FPT","VNM","ACB","DGC","REE"]

def find_trade():

    for s in symbols:
        df = get_data(s)
        if df is None:
            continue

        ma20 = df["close"].rolling(20).mean()

        if df["close"].iloc[-1] > ma20.iloc[-1]:
            entry = round(df["close"].iloc[-1],1)
            sl = round(entry*0.97,1)
            tp = round(entry*1.06,1)
            return s, entry, sl, tp

    return None

# ===== SAVE =====
def save(symbol, entry, sl, tp):

    new = pd.DataFrame([{
        "time": datetime.now(),
        "symbol": symbol,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "result": 0
    }])

    df = pd.read_csv("trades_log.csv")
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv("trades_log.csv", index=False)

# ===== NO TRADE LOG =====
def log_no_trade():

    new = pd.DataFrame([{
        "time": datetime.now(),
        "symbol": "NO_TRADE",
        "entry": 0,
        "sl": 0,
        "tp": 0,
        "result": 0
    }])

    df = pd.read_csv("trades_log.csv")
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv("trades_log.csv", index=False)

# ===== RUN =====
def run():

    print("\n🚀 RUNNING...")

    # ❌ MARKET XẤU
    if not market_ok():
    msg = "❌ Market xấu → không trade"
    send(msg)

    # 👇 BẮT BUỘC PHẢI CÓ
    save("NO_TRADE", 0, 0, 0)

    return

    trade = find_trade()

    # ❌ KHÔNG CÓ KÈO
    if trade is None:
        msg = "❌ No trade setup"
        send(msg)
        log_no_trade()
        return

    # ✅ CÓ KÈO
    symbol, entry, sl, tp = trade

    msg = f"""
🔥 TRADE

{symbol}
Entry: {entry}
SL: {sl}
TP: {tp}
"""
    send(msg)

    save(symbol, entry, sl, tp)

# ===== LOOP =====
while True:

    run()
    push()

    time.sleep(60)
