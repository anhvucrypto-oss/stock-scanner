import requests
import pandas as pd
import os
import time
import base64
from datetime import datetime

print("🚀 META AI FINAL START")
send("BOT START OK")

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

REPO = "anhvucrypto-oss/stock-scanner"
FILE_PATH = "trades_log.csv"

LOG = "trades_log.csv"
MEMORY = "meta_memory.csv"

# INIT
if not os.path.exists(LOG):
    pd.DataFrame(columns=["time","symbol","entry","sl","tp","result","strategy","regime"]).to_csv(LOG,index=False)

if not os.path.exists(MEMORY):
    pd.DataFrame(columns=["regime","strategy","result"]).to_csv(MEMORY,index=False)

# TELEGRAM
def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        res = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=10
        )
        print("📨 Telegram status:", res.status_code, res.text)
    except Exception as e:
        print("❌ Telegram error:", e)

# PUSH
def push():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ No token")
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

        res = requests.put(url, json=data, headers=headers)
        print("📡 GitHub:", res.status_code)

    except Exception as e:
        print("❌ push:", e)

# DATA
def get_data(symbol):
    try:
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol={symbol}&resolution=1D&from=1700000000&to=9999999999"
        data = requests.get(url).json()
        if "c" not in data:
            return None
        return pd.DataFrame({"close":data["c"],"high":data["h"],"low":data["l"]})
    except:
        return None

# MARKET
def detect_market():
    df = get_data("VNINDEX")
    if df is None or len(df) < 50:
        return "sideway"

    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]

    if ma20 > ma50:
        return "trend"
    return "sideway"

# STRATEGY
def trend(df):
    return df["close"].iloc[-1] > df["close"].rolling(20).mean().iloc[-1]

def mean(df):
    rsi = (df["close"].diff().clip(lower=0).rolling(14).mean() /
          df["close"].diff().abs().rolling(14).mean())*100
    return rsi.iloc[-1] < 30

# META
def choose_strategy(regime):
    return "trend" if regime == "trend" else "mean"

symbols = ["FPT","VNM","ACB","DGC","REE"]

# SCAN
def scan(strategy):
    for s in symbols:
        df = get_data(s)
        if df is None:
            continue

        if strategy == "trend" and trend(df):
            return s, df
        if strategy == "mean" and mean(df):
            return s, df

    return None

# SAVE
def save(symbol, entry, sl, tp, strat, regime):

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

# RUN
def run():

    print("\n🚀 RUNNING...")

    regime = detect_market()
    strat = choose_strategy(regime)

    trade = scan(strat)

    if not trade:
        msg = f"NO TRADE | {strat} | {regime}"
        send(msg)
        save("NO_TRADE",0,0,0,strat,regime)
        return

    symbol, df = trade

    entry = round(df["close"].iloc[-1],1)
    sl = round(entry*0.97,1)
    tp = round(entry*1.06,1)

    msg = f"{symbol} | {strat} | {regime} | {entry}"
    send(msg)

    save(symbol,entry,sl,tp,strat,regime)

# LOOP
while True:
    run()
    push()
    time.sleep(60)
