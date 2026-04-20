import pandas as pd
import requests
from datetime import datetime
import os
import json
import hashlib
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

FORECAST_FILE = "forecast.csv"
STATE_FILE = "bot_state.json"

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

NAV = 100_000_000


def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        print("❌ Telegram lỗi")


def allow_send_time():
    now = datetime.now()
    return (now.hour > 9) or (now.hour == 9 and now.minute >= 30)


# ===== STATE =====
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"sig": "", "ready": False, "time": 0}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"sig": "", "ready": False, "time": 0}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def load_forecast():
    if not os.path.exists(FORECAST_FILE):
        return None

    df = pd.read_csv(FORECAST_FILE)
    if df.empty:
        return None

    return df.head(3)


def get_data(symbol):
    try:
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol={symbol}&resolution=1D&from=1700000000&to=9999999999"
        data = requests.get(url, timeout=10).json()

        return pd.DataFrame({"close": data["c"]})
    except:
        return None


def check_entry(df):
    if len(df) < 20:
        return False

    ma20 = df["close"].rolling(20).mean()
    return bool(df["close"].iloc[-1] > ma20.iloc[-1])


# ===== SIGNATURE =====
def build_signature(results):

    clean = []

    for r in results:
        clean.append({
            "symbol": r["symbol"],
            "entry": round(r["entry"],2),
            "sl": round(r["sl"],2),
            "tp": round(r["tp"],2),
            "score": round(r["score"],3)
        })

    clean = sorted(clean, key=lambda x: x["symbol"])

    data = json.dumps(clean, sort_keys=True)
    return hashlib.md5(data.encode()).hexdigest()


# ===== MAIN =====
def run():

    print("\n🚀 BOT RUNNING...")

    forecast_df = load_forecast()
    if forecast_df is None:
        return

    results = []

    for i, row in forecast_df.iterrows():

        symbol = str(row["symbol"])

        df = get_data(symbol)
        if df is None:
            continue

        has_entry = check_entry(df)

        results.append({
            "symbol": symbol,
            "entry": float(row["entry"]),
            "sl": float(row["sl"]),
            "tp": float(row["tp"]),
            "score": float(row["score"]),
            "winrate": float(row["winrate"]),
            "capital": int(NAV * [0.5,0.3,0.2][i]),
            "has_entry": has_entry
        })

    results = sorted(results, key=lambda x: x["has_entry"], reverse=True)

    sig = build_signature(results)

    state = load_state()
    prev_sig = state["sig"]

    now = time.time()
    last_time = state["time"]

    has_ready = any(r["has_entry"] for r in results)
    prev_ready = state["ready"]

    ready_event = has_ready and not prev_ready
    sig_event = sig != prev_sig
    time_event = now - last_time > 1800  # 30 phút

    # ===== MESSAGE =====
    msg = "TOP 3 T+4 PICKS\n\n"

    for r in results:
        msg += (
            f"{r['symbol']}\n"
            f"Entry: {r['entry']}\n"
            f"SL: {r['sl']} | TP: {r['tp']}\n"
            f"Score: {r['score']}\n"
            f"Winrate: {round(r['winrate']*100,1)}%\n"
            f"Vốn: {r['capital']:,}\n"
        )
        msg += "👉 READY\n\n" if r["has_entry"] else "⏳ WAIT\n\n"

    # ===== SEND =====
    if ready_event or sig_event or time_event:

        if allow_send_time():
            send(msg)
            print("📨 SEND")
            last_time = now
        else:
            print("⏸ Before 09:30")

    else:
        print("⏸ Skip")

    save_state({
        "sig": sig,
        "ready": has_ready,
        "time": last_time
    })


if __name__ == "__main__":
    run()
