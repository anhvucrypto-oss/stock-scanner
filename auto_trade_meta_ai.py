import pandas as pd
import requests
from datetime import datetime
import os

# ===== PATH =====
os.chdir(os.path.dirname(os.path.abspath(__file__)))

FORECAST_FILE = "forecast.csv"
LOG = "trades_log.csv"
MSG_STATE_FILE = "bot_msg_state.txt"

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


# ===== MESSAGE STATE (ANTI-SPAM) =====
def load_msg_state():
    if not os.path.exists(MSG_STATE_FILE):
        return None
    with open(MSG_STATE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def save_msg_state(msg):
    with open(MSG_STATE_FILE, "w", encoding="utf-8") as f:
        f.write(msg)


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
        print("❌ Không có forecast")
        return

    results = []
    best_trade = None

    # ===== LOOP TOP 3 =====
    for i, row in forecast_df.iterrows():

        symbol = str(row["symbol"])

        df = get_data(symbol)
        if df is None:
            continue

        has_entry = check_entry(df)

        # ===== VỐN =====
        if i == 0:
            capital = int(NAV * 0.5)
        elif i == 1:
            capital = int(NAV * 0.3)
        else:
            capital = int(NAV * 0.2)

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

        # chọn kèo đầu tiên có entry
        if has_entry and best_trade is None:
            best_trade = results[-1]

    # ===== SORT READY LÊN TRÊN =====
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

        msg += "👉 READY\n\n" if r["has_entry"] else "⏳ WAIT\n\n"

    # ===== ANTI-SPAM TELEGRAM =====
    old_msg = load_msg_state()

    if msg != old_msg:
        send(msg)
        save_msg_state(msg)
        print("📨 Sent (changed)")
    else:
        print("⏸ Không đổi → không gửi")

    # ===== SAVE TRADE =====
    if best_trade:
        save_trade(
            best_trade["symbol"],
            best_trade["entry"],
            best_trade["sl"],
            best_trade["tp"]
        )


# ===== RUN RIÊNG =====
if __name__ == "__main__":
    run()
