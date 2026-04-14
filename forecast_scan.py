import pandas as pd
import requests
from datetime import datetime
import os

FILE = "forecast.csv"

symbols = ["FPT","VNM","ACB","DGC","REE"]

def get_data(symbol):
    try:
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol={symbol}&resolution=1D&from=1700000000&to=9999999999"
        data = requests.get(url).json()
        return pd.DataFrame({
            "close": data["c"],
            "high": data["h"],
            "low": data["l"]
        })
    except:
        return None

def signal(df):
    ma20 = df["close"].rolling(20).mean()
    if df["close"].iloc[-1] > ma20.iloc[-1]:
        return True
    return False

def scan():

    results = []

    for s in symbols:

        df = get_data(s)
        if df is None:
            continue

        if signal(df):

            entry = df["close"].iloc[-1]
            target = round(entry * 1.06,1)

            results.append({
                "time": datetime.now(),
                "symbol": s,
                "entry": entry,
                "target_T4": target
            })

    df_out = pd.DataFrame(results)

    if df_out.empty:
        df_out = pd.DataFrame([{
            "time": datetime.now(),
            "symbol": "NO_SIGNAL",
            "entry": 0,
            "target_T4": 0
        }])

    df_out.to_csv(FILE, index=False)

    print("✅ Forecast updated")

if __name__ == "__main__":
    scan()
def send(msg):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id": CHAT_ID, "text": msg})

# sau khi scan xong
if not df_out.empty:
    msg = "📊 T+4 Forecast:\n" + str(df_out.head())
    send(msg)