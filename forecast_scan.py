import pandas as pd
import requests
from datetime import datetime
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

FILE = "forecast.csv"


def load_symbols():
    try:
        df = pd.read_csv("symbols.csv")
        return df["symbol"].dropna().astype(str).tolist()
    except:
        return []


def get_data(symbol):
    try:
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol={symbol}&resolution=1D&from=1700000000&to=9999999999"
        data = requests.get(url, timeout=10).json()

        return pd.DataFrame({
            "close": data["c"],
            "high": data["h"],
            "low": data["l"],
            "volume": data.get("v", [0]*len(data["c"]))
        })
    except:
        return None


def compute_score(df):
    if len(df) < 50:
        return None

    close = df["close"]

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()

    if ma20.iloc[-1] < ma50.iloc[-1]:
        return None

    momentum = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5]
    pullback = close.iloc[-1] < close.rolling(10).max().iloc[-1] * 0.98

    if not pullback:
        return None

    breakout = close.iloc[-1] > close.iloc[-2]

    vol = df["volume"]
    vol_score = vol.iloc[-1] / (vol.rolling(20).mean().iloc[-1] + 1)

    score = momentum*0.5 + (1 if breakout else 0)*0.3 + min(vol_score,2)*0.2

    return round(score,4)


def backtest(df):
    wins = 0
    total = 0

    for i in range(50, len(df)-5):
        entry = df["close"].iloc[i]
        tp = entry * 1.04

        future = df.iloc[i+1:i+5]

        if any(future["high"] >= tp):
            wins += 1

        total += 1

    return round(wins/total,3) if total else 0


def scan():

    print("\n⏰ SCAN:", datetime.now())

    symbols = load_symbols()
    results = []

    for s in symbols:

        df = get_data(s)
        if df is None:
            continue

        score = compute_score(df)
        if score is None:
            continue

        winrate = backtest(df)

        entry = df["close"].iloc[-1]

        results.append({
            "symbol": s,
            "entry": round(entry,1),
            "sl": round(entry*0.98,1),
            "tp": round(entry*1.04,1),
            "score": score,
            "winrate": winrate
        })

    df_out = pd.DataFrame(results)

    if df_out.empty:
        df_out = pd.DataFrame([{
            "symbol": "NO_SIGNAL",
            "entry": 0,
            "sl": 0,
            "tp": 0,
            "score": 0,
            "winrate": 0
        }])

    df_out = df_out.sort_values(by=["score","winrate"], ascending=False).head(3)
    df_out = df_out.reset_index(drop=True)

    df_out.to_csv(FILE, index=False)

    print("📄 Saved forecast.csv")
