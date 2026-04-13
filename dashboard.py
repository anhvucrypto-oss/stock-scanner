import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.set_page_config(layout="wide")

st.title("📊 Trading Dashboard")

# ===== URL GITHUB =====
url = "https://raw.githubusercontent.com/anhvucrypto-oss/stock-scanner/main/trades_log.csv"

# ===== LOAD DATA =====
try:
    res = requests.get(url, timeout=10)

    if res.status_code != 200:
        st.error(f"Lỗi GitHub: {res.status_code}")
        st.stop()

    data = res.text.strip()

    if data == "":
        st.warning("File rỗng")
        st.stop()

    df = pd.read_csv(StringIO(data))

except Exception as e:
    st.error(f"Lỗi load data: {e}")
    st.stop()

# ===== HIỂN THỊ =====
st.subheader("📋 Trades Log")
st.dataframe(df.tail(30), use_container_width=True)

# ===== METRICS =====
if "result" in df.columns:

    df["result"] = pd.to_numeric(df["result"], errors="coerce").fillna(0)

    total = len(df)
    win = len(df[df["result"] > 0])
    pnl = df["result"].sum()

    winrate = round(win / total * 100, 2) if total > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Trades", total)
    col2.metric("Winrate", f"{winrate}%")
    col3.metric("PnL (R)", round(pnl,2))

# ===== REFRESH BUTTON =====
st.button("🔄 Refresh")

# ===== AUTO REFRESH =====
st.caption("Auto refresh mỗi 5 giây")

import time
time.sleep(5)
st.rerun()
