import pandas as pd
import requests
from datetime import datetime
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

FILE = "forecast.csv"

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

NAV = 100_000_000  # vốn

# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

# ===== LOAD SYMBOL =====
def load_symbols():
    try:
        df = pd.read_csv("symbols.csv")
        return df["symbol"].dropna().astype(str).tolist()
    except:
        return []

# ===== DATA =====
def get_data(symbol):
    try:
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol={symbol}&resolution=1D&from=1700000000&to=9999999999"
        data = requests.get(url).json()

        return pd.DataFrame({
            "close": data["c"],
            "high": data["h"],
            "low": data["l"]
        })
    except:
        return None

# ===== SCORE =====
def compute_score(df):
    if len(df) < 30:
        return None

    close = df["close"]

    momentum = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5]
    breakout = close.iloc[-1] > close.rolling(20).max().iloc[-2]

    score = momentum + (0.3 if breakout else 0)

    return score, momentum

# ===== BACKTEST T+4 =====
def backtest(df):

    wins = 0
    total = 0

    for i in range(30, len(df)-5):

        entry = df["close"].iloc[i]
        target = entry * 1.05
        stop = entry * 0.97

        future = df.iloc[i+1:i+5]

        hit_tp = any(future["high"] >= target)
        hit_sl = any(future["low"] <= stop)

        if hit_tp:
            wins += 1

        total += 1

    if total == 0:
        return 0

    return round(wins / total, 2)

# ===== MAIN =====
def scan():

    symbols = load_symbols()

    results = []

    for s in symbols:

        df = get_data(s)
        if df is None:
            continue

        res = compute_score(df)
        if res is None:
            continue

        score, momentum = res

        winrate = backtest(df)

        entry = df["close"].iloc[-1]
        sl = entry * 0.97
        tp = entry * 1.05

        results.append({
            "symbol": s,
            "entry": round(entry,1),
            "sl": round(sl,1),
            "tp": round(tp,1),
            "score": round(score,3),
            "winrate": winrate
        })

    df_out = pd.DataFrame(results)

    if df_out.empty:
        return

    # ===== RANK =====
    df_out = df_out.sort_values(by=["score","winrate"], ascending=False)

    top = df_out.head(3)

    # ===== NAV ALLOCATION =====
    weights = [0.5, 0.3, 0.2]

    msg = "🔥 TOP 3 T+4 PICKS\n\n"

    for i, (_, row) in enumerate(top.iterrows()):

        capital = NAV * weights[i]

        msg += (
            f"{row['symbol']}\n"
            f"Entry: {row['entry']}\n"
            f"SL: {row['sl']} | TP: {row['tp']}\n"
            f"Score: {row['score']}\n"
            f"Winrate: {row['winrate']*100}%\n"
            f"Vốn: {int(capital):,}\n\n"
        )

    top["time"] = datetime.now()
    top.to_csv(FILE, index=False)

    send(msg)


if __name__ == "__main__":
    scan()
