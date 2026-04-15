import pandas as pd
import requests
from datetime import datetime
import os

# ===== FIX PATH =====
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ===== CONFIG =====
FILE = "forecast.csv"

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

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
        data = requests.get(url, timeout=10).json()

        if "c" not in data:
            return None

        return pd.DataFrame({
            "close": data["c"],
            "high": data["h"],
            "low": data["l"],
            "volume": data.get("v", [0]*len(data["c"]))
        })

    except:
        return None

# ===== INDICATORS =====
def compute_score(df):

    if len(df) < 30:
        return None

    close = df["close"]

    # ===== MOMENTUM =====
    momentum = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5]

    # ===== BREAKOUT =====
    breakout = close.iloc[-1] > close.rolling(20).max().iloc[-2]

    # ===== VOLUME =====
    vol = df["volume"]
    vol_score = vol.iloc[-1] / (vol.rolling(20).mean().iloc[-1] + 1)

    # ===== RSI =====
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))

    rsi_val = rsi.iloc[-1]

    # ===== FILTER =====
    if rsi_val > 75:   # quá mua → bỏ
        return None

    # ===== SCORE COMBINE =====
    score = (
        momentum * 0.5 +
        (1 if breakout else 0) * 0.3 +
        min(vol_score, 2) * 0.2
    )

    return round(score, 4), round(momentum,4), breakout, round(vol_score,2), round(rsi_val,1)

# ===== MAIN =====
def scan():

    print("\n⏰ START AI FORECAST:", datetime.now())

    symbols = load_symbols()

    if not symbols:
        print("❌ No symbols")
        return

    results = []

    for s in symbols:

        df = get_data(s)

        if df is None:
            continue

        res = compute_score(df)

        if res is None:
            continue

        score, momentum, breakout, vol_score, rsi = res

        entry = round(df["close"].iloc[-1],1)
        target = round(entry * 1.06,1)

        results.append({
            "symbol": s,
            "entry": entry,
            "target_T4": target,
            "score": score,
            "momentum": momentum,
            "breakout": breakout,
            "volume": vol_score,
            "rsi": rsi
        })

    df_out = pd.DataFrame(results)

    if df_out.empty:
        print("❌ No signal")
        return

    # ===== RANK =====
    df_out = df_out.sort_values(by="score", ascending=False)

    top = df_out.head(3)
    top["time"] = datetime.now()

    top.to_csv(FILE, index=False)

    print("🏆 TOP PICKS:")
    print(top)

    # ===== TELEGRAM =====
    msg = "🔥 TOP 3 T+4 STRONGEST\n\n"

    for _, row in top.iterrows():
        msg += (
            f"{row['symbol']}\n"
            f"Score: {row['score']}\n"
            f"Momentum: {row['momentum']}\n"
            f"Volume: {row['volume']}\n"
            f"RSI: {row['rsi']}\n"
            f"Target: {row['target_T4']}\n\n"
        )

    send(msg)

    print("📨 Sent Telegram")


# ===== RUN =====
if __name__ == "__main__":
    scan()
