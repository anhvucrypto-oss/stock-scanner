import requests
import pandas as pd
import os
import time
import base64
from datetime import datetime

print("🚀 META AI FINAL START")

# ===== CONFIG =====
TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

REPO = "anhvucrypto-oss/stock-scanner"
FILE_PATH = "trades_log.csv"

LOG = "trades_log.csv"
MEMORY = "meta_memory.csv"

last_report_date = None

# ===== INIT FILE =====
if not os.path.exists(LOG):
    pd.DataFrame(columns=["time","symbol","entry","sl","tp","result","strategy","regime"]).to_csv(LOG,index=False)

if not os.path.exists(MEMORY):
    pd.DataFrame(columns=["regime","strategy","result"]).to_csv(MEMORY,index=False)

# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

# ===== PUSH =====
def push():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return

    try:
        with open(LOG,"r",encoding="utf-8") as f:
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

    except:
        pass

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

# ===== MARKET =====
def detect_market():
    df = get_data("VNINDEX")
    if df is None or len(df) < 50:
        return "sideway"

    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]
    vol = df["close"].pct_change().rolling(10).std().iloc[-1]

    if ma20 > ma50:
        return "trend"
    if vol > 0.02:
        return "breakout"

    return "sideway"

# ===== STRATEGY =====
def trend(df):
    return df["close"].iloc[-1] > df["close"].rolling(20).mean().iloc[-1]

def mean(df):
    rsi = (df["close"].diff().clip(lower=0).rolling(14).mean() /
          df["close"].diff().abs().rolling(14).mean())*100
    return rsi.iloc[-1] < 30

def breakout(df):
    return df["close"].iloc[-1] > df["high"].rolling(20).max().iloc[-2]

# ===== META =====
def choose_strategy(regime):
    df = pd.read_csv(MEMORY)
    df = df[df["regime"] == regime]

    if len(df) < 10:
        return "trend"

    stats = df.groupby("strategy")["result"].mean()
    return stats.idxmax()

# ===== SYMBOL =====
symbols = ["FPT","VNM","ACB","DGC","REE"]

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

    if not best:
        return None

    s, m, df = best

    entry = round(df["close"].iloc[-1],1)
    sl = round(entry * 0.97,1)
    tp = round(entry * 1.06,1)

    return s, entry, sl, tp

# ===== SAVE TRADE =====
def save_trade(symbol, entry, sl, tp, strat, regime):

    new = pd.DataFrame([{
        "time": datetime.now(),
        "symbol": symbol,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "result": 0,
        "strategy": strat,
        "regime": regime
    }])

    df = pd.read_csv(LOG)
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(LOG, index=False)

# ===== SAVE NO TRADE =====
def save_log(symbol, strat, regime):

    new = pd.DataFrame([{
        "time": datetime.now(),
        "symbol": symbol,
        "entry": 0,
        "sl": 0,
        "tp": 0,
        "result": 0,
        "strategy": strat,
        "regime": regime
    }])

    df = pd.read_csv(LOG)
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(LOG, index=False)

# ===== UPDATE RESULT =====
def update_results():

    df = pd.read_csv(LOG).reset_index(drop=True)
    mem = pd.read_csv(MEMORY).reset_index(drop=True)

    for i in range(len(df)):

        if df.iloc[i]["result"] != 0:
            continue

        symbol = df.iloc[i]["symbol"]

        if symbol == "NO_TRADE":
            continue

        sl = df.iloc[i]["sl"]
        tp = df.iloc[i]["tp"]

        data = get_data(symbol)
        if data is None:
            continue

        for _, row in data.tail(5).iterrows():

            if row["low"] <= sl:
                df.at[i,"result"] = -1
                mem.loc[len(mem)] = [df.iloc[i]["regime"], df.iloc[i]["strategy"], -1]
                break

            if row["high"] >= tp:
                df.at[i,"result"] = 2
                mem.loc[len(mem)] = [df.iloc[i]["regime"], df.iloc[i]["strategy"], 2]
                break

    df.to_csv(LOG,index=False)
    mem.to_csv(MEMORY,index=False)

# ===== DAILY REPORT =====
def daily_report():

    global last_report_date

    today = datetime.now().date()

    if last_report_date == today:
        return

    df = pd.read_csv(LOG)

    if df.empty:
        return

    df["result"] = pd.to_numeric(df["result"], errors="coerce")

    total = len(df)
    win = len(df[df["result"] > 0])
    winrate = round(win / total * 100, 2) if total > 0 else 0
    pnl = df["result"].sum()

    msg = f"""
📊 DAILY REPORT

Trades: {total}
Winrate: {winrate}%
PnL (R): {round(pnl,2)}
"""

    send(msg)

    last_report_date = today

# ===== RUN =====
def run():

    print("\n🚀 RUNNING...")

    regime = detect_market()
    strat = choose_strategy(regime)

    print("Regime:", regime, "| Strategy:", strat)

    trade = scan(strat)

    if not trade:
        msg = f"❌ No trade | {strat} | {regime}"
        print(msg)
        send(msg)
        save_log("NO_TRADE", strat, regime)
        return

    symbol, entry, sl, tp = trade

    msg = f"""
🔥 TRADE

{symbol}
Strategy: {strat}
Regime: {regime}
Entry: {entry}
SL: {sl}
TP: {tp}
"""
    print(msg)

    send(msg)
    save_trade(symbol, entry, sl, tp, strat, regime)

# ===== LOOP =====
while True:

    run()
    update_results()
    daily_report()
    push()

    time.sleep(300)
