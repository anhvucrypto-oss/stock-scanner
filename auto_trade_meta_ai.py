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

NAV = 100_000_000


# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass


# ===== LOAD FORECAST FULL =====
def load_forecast():

    if not os.path.exists(FORECAST_FILE):
        return None

    df = pd.read_csv(FORECAST_FILE)

    if df.empty:
        return None

    row = df.iloc[0]  # TOP 1

    print("🎯 Forecast:", row["symbol"])

    return row


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

    forecast = load_forecast()

    if forecast is None:

        if LAST_STATE != "NO_FORECAST":
            send("❌ Chưa có forecast → không trade")
            LAST_STATE = "NO_FORECAST"

        return

    symbol = forecast["symbol"]

    df = get_data(symbol)

    if df is None:
        return

    if check_entry(df):

        entry = forecast["entry"]
        sl = forecast["sl"]
        tp = forecast["tp"]

        score = forecast["score"]
        winrate = forecast["winrate"]

        capital = NAV

        msg = (
            "🔥 TRADE (FROM FORECAST)\n\n"
            f"{symbol}\n"
            f"Entry: {entry}\n"
            f"SL: {sl} | TP: {tp}\n"
            f"Score: {score}\n"
            f"Winrate: {round(winrate*100,1)}%\n"
            f"Vốn: {capital:,}\n"
        )

        send(msg)
        save(symbol, entry, sl, tp)

        LAST_STATE = "TRADE"

    else:

        if LAST_STATE != "WAIT_ENTRY":
            send("⏳ Đang chờ điểm vào đẹp (theo forecast)")
            LAST_STATE = "WAIT_ENTRY"


# ===== LOOP =====
while True:
    run()
    time.sleep(60)
