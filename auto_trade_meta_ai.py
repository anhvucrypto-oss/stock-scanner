import pandas as pd
import requests
from datetime import datetime
import os

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


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"ready": False}
    try:
        return pd.read_json(STATE_FILE).to_dict()
    except:
        return {"ready": False}


def save_state(state):
    pd.DataFrame([state]).to_json(STATE_FILE)


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

        return pd.DataFrame({
            "close": data["c"]
        })
    except:
        return None


def check_entry(df):
    if len(df) < 20:
        return False

    ma20 = df["close"].rolling(20).mean()
    return bool(df["close"].iloc[-1] > ma20.iloc[-1])


def run():

    print("\n🚀 BOT RUNNING...")

    forecast_df = load_forecast()
    if forecast_df is None:
        return

    results = []
    has_any_ready = False

    for i, row in forecast_df.iterrows():

        symbol = str(row["symbol"])

        df = get_data(symbol)
        if df is None:
            continue

        has_entry = check_entry(df)

        if has_entry:
            has_any_ready = True

        capital = int(NAV * [0.5, 0.3, 0.2][i])

        results.append({
            "symbol": symbol,
            "entry": float(row["entry"]),
            "sl": float(row["sl"]),
            "tp": float(row["tp"]),
            "score": float(row["score"]),
            "winrate": float(row["winrate"]),
            "capital": capital,
            "has_entry": has_entry
        })

    results = sorted(results, key=lambda x: x["has_entry"], reverse=True)

    # ===== STATE =====
    state = load_state()
    prev_ready = state.get("ready", False)

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

    # ===== ONLY SEND WHEN READY MỚI =====
    if has_any_ready and not prev_ready:
        send(msg)
        print("📨 READY SIGNAL")

    else:
        print("⏸ No new signal")

    # ===== SAVE STATE =====
    save_state({"ready": has_any_ready})


if __name__ == "__main__":
    run()
