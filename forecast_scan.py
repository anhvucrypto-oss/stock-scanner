import pandas as pd
import requests
from datetime import datetime
import os

# ===== CONFIG =====
FILE = "forecast.csv"

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

# ===== LOAD SYMBOLS =====
def load_symbols():
    try:
        url = "https://raw.githubusercontent.com/anhvucrypto-oss/stock-scanner/main/symbols.csv"

        df = pd.read_csv(url)

        symbols = df["symbol"].dropna().tolist()

        print("🌐 Load symbols từ GitHub")
        print("📊 Symbols:", symbols)

        return symbols

    except Exception as e:
        print("❌ Lỗi load GitHub:", e)

        # fallback local
        try:
            df = pd.read_csv("symbols.csv")
            symbols = df["symbol"].dropna().tolist()
            print("📁 Fallback local symbols")
            return symbols
        except:
            return []

# ===== GET DATA =====
def get_data(symbol):
    try:
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol={symbol}&resolution=1D&from=1700000000&to=9999999999"
        data = requests.get(url, timeout=10).json()

        if "c" not in data:
            return None

        return pd.DataFrame({
            "close": data["c"],
            "high": data["h"],
            "low": data["l"]
        })

    except:
        return None

# ===== SIGNAL =====
def signal(df):
    if len(df) < 25:
        return False

    ma20 = df["close"].rolling(20).mean()
    return df["close"].iloc[-1] > ma20.iloc[-1]

# ===== MAIN SCAN =====
def scan():

    print("\n⏰ START FORECAST:", datetime.now())

    symbols = load_symbols()

    results = []

    for s in symbols:

        df = get_data(s)

        if df is None:
            print(f"❌ {s} lỗi data")
            continue

        if signal(df):

            entry = round(df["close"].iloc[-1], 1)
            target = round(entry * 1.06, 1)

            results.append({
                "time": datetime.now(),
                "symbol": s,
                "entry": entry,
                "target_T4": target
            })

            print(f"✅ {s} PASS")

        else:
            print(f"➖ {s} NO SIGNAL")

    # ===== SAVE FILE =====
    if results:
        df_out = pd.DataFrame(results)
    else:
        df_out = pd.DataFrame([{
            "time": datetime.now(),
            "symbol": "NO_SIGNAL",
            "entry": 0,
            "target_T4": 0
        }])

    df_out.to_csv(FILE, index=False)

    print("💾 Saved forecast.csv")

    # ===== TELEGRAM =====
    msg = f"📊 T+4 Forecast: {len(results)} mã"
    send(msg)

    print("📨 Telegram sent")
    print("✅ DONE:", datetime.now())


# ===== RUN =====
if __name__ == "__main__":
    scan()
