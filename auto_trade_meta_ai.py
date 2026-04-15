import pandas as pd
import requests
from datetime import datetime
import time
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

LOG = "trades_log.csv"
FORECAST_FILE = "forecast.csv"

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

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
        return []

    df = pd.read_csv(FORECAST_FILE)

    if df.empty or "symbol" not in df.columns:
        return []

    symbols = df["symbol"].dropna().tolist()

    print("🎯 Forecast symbols:", symbols)

    return symbols


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


# ===== SIMPLE ENTRY =====
def check_entry(df):

    if len(df) < 25:
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

    forecast_symbols = load_forecast()

    if not forecast_symbols:

        if LAST_STATE != "NO_FORECAST":
            send("❌ Chưa có forecast → không trade")
            LAST_STATE = "NO_FORECAST"

        return

    for symbol in forecast_symbols:

        df = get_data(symbol)

        if df is None:
            continue

        if check_entry(df):

            entry = df["close"].iloc[-1]
            sl = entry * 0.97
            tp = entry * 1.05

            msg = f"""
🔥 TRADE (FROM FORECAST)

{symbol}
Entry: {round(entry,1)}
SL: {round(sl,1)}
TP: {round(tp,1)}
"""

            send(msg)
            save(symbol, entry, sl, tp)

            LAST_STATE = "TRADE"
            return

    # ===== NO TRADE =====
    if LAST_STATE != "NO_TRADE":
        send("❌ Forecast có nhưng chưa đạt điểm vào")
        LAST_STATE = "NO_TRADE"


# ===== LOOP =====
while True:
    run()
    time.sleep(60)
