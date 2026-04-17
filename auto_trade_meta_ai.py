import pandas as pd
import requests
from datetime import datetime
import os

# ===== PATH =====
os.chdir(os.path.dirname(os.path.abspath(__file__)))

FORECAST_FILE = "forecast.csv"
STATE_FILE = "bot_state.json"

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

NAV = 100_000_000


# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        print("❌ Telegram lỗi")


# ===== TIME FILTER =====
def allow_send_time():
    now = datetime.now()
    return (now.hour > 9) or (now.hour == 9 and now.minute >= 30)


# ===== STATE =====
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"sig": "", "ready": False}
    try:
        return pd.read_json(STATE_FILE).to_dict()
    except:
        return {"sig": "", "ready": False}


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


# ===== MAIN =====
def run():

    print("\n🚀 BOT RUNNING...")

    forecast_df = load_forecast()
    if forecast_df is None:
        print("❌ Không có forecast")
        return

    results = []
    has_any_ready = False

    # ===== LOOP =====
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

    # ===== SORT READY =====
    results = sorted(results, key=lambda x: x["has_entry"], reverse=True)

    # ===== SIGNATURE (QUAN TRỌNG NHẤT) =====
    sig = str([
        (r["symbol"], round(r["entry"],2), round(r["sl"],2), round(r["tp"],2))
        for r in results
    ])

    # ===== LOAD STATE =====
    state = load_state()
    prev_sig = state.get("sig", "")

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

    # ===== LOGIC GỬI =====
    if sig != prev_sig:

        if allow_send_time():
            send(msg)
            print("📨 NEW SIGNAL")
        else:
            print("⏸ Trước 09:30 → không gửi")

    else:
        print("⏸ Không đổi → không gửi")

    # ===== SAVE STATE =====
    save_state({
        "sig": sig,
        "ready": has_any_ready
    })


# ===== RUN =====
if __name__ == "__main__":
    run()
