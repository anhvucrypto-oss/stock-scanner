import pandas as pd
import requests
from datetime import datetime
import os

# ===== FIX PATH =====
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ===== CONFIG =====
FILE = "forecast.csv"
EQUITY_FILE = "equity_log.csv"

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

NAV = 100_000_000

# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

# ===== LOAD SYMBOLS =====
def load_symbols():
    try:
        df = pd.read_csv("symbols.csv")
        return df["symbol"].dropna().astype(str).tolist()
    except:
        return []

# ===== GET DATA =====
def get_data(symbol):
    try:
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol={symbol}&resolution=1D&from=1700000000&to=9999999999"
        data = requests.get(url).json()

        return pd.DataFrame({
            "close": data["c"],
            "high": data["h"],
            "low": data["l"],
            "volume": data.get("v", [0]*len(data["c"]))
        })
    except:
        return None

# ===== SCORE (OPTIMIZED) =====
def compute_score(df):

    if len(df) < 50:
        return None

    close = df["close"]

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()

    trend = ma20.iloc[-1] > ma50.iloc[-1]
    if not trend:
        return None

    momentum = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5]

    pullback = close.iloc[-1] < close.rolling(10).max().iloc[-1] * 0.98
    if not pullback:
        return None

    breakout = close.iloc[-1] > close.iloc[-2]

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    rsi_val = rsi.iloc[-1]

    if rsi_val > 70:
        return None

    vol = df["volume"]
    vol_score = vol.iloc[-1] / (vol.rolling(20).mean().iloc[-1] + 1)

    score = (
        momentum * 0.4 +
        (1 if breakout else 0) * 0.2 +
        min(vol_score, 2) * 0.2 +
        (1 if trend else 0) * 0.2
    )

    return round(score,4)

# ===== BACKTEST =====
def backtest(df):

    equity = 1.0
    peak = 1.0
    max_dd = 0

    wins = 0
    total = 0

    for i in range(50, len(df)-5):

        entry = df["close"].iloc[i]
        target = entry * 1.04
        stop = entry * 0.98

        future = df.iloc[i+1:i+5]

        hit_tp = any(future["high"] >= target)
        hit_sl = any(future["low"] <= stop)

        if hit_tp:
            equity *= 1.04
            wins += 1
        elif hit_sl:
            equity *= 0.98

        total += 1

        peak = max(peak, equity)
        dd = (peak - equity) / peak
        max_dd = max(max_dd, dd)

    winrate = wins / total if total > 0 else 0

    return round(winrate,3), round(max_dd,3), round(equity,2)

# ===== MAIN =====
def scan():

    print("\n⏰ START:", datetime.now())

    symbols = load_symbols()
    results = []

    for s in symbols:

        df = get_data(s)
        if df is None:
            continue

        score = compute_score(df)
        if score is None:
            continue

        winrate, max_dd, equity = backtest(df)

        entry = df["close"].iloc[-1]
        sl = entry * 0.98
        tp = entry * 1.04

        results.append({
            "symbol": s,
            "entry": round(entry,1),
            "sl": round(sl,1),
            "tp": round(tp,1),
            "score": score,
            "winrate": winrate,
            "max_dd": max_dd,
            "equity": equity
        })

    df_out = pd.DataFrame(results)

    if df_out.empty:
        print("❌ No signal")
        return

    # ===== FILTER EDGE =====
    df_out = df_out[df_out["winrate"] > 0.55]

    if df_out.empty:
        print("❌ No strong edge")
        return

    # ===== RANK =====
    df_out = df_out.sort_values(by=["score","winrate"], ascending=False)

    top = df_out.head(3).copy()  # TOP 3 ONLY
    top["time"] = datetime.now()

    top.to_csv(FILE, index=False)

    # ===== SAVE EQUITY =====
    if os.path.exists(EQUITY_FILE):
        eq = pd.read_csv(EQUITY_FILE)
        eq = pd.concat([eq, top], ignore_index=True)
    else:
        eq = top

    eq.to_csv(EQUITY_FILE, index=False)

    print("🏆 TOP PICK:")
    print(top)

    # ===== TELEGRAM =====
    row = top.iloc[0]

    capital = NAV

    msg = (
        "🔥 BEST T+4 PICK\n\n"
        f"{row['symbol']}\n"
        f"Entry: {row['entry']}\n"
        f"SL: {row['sl']} | TP: {row['tp']}\n"
        f"Score: {row['score']}\n"
        f"Winrate: {round(row['winrate']*100,1)}%\n"
        f"Max DD: {round(row['max_dd']*100,1)}%\n"
        f"Equity: {row['equity']}x\n"
        f"Vốn: {capital:,}\n"
    )

    send(msg)

    print("📨 SENT")


# ===== RUN =====
if __name__ == "__main__":
    scan()
