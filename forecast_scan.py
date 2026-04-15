import pandas as pd
import requests
from datetime import datetime
import os

# ===== FIX PATH =====
os.chdir(os.path.dirname(os.path.abspath(__file__)))

FILE = "forecast.csv"
STATE_FILE = "forecast_state.json"

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

NAV = 100_000_000


# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass


# ===== LOAD SYMBOL =====
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


# ===== SCORE =====
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


# ===== BACKTEST =====
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


# ===== STATE =====
def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        return pd.read_json(STATE_FILE).to_dict()
    except:
        return None


def save_state(df):
    df = df.drop(columns=["time"], errors="ignore")  # ❗ FIX spam
    df.to_json(STATE_FILE, date_format="iso")


# ===== SAFE SAVE =====
def save_state(df):

    df = df.copy()
    df = df.drop(columns=["time"], errors="ignore")

    df["entry"] = df["entry"].round(2)
    df["sl"] = df["sl"].round(2)
    df["tp"] = df["tp"].round(2)
    df["score"] = df["score"].round(3)
    df["winrate"] = df["winrate"].round(3)

    df.to_json(STATE_FILE, date_format="iso")

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

        winrate = backtest(df)

        entry = df["close"].iloc[-1]

        results.append({
            "symbol": s,
            "entry": round(entry,1),
            "sl": round(entry*0.98,1),
            "tp": round(entry*1.04,1),
            "score": score,
            "winrate": winrate,
            "time": datetime.now()
        })

    df_out = pd.DataFrame(results)

    # ===== KHÔNG BAO GIỜ RỖNG =====
    if df_out.empty:
        df_out = pd.DataFrame([{
            "symbol": "NO_SIGNAL",
            "entry": 0,
            "sl": 0,
            "tp": 0,
            "score": 0,
            "winrate": 0,
            "time": datetime.now()
        }])

    # ===== TOP 3 =====
    df_out = df_out.sort_values(by=["score","winrate"], ascending=False).head(3)

    df_out = df_out.reset_index(drop=True)

    # ===== LUÔN SAVE FILE =====
    safe_save(df_out)

    # ===== CHECK CHANGE (FIX TRÙNG TELE) =====
    old = load_state()
   df_check = df_out.copy()

df_check = df_check.drop(columns=["time"], errors="ignore")

# FIX FLOAT (QUAN TRỌNG NHẤT)
df_check["entry"] = df_check["entry"].round(2)
df_check["sl"] = df_check["sl"].round(2)
df_check["tp"] = df_check["tp"].round(2)
df_check["score"] = df_check["score"].round(3)
df_check["winrate"] = df_check["winrate"].round(3)

new = df_check.to_dict()
    if old == new:
        print("⏸ Không đổi → không gửi Telegram")
        return

    save_state(df_out)

    # ===== TELEGRAM =====
    weights = [0.5, 0.3, 0.2]

    msg = "TOP 3 T+4 PICKS\n\n"

    for idx, row in df_out.iterrows():

        capital = int(NAV * weights[idx])

        msg += (
            f"{row['symbol']}\n"
            f"Entry: {row['entry']}\n"
            f"SL: {row['sl']} | TP: {row['tp']}\n"
            f"Score: {row['score']}\n"
            f"Winrate: {round(row['winrate']*100,1)}%\n"
            f"Vốn: {capital:,}\n\n"
        )

    send(msg)

    print("📨 Sent Telegram")
    print("✅ DONE:", datetime.now())


# ===== RUN =====
if __name__ == "__main__":
    scan()
