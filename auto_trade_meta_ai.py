import pandas as pd
import requests
from datetime import datetime
import time
import os

# ===== FIX PATH =====
os.chdir(os.path.dirname(os.path.abspath(__file__)))

LOG = "trades_log.csv"
FORECAST_FILE = "forecast.csv"

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

NAV = 100_000_000

LAST_STATE = None


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


# ===== SAVE =====
def save(symbol, entry, sl, tp):

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


# ===== MAIN =====
def run():

    global LAST_STATE

    print("\n🚀 RUNNING...")

    forecast_df = load_forecast()

    if forecast_df is None:

        if LAST_STATE != "NO_FORECAST":
            send("❌ Chưa có forecast → không trade")
            LAST_STATE = "NO_FORECAST"

        return

    results = []

    best_trade = None

    # ===== DUYỆT 3 MÃ =====
    for i, row in forecast_df.iterrows():

        symbol = row["symbol"]

        df = get_data(symbol)
        if df is None:
            continue

        has_entry = check_entry(df)

        # ===== PHÂN BỔ VỐN =====
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

        # chọn kèo có entry đầu tiên (tốt nhất)
        if has_entry and best_trade is None:
            best_trade = results[-1]

    # ===== SORT: kèo có entry lên đầu =====
    results = sorted(results, key=lambda x: x["has_entry"], reverse=True)

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

        if r["has_entry"]:
            msg += "👉 READY\n\n"
        else:
            msg += "⏳ WAIT\n\n"

    send(msg)

    # ===== CHỈ TRADE 1 MÃ =====
    if best_trade:

        save(
            best_trade["symbol"],
            best_trade["entry"],
            best_trade["sl"],
            best_trade["tp"]
        )

        LAST_STATE = "TRADE"

    else:
        LAST_STATE = "WAIT"


# ===== LOOP =====
while True:
    run()
    time.sleep(60)
