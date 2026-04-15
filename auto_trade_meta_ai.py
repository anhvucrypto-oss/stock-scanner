import pandas as pd
import requests
from datetime import datetime
import time
import os
import json

# ===== FIX PATH =====
os.chdir(os.path.dirname(os.path.abspath(__file__)))

LOG = "trades_log.csv"
FORECAST_FILE = "forecast.csv"
STATE_FILE = "bot_state.json"

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


# ===== LOAD FORECAST =====
def load_forecast():
    if not os.path.exists(FORECAST_FILE):
        return None

    df = pd.read_csv(FORECAST_FILE)

    if df.empty:
        return None

    return df.head(3)


# ===== LOAD STATE =====
def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return None


# ===== SAVE STATE =====
def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ===== GET DATA =====
def get_data(symbol):
    try:
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol={symbol}&resolution=1D&from=1700000000&to=9999999999"
        data = requests.get(url).json()

        return pd.DataFrame({
            "close": data["c"]
        })
    except:
        return None


# ===== ENTRY =====
def check_entry(df):
    if len(df) < 20:
        return False

    ma20 = df["close"].rolling(20).mean()

    return df["close"].iloc[-1] > ma20.iloc[-1]


# ===== SAVE TRADE =====
def save_trade(symbol, entry, sl, tp):

    new = pd.DataFrame([{
        "time": datetime.now(),
        "symbol": symbol,
        "entry": entry,
        "sl": sl,
        "tp": tp
    }])

    if os.path.exists(LOG):
        df = pd.read_csv(LOG)
        df = pd.concat([df, new], ignore_index=True)
    else:
        df = new

    df.to_csv(LOG, index=False)


# ===== BUILD STATE =====
def build_state(results):
    return [
        {
            "symbol": r["symbol"],
            "has_entry": r["has_entry"]
        }
        for r in results
    ]


# ===== MAIN =====
def run():

    print("\n🚀 RUNNING...")

    forecast_df = load_forecast()
    if forecast_df is None:
        return

    results = []

    best_trade = None

    for i, row in forecast_df.iterrows():

        symbol = row["symbol"]

        df = get_data(symbol)
        if df is None:
            continue

        has_entry = check_entry(df)

        if i == 0:
            capital = int(NAV * 0.5)
        elif i == 1:
            capital = int(NAV * 0.3)
        else:
            capital = int(NAV * 0.2)

        results.append({
            "symbol": symbol,
            "entry": row["entry"],
            "sl": row["sl"],
            "tp": row["tp"],
            "score": row["score"],
            "winrate": row["winrate"],
            "capital": capital,
            "has_entry": has_entry
        })

        if has_entry and best_trade is None:
            best_trade = results[-1]

    # ===== SORT =====
    results = sorted(results, key=lambda x: x["has_entry"], reverse=True)

    # ===== CHECK STATE CHANGE =====
    new_state = build_state(results)
    old_state = load_state()

    if new_state == old_state:
        print("⏸ Không có thay đổi → không gửi")
        return

    # ===== SAVE STATE =====
    save_state(new_state)

    # ===== BUILD MESSAGE =====
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

    send(msg)

    # ===== TRADE =====
    if best_trade:
        save_trade(
            best_trade["symbol"],
            best_trade["entry"],
            best_trade["sl"],
            best_trade["tp"]
        )


# ===== LOOP =====
while True:
    run()
    time.sleep(60)
