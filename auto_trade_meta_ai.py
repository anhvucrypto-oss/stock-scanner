import pandas as pd
import requests
from datetime import datetime
import os
import time

# ===== PATH =====
os.chdir(os.path.dirname(os.path.abspath(__file__)))

FORECAST_FILE = "forecast.csv"
LOG = "trades_log.csv"

STATE_FILE = "bot_state.json"

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

NAV = 100_000_000

COOLDOWN = 600  # 10 phút


# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        print("❌ Telegram lỗi")


# ===== STATE =====
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_msg": "", "last_time": 0}
    try:
        return pd.read_json(STATE_FILE).to_dict()
    except:
        return {"last_msg": "", "last_time": 0}


def save_state(state):
    pd.DataFrame([state]).to_json(STATE_FILE)


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
        data = requests.get(url, timeout=10).json()

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
    return bool(df["close"].iloc[-1] > ma20.iloc[-1])


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


# ===== MAIN =====
def run():

    print("\n🚀 BOT RUNNING...")

    forecast_df = load_forecast()
    if forecast_df is None:
        return

    results = []
    best_trade = None

    for i, row in forecast_df.iterrows():

        symbol = str(row["symbol"])

        df = get_data(symbol)
        if df is None:
            continue

        has_entry = check_entry(df)

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

        if has_entry and best_trade is None:
            best_trade = results[-1]

    # SORT READY lên trên
    results = sorted(results, key=lambda x: x["has_entry"], reverse=True)

    # ===== BUILD MESSAGE =====
    msg = "TOP 3 T+4 PICKS\n\n"
    has_any_ready = False

    for r in results:

        if r["has_entry"]:
            has_any_ready = True

        msg += (
            f"{r['symbol']}\n"
            f"Entry: {r['entry']}\n"
            f"SL: {r['sl']} | TP: {r['tp']}\n"
            f"Score: {r['score']}\n"
            f"Winrate: {round(r['winrate']*100,1)}%\n"
            f"Vốn: {r['capital']:,}\n"
        )

        msg += "👉 READY\n\n" if r["has_entry"] else "⏳ WAIT\n\n"

    # ===== LOAD STATE =====
    state = load_state()
    now = time.time()

    # ===== RULE 1: READY mới xuất hiện =====
    prev_ready = "👉 READY" in state.get("last_msg", "")
    new_ready = has_any_ready

    ready_event = (new_ready and not prev_ready)

    # ===== RULE 2: COOLDOWN =====
    cooldown_ok = now - state.get("last_time", 0) > COOLDOWN

    # ===== DECISION =====
    if ready_event or cooldown_ok:

        send(msg)

        save_state({
            "last_msg": msg,
            "last_time": now
        })

        print("📨 Sent")

    else:
        print("⏸ Skip (cooldown / no new signal)")

    # ===== SAVE TRADE =====
    if best_trade:
        save_trade(
            best_trade["symbol"],
            best_trade["entry"],
            best_trade["sl"],
            best_trade["tp"]
        )


# ===== RUN =====
if __name__ == "__main__":
    run()
