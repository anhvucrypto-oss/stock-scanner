import requests
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD
from datetime import datetime

# ===== CONFIG =====
TELEGRAM_TOKEN = "8216332974:AAHQS-fk-gq5aX3cPp0j8xcjXzl6BhA01zs"
CHAT_ID = "1329522024"

symbols = pd.read_csv(r"C:\stock_scanner\symbols.csv")["symbol"].dropna().tolist()

# ===== TELEGRAM =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ===== GET DATA =====
def get_data(symbol, res):
    try:
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol={symbol}&resolution={res}&from=1700000000&to=9999999999"
        data = requests.get(url, timeout=10).json()

        df = pd.DataFrame({
            "close": data["c"],
            "high": data["h"],
            "low": data["l"],
            "volume": data["v"]
        })

        if len(df) < 100:
            return None

        return df
    except:
        return None

# ===== INDICATORS =====
def add_indicators(df):
    df["tenkan"] = (df["high"].rolling(9).max() + df["low"].rolling(9).min()) / 2
    df["kijun"]  = (df["high"].rolling(17).max() + df["low"].rolling(17).min()) / 2
    df["senkouA"] = (df["tenkan"] + df["kijun"]) / 2
    df["senkouB"] = (df["high"].rolling(26).max() + df["low"].rolling(26).min()) / 2

    df["ma89"] = df["close"].rolling(89).mean()

    df["wma45"] = df["close"].rolling(45).apply(
        lambda x: np.dot(x, np.arange(1,46))/sum(np.arange(1,46))
    )

    df["rsi"] = RSIIndicator(df["close"], 14).rsi()

    macd = MACD(df["close"], 12, 26, 9)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    # Fisher
    n = 9
    hl2 = (df["high"] + df["low"]) / 2
    min_low = hl2.rolling(n).min()
    max_high = hl2.rolling(n).max()
    x = 2 * ((hl2 - min_low) / (max_high - min_low + 1e-9) - 0.5)
    x = x.clip(-0.999, 0.999)

    fisher = [0]*len(df)
    for i in range(1, len(df)):
        fisher[i] = 0.5 * np.log((1 + x.iloc[i])/(1 - x.iloc[i])) + 0.5 * fisher[i-1]

    df["fisher"] = fisher

    return df

# ===== LOGIC =====
def trend_ok(df):
    last = df.iloc[-1]
    cloud_top = max(last["senkouA"], last["senkouB"])

    return (
        last["close"] > last["tenkan"] and
        last["tenkan"] > last["kijun"] and
        last["kijun"] > cloud_top and
        last["close"] > last["ma89"]
    )

def momentum_ok(df):
    last = df.iloc[-1]
    return (
        last["rsi"] > 50 and
        last["macd"] > last["macd_signal"] and
        last["close"] > last["wma45"]
    )

def entry_ok(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    pullback = (
        prev["low"] <= prev["tenkan"] * 1.01 or
        prev["low"] <= prev["kijun"] * 1.01
    )

    bounce = last["close"] > prev["close"]
    fisher_up = last["fisher"] > prev["fisher"]

    return pullback and bounce and fisher_up

# ===== MAIN =====
def run():
    results = []

    for s in symbols:
        df_d  = get_data(s, "1D")
        df_4h = get_data(s, "240")
        df_1h = get_data(s, "60")
        df_15 = get_data(s, "15")

        if None in (df_d, df_4h, df_1h, df_15):
            continue

        df_d  = add_indicators(df_d)
        df_4h = add_indicators(df_4h)
        df_1h = add_indicators(df_1h)
        df_15 = add_indicators(df_15)

        if not trend_ok(df_d): continue
        if not trend_ok(df_4h): continue
        if not momentum_ok(df_1h): continue
        if not entry_ok(df_15): continue

        momentum = (df_d["close"].iloc[-1] - df_d["close"].iloc[-4]) / df_d["close"].iloc[-4]

        if momentum < 0.03:
            continue

        last = df_15.iloc[-1]

        entry = round(last["close"],1)
        sl = round(df_1h["kijun"].iloc[-1]*0.97,1)
        tp = round(entry + 2*(entry-sl),1)

        score = momentum

        results.append((s, score, entry, sl, tp))

    if not results:
        send_telegram("❌ Không có kèo")
        return

    best = sorted(results, key=lambda x: x[1], reverse=True)[0]

    symbol, score, entry, sl, tp = best

    # ===== POSITION SIZE =====
    capital = 100000000  # 100tr
    risk_per_trade = 0.01

    risk_amount = capital * risk_per_trade
    position_size = risk_amount / (entry - sl)

    msg = f"""
🔥 KÈO MẠNH NHẤT

Mã: {symbol}
Entry: {entry}
SL: {sl}
TP: {tp}

Khối lượng: {int(position_size)}

Score: {round(score,2)}
Time: {datetime.now().strftime('%H:%M')}
"""

    send_telegram(msg)

# ===== RUN =====
if __name__ == "__main__":
    run()