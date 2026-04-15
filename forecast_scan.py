import pandas as pd
import requests
from datetime import datetime
import os

# ===== FIX PATH (QUAN TRỌNG) =====
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ===== CONFIG =====
FILE = "forecast.csv"

TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print("❌ Telegram lỗi:", e)

# ===== LOAD SYMBOLS =====
def load_symbols():
    try:
        if not os.path.exists("symbols.csv"):
            print("❌ Không tìm thấy symbols.csv")
            return []

        df = pd.read_csv("symbols.csv")

        if "symbol" not in df.columns:
            print("❌ symbols.csv thiếu cột 'symbol'")
            return []

        symbols = df["symbol"].dropna().astype(str).tolist()

        if len(symbols) == 0:
            print("❌ symbols.csv rỗng")
        else:
            print("📊 Loaded symbols:", symbols)
            print("📊 Tổng số mã:", len(symbols))

        return symbols

    except Exception as e:
        print("❌ Lỗi load symbols:", e)
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

    except Exception as e:
        print(f"❌ {symbol} lỗi API:", e)
        return None

# ===== SIGNAL =====
def signal(df):
    if len(df) < 25:
        return False

    ma20 = df["close"].rolling(20).mean()
    return df["close"].iloc[-1] > ma20.iloc[-1]

# ===== MAIN =====
def scan():

    print("\n⏰ START FORECAST:", datetime.now())

    symbols = load_symbols()

    if len(symbols) == 0:
        print("❌ KHÔNG CÓ SYMBOL → DỪNG")
        return

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
