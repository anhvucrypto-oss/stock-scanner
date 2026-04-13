import requests
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from datetime import datetime
import time
import os
import base64

print("🚀 META AI SYSTEM START")

# ===== CONFIG =====
TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

REPO = "anhvucrypto-oss/stock-scanner"
FILE_PATH = "trades_log.csv"

# ===== MEMORY FILE =====
MEMORY_FILE = "meta_memory.csv"

# ===== INIT MEMORY =====
if not os.path.exists(MEMORY_FILE):
    df_mem = pd.DataFrame(columns=["regime","strategy","result"])
    df_mem.to_csv(MEMORY_FILE, index=False)

# ===== LOAD SYMBOL =====
symbols = pd.read_csv("symbols.csv")["symbol"].dropna().tolist()

# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ===== PUSH =====
def push():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return

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

    requests.put(url, json=data, headers=headers)

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

# ===== MARKET REGIME =====
def detect_market():

    df = get_data("VNINDEX")
    if df is None:
        return "unknown"

    df["ma20"] = df["close"].rolling(20).mean()
    df["ma50"] = df["close"].rolling(50).mean()

    vol = df["close"].pct_change().rolling(10).std().iloc[-1]

    if df["ma20"].iloc[-1] > df["ma50"].iloc[-1]:
        return "trend"

    if vol > 0.02:
        return "breakout"

    return "sideway"

# ===== STRATEGIES =====
def trend(df):
    df["ma20"] = df["close"].rolling(20).mean()
    return df["close"].iloc[-1] > df["ma20"].iloc[-1]

def mean(df):
    df["rsi"] = RSIIndicator(df["close"], 14).rsi()
    return df["rsi"].iloc[-1] < 30

def breakout(df):
    return df["close"].iloc[-1] > df["high"].rolling(20).max().iloc[-2]

# ===== META AI CHOOSE =====
def choose_strategy(regime):

    df = pd.read_csv(MEMORY_FILE)

    df = df[df["regime"] == regime]

    if len(df) < 10:
        return "trend"  # default

    stats = df.groupby("strategy")["result"].mean()

    best = stats.idxmax()

    print(f"🤖 META chọn: {best} trong {regime}")

    return best

# ===== SAVE MEMORY =====
def update_memory(regime, strategy, result):

    df = pd.read_csv(MEMORY_FILE)

    new = pd.DataFrame([[regime, strategy, result]], columns=df.columns)

    df = pd.concat([df, new], ignore_index=True)

    df.to_csv(MEMORY_FILE, index=False)

# ===== SCAN =====
def scan(strategy):

    best = None

    for s in symbols:

        df = get_data(s)
        if df is None:
            continue

        signal = False

        if strategy == "trend":
            signal = trend(df)
        elif strategy == "mean":
            signal = mean(df)
        elif strategy == "breakout":
            signal = breakout(df)

        if signal:

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

# ===== SAVE TRADE =====
def save(symbol, entry, sl, tp, strategy, regime):
    row = f"{datetime.now()},{symbol},{entry},{sl},{tp},0,{strategy},{regime}\n"
    with open("trades_log.csv","a") as f:
        f.write(row)

# ===== UPDATE RESULT =====
def update_results():

    df = pd.read_csv(LOG)
    mem = pd.read_csv(MEMORY)

    # reset index cho chắc
    df = df.reset_index(drop=True)
    mem = mem.reset_index(drop=True)

    for i in range(len(df)):

        # dùng iloc thay vì loc
        if df.iloc[i]["result"] != 0:
            continue

        symbol = df.iloc[i]["symbol"]
        sl = df.iloc[i]["sl"]
        tp = df.iloc[i]["tp"]

        data = get_data(symbol)
        if data is None:
            continue

        for _, row in data.tail(5).iterrows():

            if row["low"] <= sl:
                df.at[i, "result"] = -1
                mem.loc[len(mem)] = [df.iloc[i]["regime"], df.iloc[i]["strategy"], -1]
                break

            if row["high"] >= tp:
                df.at[i, "result"] = 2
                mem.loc[len(mem)] = [df.iloc[i]["regime"], df.iloc[i]["strategy"], 2]
                break

    df.to_csv(LOG, index=False)
    mem.to_csv(MEMORY, index=False)

# ===== RUN =====
def run():

    print("\n🚀 RUNNING...")

    regime = detect_market()
    strategy = choose_strategy(regime)

    print(f"📊 Regime: {regime} → Strategy: {strategy}")

    trade = scan(strategy)

    if not trade:
        print("❌ No trade")
        return

    symbol, entry, sl, tp = trade

    msg = f"""
🔥 META AI TRADE

Regime: {regime}
Strategy: {strategy}
{symbol}
Entry: {entry}
SL: {sl}
TP: {tp}
"""

    print(msg)

    send(msg)
    save(symbol, entry, sl, tp, strategy, regime)

# ===== LOOP =====
while True:
    run()
    update_results()
    push()
    time.sleep(300)
