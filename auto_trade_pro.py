import requests
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
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

INITIAL_CAPITAL = 100000000
capital = INITIAL_CAPITAL

# ===== RISK CONTROL =====
MAX_DRAWDOWN_ALERT = -5
MAX_DRAWDOWN_STOP = -8

trading_enabled = True
peak_equity = 0

# ===== LOAD SYMBOL =====
symbols = pd.read_csv("symbols.csv")["symbol"].dropna().tolist()

# ===== INIT FILE =====
if not os.path.exists("trades_log.csv"):
    with open("trades_log.csv", "w") as f:
        f.write("time,symbol,entry,sl,tp,result\n")

# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ===== PUSH GITHUB (SAFE TOKEN) =====
def push_to_github():

    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("❌ Không có token")
        return

    try:
        with open("trades_log.csv", "r", encoding="utf-8") as f:
            content = f.read()

        encoded = base64.b64encode(content.encode()).decode()

        url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

        res = requests.get(url, headers=headers)

        sha = res.json()["sha"] if res.status_code == 200 else None

        data = {
            "message": "update trades log",
            "content": encoded
        }

        if sha:
            data["sha"] = sha

        res = requests.put(url, json=data, headers=headers)

        if res.status_code in [200, 201]:
            print("✅ pushed GitHub OK")
        else:
            print("❌ push lỗi:", res.text)

    except Exception as e:
        print("❌ lỗi push:", e)

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
    if df is None:
        return False

    df["ma50"] = df["close"].rolling(50).mean()
    return df["close"].iloc[-1] > df["ma50"].iloc[-1]

# ===== POSITION SIZE =====
def position_size(entry, sl, winrate=0.5, rr=2):
    risk = (winrate * rr - (1 - winrate)) / rr
    risk = max(0.005, min(risk, 0.02))
    risk_money = capital * risk
    qty = int(risk_money / (entry - sl))
    return qty

# ===== SIGNAL =====
def find_trade():
    best = None

    for s in symbols:

        df = get_data(s)
        if df is None:
            continue

        df["rsi"] = RSIIndicator(df["close"], 14).rsi()

        if df["rsi"].iloc[-2] < 50 and df["rsi"].iloc[-1] > 50:

            momentum = (df["close"].iloc[-1] - df["close"].iloc[-4]) / df["close"].iloc[-4]

            if best is None or momentum > best[1]:
                best = (s, momentum, df)

    if best is None:
        return None

    s, m, df = best

    entry = round(df["close"].iloc[-1],1)
    sl = round(entry * 0.97,1)
    tp = round(entry * 1.06,1)

    return s, entry, sl, tp

# ===== SAVE =====
def save_trade(symbol, entry, sl, tp):
    row = f"{datetime.now()},{symbol},{entry},{sl},{tp},0\n"
    with open("trades_log.csv", "a") as f:
        f.write(row)

# ===== UPDATE RESULT =====
def update_results():
    global capital

    df = pd.read_csv("trades_log.csv")

    for i in range(len(df)):

        if df.loc[i,"result"] != 0:
            continue

        symbol = df.loc[i,"symbol"]
        entry = df.loc[i,"entry"]
        sl = df.loc[i,"sl"]
        tp = df.loc[i,"tp"]

        data = get_data(symbol)
        if data is None:
            continue

        recent = data.tail(5)

        for _, row in recent.iterrows():
            if row["low"] <= sl:
                df.loc[i,"result"] = -1
                capital *= 0.98
                break
            if row["high"] >= tp:
                df.loc[i,"result"] = 2
                capital *= 1.02
                break

    df.to_csv("trades_log.csv", index=False)

# ===== DRAWNDOWN =====
def calculate_drawdown():

    global peak_equity

    df = pd.read_csv("trades_log.csv")
    df["result"] = pd.to_numeric(df["result"], errors="coerce")
    df = df.dropna()

    if len(df) == 0:
        return 0

    df["equity"] = df["result"].cumsum()

    current = df["equity"].iloc[-1]
    peak_equity = max(peak_equity, current)

    return current - peak_equity

# ===== RISK CONTROL =====
def risk_control():

    global trading_enabled

    dd = calculate_drawdown()

    print(f"📉 Drawdown: {round(dd,2)}R")

    if dd <= MAX_DRAWDOWN_ALERT:
        send(f"⚠️ WARNING: DD {round(dd,2)}R")

    if dd <= MAX_DRAWDOWN_STOP:
        if trading_enabled:
            send(f"🛑 STOP TRADING: DD {round(dd,2)}R")
        trading_enabled = False

    if dd > -3:
        if not trading_enabled:
            send("✅ RESUME TRADING")
        trading_enabled = True

# ===== RUN =====
def run():

    global trading_enabled

    print("\n🚀 RUNNING...")

    risk_control()

    if not trading_enabled:
        print("🛑 Trading paused")
        return

    if not market_ok():
        print("❌ Market xấu")
        return

    trade = find_trade()

    if trade is None:
        print("❌ No trade")
        return

    symbol, entry, sl, tp = trade

    qty = position_size(entry, sl)

    msg = f"""
🔥 TRADE

{symbol}
Entry: {entry}
SL: {sl}
TP: {tp}
Qty: {qty}
Capital: {round(capital,0)}
"""

    print(msg)

    send(msg)
    save_trade(symbol, entry, sl, tp)

# ===== LOOP =====
while True:

    run()
    update_results()
    push_to_github()

    print(f"💰 Capital: {round(capital,0)}")

    time.sleep(300)